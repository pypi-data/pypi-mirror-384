import logging
import re
from asyncio import sleep
from collections import defaultdict
from difflib import SequenceMatcher

from xync_schema import models
from xync_schema.xtype import BaseAd


class AdLoader:
    ex: models.Ex
    all_conds: dict[int, tuple[str, set[int]]] = {}
    cond_sims: dict[int, int] = defaultdict(set)
    rcond_sims: dict[int, set[int]] = defaultdict(set)  # backward
    tree: dict = {}

    async def old_conds_load(self):
        # пока не порешали рейс-кондишн, очищаем сиротские условия при каждом запуске
        # [await c.delete() for c in await Cond.filter(ads__isnull=True)]
        self.all_conds = {
            c.id: (c.raw_txt, {a.maker.exid for a in c.ads})
            for c in await models.Cond.all().prefetch_related("ads__maker")
        }
        for curr, old in await models.CondSim.filter().values_list("cond_id", "cond_rel_id"):
            self.cond_sims[curr] = old
            self.rcond_sims[old] |= {curr}

        self.build_tree()
        a = set()

        def check_tree(tre):
            for p, c in tre.items():
                a.add(p)
                check_tree(c)

        for pr, ch in self.tree.items():
            check_tree(ch)
        if ct := set(self.tree.keys()) & a:
            logging.exception(f"cycle cids: {ct}")

    async def person_name_update(self, name: str, exid: int) -> models.Person:
        if actor := await models.Actor.get_or_none(exid=exid, ex=self.ex).prefetch_related("person"):
            actor.person.name = name
            await actor.person.save()
            return actor.person
        # return await models.Person.create(note=f'{actor.ex_id}:{actor.exid}:{name}') # no person for just ads with no orders
        raise ValueError(f"Agent #{exid} not found")

    async def ad_load(
        self,
        pad: BaseAd,
        cid: int = None,
        ps: models.PairSide = None,
        maker: models.Actor = None,
        coinex: models.CoinEx = None,
        curex: models.CurEx = None,
        rname: str = None,
        pms_from_cond: bool = False,
    ) -> models.Ad:
        if not maker:
            if not (maker := await models.Actor.get_or_none(exid=pad.userId, ex=self.ex)):
                person = await models.Person.create(name=rname, note=f"{self.ex.id}:{pad.userId}:{pad.nickName}")
                maker = await models.Actor.create(name=pad.nickName, person=person, exid=pad.userId, ex=self.ex)
        if rname:
            await self.person_name_update(rname, int(pad.userId))
        ps = ps or await models.PairSide.get_or_none(
            is_sell=pad.side,
            pair__coin__ticker=pad.tokenId,
            pair__cur__ticker=pad.currencyId,
        ).prefetch_related("pair")
        # if not ps or not ps.pair:
        #     ...  # THB/USDC: just for initial filling
        ad_upd = models.Ad.validate(pad.model_dump(by_alias=True))
        cur_scale = 10 ** (curex or await models.CurEx.get(coin_id=ps.pair.cur_id, ex=self.ex)).scale
        coin_scale = 10 ** (coinex or await models.CoinEx.get(coin_id=ps.pair.coin_id, ex=self.ex)).scale
        df_unq = ad_upd.df_unq(
            maker_id=maker.id,
            pair_side_id=ps.id,
            amount=int(float(pad.quantity) * float(pad.price) * cur_scale),
            quantity=int(float(pad.quantity) * coin_scale),
            min_fiat=int(float(pad.minAmount) * cur_scale),
            max_fiat=pad.maxAmount and int(float(pad.maxAmount) * cur_scale),
            price=int(float(pad.price) * cur_scale),
            premium=int(float(pad.premium) * 100),
            cond_id=cid,
        )
        ad_db, _ = await models.Ad.update_or_create(**df_unq)
        if not pms_from_cond:
            await ad_db.pms.add(*(await models.Pm.filter(pmexs__ex=self.ex, pmexs__exid__in=pad.payments)))
        return ad_db

    async def cond_load(  # todo: refact from Bybit Ad format to universal
        self,
        ad: BaseAd,
        ps: models.PairSide = None,
        force: bool = False,
        rname: str = None,
        coinex: models.CoinEx = None,
        curex: models.CurEx = None,
        pms_from_cond: bool = False,
    ) -> tuple[models.Ad, bool]:
        _sim, cid = None, None
        ad_db = await models.Ad.get_or_none(exid=ad.id, maker__ex=self.ex).prefetch_related("cond")
        # если точно такое условие уже есть в бд
        if not (cleaned := clean(ad.remark)) or (cid := {oc[0]: ci for ci, oc in self.all_conds.items()}.get(cleaned)):
            # и объява с таким ид уже есть, но у нее другое условие
            if ad_db and ad_db.cond_id != cid:
                # то обновляем ид ее условия
                ad_db.cond_id = cid
                await ad_db.save()
                logging.info(f"{ad.nickName} upd cond#{ad_db.cond_id}->{cid}")
                # old_cid = ad_db.cond_id # todo: solve race-condition, а пока что очищаем при каждом запуске
                # if not len((old_cond := await Cond.get(id=old_cid).prefetch_related('ads')).ads):
                #     await old_cond.delete()
                #     logging.warning(f"Cond#{old_cid} deleted!")
            return (
                ad_db
                or force
                and await self.ad_load(
                    ad, cid, ps, coinex=coinex, curex=curex, rname=rname, pms_from_cond=pms_from_cond
                )
            ), False
        # если эта объява в таким ид уже есть в бд, но с другим условием (или без), а текущего условия еще нет в бд
        if ad_db:
            await ad_db.fetch_related("cond__ads", "maker")
            if not ad_db.cond_id or (
                # у измененного условия этой объявы есть другие объявы?
                (rest_ads := set(ad_db.cond.ads) - {ad_db})
                and
                # другие объявы этого условия принадлежат другим юзерам
                {ra.maker_id for ra in rest_ads} - {ad_db.maker_id}
            ):
                # создадим новое условие и присвоим его только текущей объяве
                cid = await self.cond_new(cleaned, {int(ad.userId)})
                ad_db.cond_id = cid
                await ad_db.save()

                return ad_db, True
            # а если других объяв со старым условием этой обявы нет, либо они все этого же юзера
            # обновляем условие (в тч во всех ЕГО объявах)
            ad_db.cond.last_ver = ad_db.cond.raw_txt
            ad_db.cond.raw_txt = cleaned
            await ad_db.cond.save()
            await self.cond_upd(ad_db.cond, {ad_db.maker.exid})
            # и подправим коэфициенты похожести нового текста
            await self.fix_rel_sims(ad_db.cond_id, cleaned)
            return ad_db, False

        cid = await self.cond_new(cleaned, {int(ad.userId)})
        return await self.ad_load(
            ad, cid, ps, coinex=coinex, curex=curex, rname=rname, pms_from_cond=pms_from_cond
        ), True

    async def cond_new(self, txt: str, uids: set[int]) -> int:
        new_cond, _ = await models.Cond.update_or_create(raw_txt=txt)
        # и максимально похожую связь для нового условия (если есть >= 60%)
        await self.cond_upd(new_cond, uids)
        return new_cond.id

    async def cond_upd(self, cond: models.Cond, uids: set[int]):
        self.all_conds[cond.id] = cond.raw_txt, uids
        # и максимально похожую связь для нового условия (если есть >= 60%)
        old_cid, sim = await self.cond_get_max_sim(cond.id, cond.raw_txt, uids)
        await self.actual_sim(cond.id, old_cid, sim)

    def find_in_tree(self, cid: int, old_cid: int) -> bool:
        if p := self.cond_sims.get(old_cid):
            if p == cid:
                return True
            return self.find_in_tree(cid, p)
        return False

    async def cond_get_max_sim(self, cid: int, txt: str, uids: set[int]) -> tuple[int | None, int | None]:
        # находим все старые тексты похожие на 90% и более
        if len(txt) < 15:
            return None, None
        sims: dict[int, int] = {}
        for old_cid, (old_txt, old_uids) in self.all_conds.items():
            if len(old_txt) < 15 or uids == old_uids:
                continue
            elif not self.can_add_sim(cid, old_cid):
                continue
            if sim := get_sim(txt, old_txt):
                sims[old_cid] = sim
        # если есть, берем самый похожий из них
        if sims:
            old_cid, sim = max(sims.items(), key=lambda x: x[1])
            await sleep(0.3)
            return old_cid, sim
        return None, None

    def can_add_sim(self, cid: int, old_cid: int) -> bool:
        if cid == old_cid:
            return False
        elif self.cond_sims.get(cid) == old_cid:
            return False
        elif self.find_in_tree(cid, old_cid):
            return False
        elif self.cond_sims.get(old_cid) == cid:
            return False
        elif cid in self.rcond_sims.get(old_cid, {}):
            return False
        elif old_cid in self.rcond_sims.get(cid, {}):
            return False
        return True

    async def fix_rel_sims(self, cid: int, new_txt: str):
        for rel_sim in await models.CondSim.filter(cond_rel_id=cid).prefetch_related("cond"):
            if sim := get_sim(new_txt, rel_sim.cond.raw_txt):
                rel_sim.similarity = sim
                await rel_sim.save()
            else:
                await rel_sim.delete()

    async def actual_cond(self):
        for curr, old in await models.CondSim.all().values_list("cond_id", "cond_rel_id"):
            self.cond_sims[curr] = old
            self.rcond_sims[old] |= {curr}
        for cid, (txt, uids) in self.all_conds.items():
            old_cid, sim = await self.cond_get_max_sim(cid, txt, uids)
            await self.actual_sim(cid, old_cid, sim)
            # хз бля чо это ваще
            # for ad_db in await models.Ad.filter(direction__pairex__ex=self.ex).prefetch_related("cond", "maker"):
            #     ad = Ad(id=str(ad_db.exid), userId=str(ad_db.maker.exid), remark=ad_db.cond.raw_txt)
            #     await self.cond_upsert(ad, force=True)

    async def actual_sim(self, cid: int, old_cid: int, sim: int):
        if not sim:
            return
        if old_sim := await models.CondSim.get_or_none(cond_id=cid):
            if old_sim.cond_rel_id != old_cid:
                if sim > old_sim.similarity:
                    logging.warning(f"R {cid}: {old_sim.similarity}->{sim} ({old_sim.cond_rel_id}->{old_cid})")
                    await old_sim.update_from_dict({"similarity": sim, "old_rel_id": old_cid}).save()
                    self._cond_sim_upd(cid, old_cid)
            elif sim != old_sim.similarity:
                logging.info(f"{cid}: {old_sim.similarity}->{sim}")
                await old_sim.update_from_dict({"similarity": sim}).save()
        else:
            await models.CondSim.create(cond_id=cid, cond_rel_id=old_cid, similarity=sim)
            self._cond_sim_upd(cid, old_cid)

    def _cond_sim_upd(self, cid: int, old_cid: int):
        if old_old_cid := self.cond_sims.get(cid):  # если старый cid уже был в дереве:
            self.rcond_sims[old_old_cid].remove(cid)  # удаляем из обратного
        self.cond_sims[cid] = old_cid  # а в прямом он автоматом переопределится, даже если и был
        self.rcond_sims[old_cid] |= {cid}  # ну и в обратное добавим новый

    def build_tree(self):
        set(self.cond_sims.keys()) | set(self.cond_sims.values())
        tree = defaultdict(dict)
        # Группируем родителей по детям
        for child, par in self.cond_sims.items():
            tree[par] |= {child: {}}  # todo: make from self.rcond_sim

        # Строим дерево снизу вверх
        def subtree(node):
            if not node:
                return node
            for key in node:
                subnode = tree.pop(key, {})
                d = subtree(subnode)
                node[key] |= d  # actual tree rebuilding here!
            return node  # todo: refact?

        # Находим корни / без родителей
        roots = set(self.cond_sims.values()) - set(self.cond_sims.keys())
        for root in roots:
            _ = subtree(tree[root])

        self.tree = tree


def get_sim(s1, s2) -> int:
    sim = int((SequenceMatcher(None, s1, s2).ratio() - 0.6) * 10_000)
    return sim if sim > 0 else 0


def clean(s) -> str:
    clear = r"[^\w\s.,!?;:()\-]"
    repeat = r"(.)\1{2,}"
    s = re.sub(clear, "", s).lower()
    s = re.sub(repeat, r"\1", s)
    return s.replace("\n\n", "\n").replace("  ", " ").strip(" \n/.,!?-")
