import logging
from asyncio import run
from base64 import b64encode
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from json import dumps
from math import ceil
from os import urandom
from time import sleep
from urllib.parse import urlencode

from PGram import Bot
from asyncpg.pgproto.pgproto import timedelta
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from payeer_api import PayeerAPI
from playwright.async_api import async_playwright, Playwright, Error

# noinspection PyProtectedMember
from playwright._impl._errors import TimeoutError
from tortoise.timezone import now
from xync_bot import XyncBot
from xync_schema.models import TopUp, TopUpAble, PmAgent, Transfer

from xync_client.loader import TORM, PAY_TOKEN

from xync_client.Abc.PmAgent import PmAgentClient
from xync_client.Pms.Payeer.login import login


def encrypt_data(data: dict, md5digest: bytes):
    # Convert data to JSON string (equivalent to json_encode)
    bdata = dumps(data).encode()

    # Generate random IV (16 bytes for AES)
    iv = urandom(16)

    # Pad or truncate key to 32 bytes
    if len(md5digest) < 32:
        md5digest = md5digest.ljust(32, b"\0")  # Pad with null bytes
    elif len(md5digest) > 32:
        md5digest = md5digest[:32]  # Truncate to 32 bytes

    # Apply PKCS7 padding
    padder = padding.PKCS7(128).padder()  # 128 bits = 16 bytes block size
    padded_data = padder.update(bdata)
    padded_data += padder.finalize()

    # Create cipher
    cipher = Cipher(AES(md5digest), CBC(iv))
    encryptor = cipher.encryptor()

    # Encrypt
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return iv + ciphertext


class Client(PmAgentClient):
    class Pages(StrEnum):
        _base = "https://payeer.com/en/"
        LOGIN = _base + "auth/"
        SEND = _base + "account/send/"

    norm: str = "payeer"
    pages: type(StrEnum) = Pages
    api: PayeerAPI
    with_userbot: bool = False

    def __init__(self, agent: PmAgent, abot: XyncBot):
        super().__init__(agent, abot)
        if api_id := self.agent.auth.get("api_id"):
            self.api = PayeerAPI(self.agent.auth["email"], api_id, self.agent.auth["api_sec"])

    async def _login(self):
        await login(self.agent)
        for cookie in self.agent.state["cookies"]:
            await self.page.context.add_cookies([cookie])
        await self.page.goto(self.pages.SEND, wait_until="commit")

    @staticmethod
    def form_redirect(topup: TopUp) -> tuple[str, dict | None]:
        m_shop = str(topup.topupable.auth["id"])
        m_orderid = str(topup.id)
        m_amount = "{0:.2f}".format(topup.amount * 0.01)
        m_curr = topup.cur.ticker
        m_desc = b64encode(b"XyncPay top up").decode()
        m_key = topup.topupable.auth["sec"]
        data = [m_shop, m_orderid, m_amount, m_curr, m_desc]

        # # additional
        # m_params = {
        #     'success_url': 'https://xync.net/topup?success=1',
        #     'fail_url': 'https://xync.net/topup?success=0',
        #     'status_url': 'https://xync.net/topup',
        #     'reference': {'var1': '1'},
        # }
        #
        # key = md5(m_orderid.to_bytes()).digest()
        #
        # base64url_encode(encrypt_data(params, key))
        #
        # data.append(m_params)
        # # additional

        data.append(m_key)

        sign = sha256(":".join(data).encode()).hexdigest().upper()

        params = {
            "m_shop": m_shop,
            "m_orderid": m_orderid,
            "m_amount": m_amount,
            "m_curr": m_curr,
            "m_desc": m_desc,
            "m_sign": sign,
            # 'm_params': m_params,
            # 'm_cipher_method': 'AES-256-CBC-IV',
            "form[ps]": "2609",
            "form[curr[2609]]": m_curr,
        }
        url = "https://payeer.com/merchant/?" + urlencode(params)
        return url, None

    def get_topup(self, tid: str) -> dict:
        hi = self.api.get_history_info(tid)
        ti = self.api.shop_order_info(hi["params"]["SHOP_ID"], hi["params"]["ORDER_ID"])["info"]
        return ti["status"] == "execute" and {
            "pmid": ti["id"],
            "from_acc": hi["params"]["ACCOUNT_NUMBER"],
            "oid": hi["params"]["ORDER_ID"],
            "amount": int(float(ti["sumOut"]) * 100),
            "ts": datetime.strptime(ti["dateCreate"], "%d.%m.%Y %H:%M:%S") - timedelta(hours=3),
        }

    async def send(self, t: Transfer) -> tuple[str, bytes] | float:
        dest, cur = t.order.cred.detail, t.order.cred.pmcur.cur.ticker
        amount = round(t.order.amount * 10**-t.order.cred.pmcur.cur.scale, t.order.cred.pmcur.cur.scale)
        self.last_active = now()
        page = self.page
        if not page.url.startswith(self.pages.SEND):
            try:
                await page.goto(self.pages.SEND, wait_until="commit")
            except (TimeoutError, Error):
                await login(self.agent)
                for cookie in self.agent.state["cookies"]:
                    await page.context.add_cookies([cookie])
                sleep(0.5)
                await page.goto("https://payeer.com/en/account/send/", wait_until="commit")
        has_amount = float(self.api.get_balance()[cur]["DOSTUPNO"])
        if amount <= has_amount:
            sleep(0.1)
            await page.locator('input[name="param_ACCOUNT_NUMBER"]').fill(dest)
            await page.locator("select[name=curr_receive]").select_option(value=cur)
            sleep(0.8)
            await page.locator('input[name="sum_receive"]').fill(str(amount))
            sleep(0.1)
            # await page.locator("div.n-form--title").first.click()
            # sleep(0.1)
            await page.click(".btn.n-form--btn.n-form--btn-mod")
            sleep(0.5)
            await page.click(".btn.n-form--btn.n-form--btn-mod")
            sleep(1.1)
            if await page.locator(".input4").count():
                await page.locator(".input4").fill(self.agent.auth.get("master_key"))
                await page.click(".ok.button_green2")
            sleep(1)
            try:
                await page.locator(".note_txt").wait_for(state="visible", timeout=6000)
            except TimeoutError as _:
                logging.error("Repeat!")
                sleep(0.5)
                return await self.send(t)
            if await page.locator('.note_txt:has-text("successfully completed")').count():
                transaction = await page.locator(".note_txt").all_text_contents()
                trans_num = transaction[0].replace("Transaction #", "").split()[0]
                await page.goto("https://payeer.com/ru/account/history/", wait_until="commit")
                await page.click(f".history-id-{trans_num} a.link")
                sleep(1)
                receipt = await page.query_selector(".ui-dialog.ui-corner-all")
                return trans_num, receipt and await receipt.screenshot(path=f"tmp/{trans_num}.png")
            else:
                await self.receive("Payeer хз", photo=await self.page.screenshot())
                return -1
        else:
            await self.receive(
                f"Payeer no have {amount}, only {has_amount}{cur} to {dest}",
                photo=await self.page.screenshot(),
            )
            return has_amount

    async def check_in(
        self, amount: Decimal | int | float, cur: str, dt: datetime = None, tid: str | int = None
    ) -> tuple[Decimal | None, int | None]:
        history = self.api.history(type="incoming", count=10)
        if tid:
            return (t := history.get(tid)) and Decimal(t["creditedAmount"])
        ts: list[dict] = [
            h
            for h in history.values()
            if (
                amount <= Decimal(h["creditedAmount"]) <= ceil(amount)
                and h["creditedCurrency"] == cur
                # todo: wrong tz
                and datetime.fromisoformat(h["date"]) > dt - timedelta(minutes=3)  # +180(tz)-5
            )
        ]
        if not (t := ts and ts[0]):
            return None, None
        return (
            amount <= (am := Decimal(t["creditedAmount"])) <= ceil(amount) and t["creditedCurrency"] == cur
        ) and am, t["id"]

    async def proof(self) -> bytes: ...


async def main(uid: int):
    from x_model import init_db

    _ = await init_db(TORM, True)
    agent = await PmAgent.get_or_none(pm__norm="payeer", user__username_id=uid).prefetch_related(
        "user__username__session", "pm"
    )
    if not agent:
        raise Exception(f"No active user #{uid} with agent for volet!")
    abot = Bot(PAY_TOKEN)
    pyr = agent.client(abot)
    playwright: Playwright = await async_playwright().start()
    try:
        dest, amount, cur = "P79619335", 4, "RUB"
        ta = await TopUpAble.get(pm__norm="payeer")
        topup = await TopUp.create(amount=1001, cur_id=1, topupable=ta, user_id=1)
        await topup.fetch_related("cur")
        _url, _data = pyr.form_redirect(topup)

        await pyr.start(playwright, False)

        _res = await pyr.send(dest, amount, cur)
        _res = await pyr.send(dest, 3, cur)

        res = pyr.check_in(3, cur, datetime.now())

        if len(res) > 1 and isinstance(res[1], bytes):
            await pyr.receive(f"Transaction #{res[0]}", photo=res[1])
        elif res[0] > 0:
            await pyr.receive(f"Sreen of transaction #{res[0]} failed", photo=await pyr.page.screenshot())
        else:
            await pyr.receive(f"Sending {amount} {cur} to {dest} FAILED", photo=await pyr.page.screenshot())

    except TimeoutError as te:
        await pyr.receive(repr(te), photo=await pyr.page.screenshot())
        raise te
    # finally:
    #     await pyr.stop()


if __name__ == "__main__":
    run(main(193017646))
