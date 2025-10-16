import json
import logging
import re
import traceback
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import websockets
from asyncio import run, sleep
from decimal import Decimal

from playwright.async_api import async_playwright
from pydantic import ValidationError
from pyro_client.client.file import FileClient
from tortoise.exceptions import IntegrityError
from tortoise.timezone import now
from tortoise.transactions import in_transaction
from xync_bot import XyncBot

from xync_client.Abc.PmAgent import PmAgentClient
from xync_schema import models
from xync_schema.enums import UserStatus, OrderStatus

from xync_client.Bybit.etype.order import (
    StatusChange,
    CountDown,
    SellerCancelChange,
    Read,
    Receive,
    OrderFull,
    StatusApi,
)
from xync_client.loader import NET_TOKEN, PAY_TOKEN
from xync_client.Abc.InAgent import BaseInAgentClient
from xync_client.Bybit.agent import AgentClient


class InAgentClient(BaseInAgentClient):
    agent_client: AgentClient

    async def start_listen(self):
        t = await self.agent_client.ott()
        ts = int(float(t["time_now"]) * 1000)
        await self.ws_prv(self.agent_client.agent.auth["deviceId"], t["result"], ts)

    # 3N: [T] - Уведомление об одобрении запроса на сделку
    async def request_accepted_notify(self) -> int: ...  # id

    async def ws_prv(self, did: str, tok: str, ts: int):
        u = f"wss://ws2.bybit.com/private?appid=bybit&os=web&deviceid={did}&timestamp={ts}"
        async with websockets.connect(u) as websocket:
            auth_msg = json.dumps({"req_id": did, "op": "login", "args": [tok]})
            await websocket.send(auth_msg)

            sub_msg = json.dumps({"op": "subscribe", "args": ["FIAT_OTC_TOPIC", "FIAT_OTC_ONLINE_TOPIC"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"SUPER_DEAL"}']})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"OTC_ORDER_STATUS"}']})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"WEB_THREE_SELL"}']})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"APPEALED_CHANGE"}']})
            await websocket.send(sub_msg)

            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.cashier.order"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.cashier.order-eftd-complete-privilege-event"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.cashier.order-savings-product-event"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.deal-core.order-savings-complete-event"]})
            await websocket.send(sub_msg)

            sub_msg = json.dumps({"op": "subscribe", "args": ["FIAT_OTC_TOPIC", "FIAT_OTC_ONLINE_TOPIC"]})
            await websocket.send(sub_msg)
            while resp := await websocket.recv():
                if data := json.loads(resp):
                    upd, order_db = None, None
                    logging.info(f" {now().strftime('%H:%M:%S')} upd: {data.get('topic')}:{data.get('type')}")
                    match data.get("topic"):
                        case "OTC_ORDER_STATUS":
                            match data["type"]:
                                case "STATUS_CHANGE":
                                    try:
                                        upd = StatusChange.model_validate(data["data"])
                                    except ValidationError as e:
                                        logging.error(e)
                                        logging.error(data["data"])
                                    order = self.agent_client.api.get_order_details(orderId=upd.id)
                                    order = OrderFull.model_validate(order["result"])
                                    order_db = await models.Order.get_or_none(
                                        exid=order.id, ad__exid=order.itemId
                                    ) or await self.agent_client.create_order(order)
                                    match upd.status:
                                        case StatusApi.created:
                                            logging.info(f"Order {order.id} created at {order.createDate}")
                                            # сразу уменьшаем доступный остаток монеты/валюты
                                            await self.money_upd(order_db)
                                            if upd.side:  # я покупатель - ждем мою оплату
                                                _dest = order.paymentTermList[0].accountNo
                                                if not re.match(r"^([PpРр])\d{7,10}\b", _dest):
                                                    continue
                                                await order_db.fetch_related("ad__pair_side__pair", "cred__pmcur__cur")
                                                await self.send_payment(order_db)
                                        case StatusApi.wait_for_buyer:
                                            if upd.side == 0:  # ждем когда покупатель оплатит
                                                if not (pmacdx := await self.get_pma_by_cdex(order)):
                                                    continue
                                                pma, cdx = pmacdx
                                                am, tid = await pma.check_in(
                                                    Decimal(order.amount),
                                                    cdx.cred.pmcur.cur.ticker,
                                                    # todo: почему в московском час.поясе?
                                                    datetime.fromtimestamp(float(order.transferDate) / 1000),
                                                )
                                                if not tid:
                                                    logging.info(
                                                        f"Order {order.id} created at {order.createDate}, not paid yet"
                                                    )
                                                    continue
                                                try:
                                                    t, is_new = await models.Transfer.update_or_create(
                                                        dict(
                                                            amount=int(float(order.amount) * 100),
                                                            order=order_db,
                                                        ),
                                                        pmid=tid,
                                                    )
                                                except IntegrityError as e:
                                                    logging.error(tid)
                                                    logging.error(order)
                                                    logging.exception(e)

                                                if not is_new:  # если по этому платежу уже отпущен другая продажа
                                                    continue

                                                # если висят незавершенные продажи с такой же суммой
                                                pos = (await self.agent_client.get_orders_active(1))["result"]
                                                pos = [
                                                    o
                                                    for o in pos.get("items", [])
                                                    if (
                                                        o["amount"] == order.amount
                                                        and o["id"] != upd.id
                                                        and int(order.createDate)
                                                        < int(o["createDate"]) + 15 * 60 * 1000
                                                        # get full_order from o, and cred or pm from full_order:
                                                        and self.agent_client.api.get_order_details(orderId=o["id"])[
                                                            "result"
                                                        ]["paymentTermList"][0]["accountNo"]
                                                        == order.paymentTermList[0].accountNo
                                                    )
                                                ]
                                                curex = await models.CurEx.get(
                                                    cur__ticker=order.currencyId, ex=self.agent_client.ex_client.ex
                                                )
                                                pos_db = await models.Order.filter(
                                                    exid__not=order.id,
                                                    cred_id=order_db.cred_id,
                                                    amount=int(float(order.amount) * 10**curex.scale),
                                                    status__not_in=[OrderStatus.completed, OrderStatus.canceled],
                                                    created_at__gt=now() - timedelta(minutes=15),
                                                )
                                                if pos or pos_db:
                                                    await self.agent_client.ex_client.bot.send(
                                                        f"[Duplicate amount!]"
                                                        f"(https://www.bybit.com/ru-RU/p2p/orderList/{order.id})",
                                                        self.agent_client.actor.person.user.username_id,
                                                    )
                                                    logging.warning("Duplicate amount!")
                                                    continue

                                                # !!! ОТПРАВЛЯЕМ ДЕНЬГИ !!!
                                                self.agent_client.api.release_assets(orderId=upd.id)
                                                logging.info(
                                                    f"Order {order.id} created, paid before #{tid}:{am} at {order.createDate}, and RELEASED at {now()}"
                                                )
                                            elif upd.side == 1:  # я покупатель - ждем мою оплату
                                                continue  # logging.warning(f"Order {order.id} PAID at {now()}: {int_am}")
                                            else:
                                                ...
                                            # todo: check is always canceling
                                            # await order_db.update_from_dict({"status": OrderStatus.canceled}).save()
                                            # logging.info(f"Order {order.id} canceled at {datetime.now()}")

                                        case StatusApi.wait_for_seller:
                                            if order_db.status == OrderStatus.paid:
                                                continue
                                            await order_db.update_from_dict(
                                                {
                                                    "status": OrderStatus.paid,
                                                    "payed_at": datetime.fromtimestamp(
                                                        float(order.transferDate) / 1000
                                                    ),
                                                }
                                            ).save()
                                            logging.info(f"Order {order.id} payed at {order_db.payed_at}")

                                        case StatusApi.appealed:
                                            # todo: appealed by WHO? щас наугад стоит by_seller
                                            await order_db.update_from_dict(
                                                {
                                                    "status": OrderStatus.appealed_by_seller,
                                                    "appealed_at": datetime.fromtimestamp(
                                                        float(order.updateDate) / 1000
                                                    ),
                                                }
                                            ).save()
                                            logging.info(f"Order {order.id} appealed at {order_db.appealed_at}")

                                        case StatusApi.canceled:
                                            await order_db.update_from_dict({"status": OrderStatus.canceled}).save()
                                            logging.info(f"Order {order.id} canceled at {datetime.now()}")
                                            await self.money_upd(order_db)

                                        case StatusApi.completed:
                                            await order_db.update_from_dict(
                                                {
                                                    "status": OrderStatus.completed,
                                                    "confirmed_at": datetime.fromtimestamp(
                                                        float(order.updateDate) / 1000
                                                    ),
                                                }
                                            ).save()
                                            await self.money_upd(order_db)

                                        case _:
                                            logging.warning(f"Order {order.id} UNKNOWN STATUS {datetime.now()}")
                                case "COUNT_DOWN":
                                    upd = CountDown.model_validate(data["data"])
                                case _:
                                    self.listen(data)
                        case "OTC_USER_CHAT_MSG":
                            match data["type"]:
                                case "RECEIVE":
                                    upd = Receive.model_validate(data["data"])
                                    if order_db := await models.Order.get_or_none(
                                        exid=upd.orderId, ad__maker__ex=self.agent_client.actor.ex
                                    ).prefetch_related("ad__pair_side__pair", "cred__pmcur__cur"):
                                        im_taker = order_db.taker_id == self.agent_client.actor.id
                                        im_buyer = order_db.ad.pair_side.is_sell == im_taker
                                        if order_db.ad.auto_msg != upd.message and upd.roleType == "user":
                                            msg, _ = await models.Msg.update_or_create(
                                                {
                                                    "to_maker": upd.userId == self.agent_client.actor.exid and im_taker,
                                                    "sent_at": datetime.fromtimestamp(float(upd.createDate) / 1000),
                                                },
                                                txt=upd.message,
                                                order=order_db,
                                            )
                                            if not upd.message:
                                                ...
                                            if im_buyer and (g := re.match(r"^[PpРр]\d{7,10}\b", upd.message)):
                                                if not order_db.cred.detail.startswith(dest := g.group()):
                                                    order_db.cred.detail = dest
                                                    await order_db.save()
                                                await self.send_payment(order_db)
                                case "READ":
                                    upd = Read.model_validate(data["data"])
                                    # if upd.status not in (StatusWs.created, StatusWs.canceled, 10, StatusWs.completed):
                                    if upd.orderStatus in (
                                        StatusApi.wait_for_buyer,
                                    ):  # todo: тут приходит ордер.статус=10, хотя покупатель еще не нажал оплачено
                                        order = self.agent_client.api.get_order_details(orderId=upd.orderId)["result"]
                                        order = OrderFull.model_validate(order)

                                case "CLEAR":
                                    continue
                                case _:
                                    self.listen(data)
                        case "OTC_USER_CHAT_MSG_V2":
                            # match data["type"]:
                            #     case "RECEIVE":
                            #         upd = Receive.model_validate(data["data"])
                            #     case "READ":
                            #         upd = Read.model_validate(data["data"])
                            #     case "CLEAR":
                            #         pass
                            #     case _:
                            #         self.listen(data)
                            continue
                        case "SELLER_CANCEL_CHANGE":
                            upd = SellerCancelChange.model_validate(data["data"])
                        case None:
                            if not data.get("success"):
                                logging.error(data, "NOT SUCCESS!")
                            else:
                                continue  # success login, subscribes, input
                        case _:
                            logging.warning(data, "UNKNOWN TOPIC")
                    if not upd:
                        logging.warning(data, "NOT PROCESSED UPDATE")

    async def money_upd(self, order_db: models.Order):
        # обновляем остаток монеты
        await order_db.fetch_related("ad__pair_side__pair", "cred", "transfer")
        ass = await models.Asset.get(
            addr__coin_id=order_db.ad.pair_side.pair.coin_id, addr__actor=self.agent_client.actor
        )
        # обновляем остаток валюты
        fiat = await models.Fiat.get(
            cred__person_id=self.agent_client.actor.person_id, cred__pmcur_id=order_db.cred.pmcur_id
        ).prefetch_related("cred__pmcur__pm")
        fee = round(order_db.amount * (fiat.cred.pmcur.pm.fee or 0) * 0.0001)
        im_seller = order_db.ad.pair_side.is_sell == (_im_maker := order_db.ad.maker_id == self.agent_client.actor.id)
        # k = int(im_seller) * 2 - 1  # im_seller: 1, im_buyer: -1
        if order_db.status == OrderStatus.created:
            if im_seller:
                ass.free -= order_db.quantity
                ass.freeze += order_db.quantity
            else:  # я покупатель
                fiat.amount -= order_db.amount + fee
        elif order_db.status == OrderStatus.completed:
            if im_seller:
                fiat.amount += order_db.amount
            else:  # я покупатель
                ass.free += order_db.quantity
        elif order_db.status == OrderStatus.canceled:
            if im_seller:
                ass.free += order_db.quantity
                ass.freeze -= order_db.quantity
            else:  # я покупатель
                fiat.amount += order_db.amount + fee
        else:
            logging.exception(order_db.id, f"STATUS: {order_db.status.name}")
        await ass.save(update_fields=["free", "freeze"])
        await fiat.save(update_fields=["amount"])
        logging.info(f"Order #{order_db.id} {order_db.status.name}. Fiat: {fiat.amount}, Asset: {ass.free}")

    async def send_payment(self, order_db: models.Order):
        if order_db.status != OrderStatus.created:
            return
        fmt_am = round(order_db.amount * 10**-2, 2)
        pma, cur = await self.get_pma_by_pmex(order_db)
        async with in_transaction():
            # отмечаем ордер на бирже "оплачен"
            pmex = await models.PmEx.get(pm_id=order_db.cred.pmcur.pm_id, ex=self.agent_client.actor.ex)
            credex = await models.CredEx.get(cred=order_db.cred, ex=self.agent_client.actor.ex)
            self.agent_client.api.mark_as_paid(
                orderId=str(order_db.exid),
                paymentType=pmex.exid,  # pmex.exid
                paymentId=str(credex.exid),  # credex.exid
            )
            # проверяем не отправляли ли мы уже перевод по этому ордеру
            if t := await models.Transfer.get_or_none(order=order_db, amount=order_db.amount):
                await pma.bot.send(
                    f"Order# {order_db.exid}: Double send {fmt_am}{cur} to {order_db.cred.detail} #{t.pmid}!",
                    self.agent_client.actor.person.user.username_id,
                )
                raise Exception(
                    f"Order# {order_db.exid}: Double send {fmt_am}{cur} to {order_db.cred.detail} #{t.pmid}!"
                )

            # ставим в бд статус "оплачен"
            order_db.status = OrderStatus.paid
            order_db.payed_at = datetime.now(timezone.utc)
            await order_db.save()
            # создаем перевод в бд
            t = models.Transfer(order=order_db, amount=order_db.amount, updated_at=now())
            # отправляем деньги
            tid, img = await pma.send(t)
            t.pmid = tid
            await t.save()
            await self.send_receipt(str(order_db.exid), tid)  # отправляем продавцу чек
            logging.info(f"Order {order_db.exid} PAID at {datetime.now()}: {fmt_am}!")

    async def send_receipt(self, oexid: str, tid: int) -> tuple[PmAgentClient | None, models.CredEx] | None:
        try:
            if res := self.agent_client.api.upload_chat_file(upload_file=f"tmp/{tid}.png").get("result"):
                await sleep(0.5)
                self.agent_client.api.send_chat_message(
                    orderId=oexid, contentType="pic", message=res["url"], msgUuid=uuid4().hex
                )
        except Exception as e:
            logging.error(e)
        await sleep(0.5)
        self.agent_client.api.send_chat_message(
            orderId=oexid, contentType="str", message=f"#{tid}", msgUuid=uuid4().hex
        )

    async def get_pma_by_cdex(self, order: OrderFull) -> tuple[PmAgentClient | None, models.CredEx] | None:
        cdxs = await models.CredEx.filter(
            ex=self.agent_client.ex_client.ex,
            exid__in=[ptl.id for ptl in order.paymentTermList],
            cred__person=self.agent_client.actor.person,
        ).prefetch_related("cred__pmcur__cur")
        pmas = [pma for cdx in cdxs if (pma := self.pmacs.get(cdx.cred.pmcur.pm_id))]
        if not len(pmas):
            # raise ValueError(order.paymentTermList, f"No pm_agents for {order.paymentTermList[0].paymentType}")
            return None
        elif len(pmas) > 1:
            logging.error(order.paymentTermList, f">1 pm_agents for {cdxs[0].cred.pmcur.pm_id}")
        else:
            return pmas[0], cdxs[0]

    async def get_pma_by_pmex(self, order_db: models.Order) -> tuple[PmAgentClient, str]:
        pma = self.pmacs.get(order_db.cred.pmcur.pm_id)
        if pma:
            return pma, order_db.cred.pmcur.cur.ticker
        logging.error(f"No pm_agents for {order_db.cred.pmcur.pm_id}")

    @staticmethod
    def listen(data: dict | None):
        # print(data)
        ...


async def main():
    from x_model import init_db
    from xync_client.loader import TORM

    cn = await init_db(TORM, True)
    logging.basicConfig(level=logging.INFO)

    agent = (
        await models.Agent.filter(
            actor__ex_id=4,
            active=True,
            auth__isnull=False,
            actor__person__user__status=UserStatus.ACTIVE,
            actor__person__user__pm_agents__isnull=False,
        )
        .prefetch_related("actor__ex", "actor__person__user__gmail")
        .first()
    )
    pm_agents = await models.PmAgent.filter(
        active=True,
        auth__isnull=False,
        user__status=UserStatus.ACTIVE,
    ).prefetch_related("pm", "user__gmail")

    bbot = XyncBot(PAY_TOKEN, cn)

    async with FileClient(NET_TOKEN) as b:
        b: FileClient
        cl: InAgentClient = agent.in_client(b, bbot)
        # await cl.agent_client.export_my_ads()
        # payeer_cl = Client(actor.person.user.username_id)
        for pma in pm_agents:
            pcl: PmAgentClient = pma.client(bbot)
            cl.pmacs[pma.pm_id] = await pcl.start(await async_playwright().start(), False)
        try:
            _ = await cl.start_listen()
        except Exception as e:
            await b.send("😱Bybit InAgent CRASHED!!!😱", agent.actor.person.user.username_id)
            await b.send(f"```\n{''.join(traceback.format_exception(e))}\n```", agent.actor.person.user.username_id)
        await cl.agent_client.close()


if __name__ == "__main__":
    run(main())
