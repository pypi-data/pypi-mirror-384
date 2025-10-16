import asyncio
import hashlib
import random
import re
import time
from hyperquant.broker.lib.edgex_sign import LimitOrderMessage, LimitOrderSigner
import pybotters
from hyperquant.broker.edgex import Edgex


def gen_client_id():
    # 1. 生成 [0,1) 的浮点数
    r = random.random()
    # 2. 转成字符串
    s = str(r)  # e.g. "0.123456789"
    # 3. 去掉 "0."
    digits = s[2:]
    # 4. 去掉前导 0
    digits = re.sub(r"^0+", "", digits)
    return digits


def calc_nonce(client_order_id: str) -> int:
    digest = hashlib.sha256(client_order_id.encode()).hexdigest()
    return int(digest[:8], 16)


async def place_order(client_id: str = None):

    args = {
        "price": "210.00",
        "size": "1.0",
        "type": "LIMIT",
        "timeInForce": "GOOD_TIL_CANCEL",
        "reduceOnly": False,
        "isPositionTpsl": False,
        "isSetOpenTp": False,
        "isSetOpenSl": False,
        "accountId": "663528067938910372",
        "contractId": "10000003",
        "side": "BUY",
        "triggerPrice": "",
        "triggerPriceType": "LAST_PRICE",
        "clientOrderId": "39299826149407513",
        "expireTime": "1760352231536",
        "l2Nonce": "1872301",
        "l2Value": "210",
        "l2Size": "1.0",
        "l2LimitFee": "1",
        "l2ExpireTime": "1761129831536",
        "l2Signature": "03c4d84c30586b12ab9fec939a875201e58dac9a0391f15eb6118ab2fb50464804ce38b19cc5e07c973fc66b449bec0274058ea2d012c1c7a580f805d2c7a1d3",
        "extraType": "",
        "extraDataJson": "",
        "symbol": "SOLUSD",
        "showEqualValInput": False,
        "maxSellQTY": 1,  # 不需要特别计算, 服务器不校验
        "maxBuyQTY": 1,  # 不需要特别计算, 服务器不校验
    }

    cid = gen_client_id() or client_id
    nonce = calc_nonce(cid)

    now = int(time.time() * 1000)
    expire_time = now + 2592e6  # 30 天后
    start_time = expire_time - 7776e5  # 提前 9 天
    args["expireTime"] = str(int(start_time))
    args["l2ExpireTime"] = str(int(expire_time))
    args["clientOrderId"] = cid

    message = LimitOrderMessage(
        asset_id_synthetic="0x534f4c2d3800000000000000000000",
        asset_id_collateral="0x2ce625e94458d39dd0bf3b45a843544dd4a14b8169045a3a3d15aa564b936c5",
        asset_id_fee="0x2ce625e94458d39dd0bf3b45a843544dd4a14b8169045a3a3d15aa564b936c5",
        is_buy=True,  # isBuyingSynthetic
        amount_synthetic=int("100000000"),  # quantumsAmountSynthetic
        amount_collateral=int("210000000"),  # quantumsAmountCollateral
        amount_fee=int("1000000"),  # quantumsAmountFee
        nonce=int(nonce),  # nonce
        position_id=int("663528067938910372"),  # positionId
        expiration_epoch_hours=int("489203"),  # 此处也比较重要 # TODO: 计算
    )

    signer = LimitOrderSigner(
        "02b746d6a832346a46a97faf054b2909c1a0b58a35e04c3504923a99a5503c1c"
    )
    hash_hex, signature_hex = signer.sign(message)

    args["l2Signature"] = signature_hex
    args["l2Nonce"] = str(nonce)

    async with pybotters.Client(apis="./apis.json") as client:

        res = await client.fetch(
            "POST",
            "https://pro.edgex.exchange/api/v1/private/order/createOrder",
            data=args,
        )

        print(res.data)


async def test_detail():
    async with pybotters.Client(apis="./apis.json") as client:

        async with Edgex(client) as edgex:
            print(edgex.store.detail.find({"contractName": "SOLUSD"}))

async def test_balance():
    async with pybotters.Client(apis="./apis.json") as client:

        async with Edgex(client) as edgex:
            await edgex.update('balance')
            print(edgex.store.balance.find())

async def test_position():
    async with pybotters.Client(apis="./apis.json") as client:

        async with Edgex(client) as edgex:
            await edgex.update('position')
            print(edgex.store.position.find())

async def place_order2():
    async with pybotters.Client(apis="./apis.json") as client:

        async with Edgex(client) as edgex:
            ts = int(time.time() * 1000)
            oid = await edgex.place_order(
                symbol="ORDIUSD",
                price="8.23",
                quantity="10",
                side="buy",
                order_type="limit_ioc"
            )
            print(oid)
            print(f'下单延迟: {int(time.time() * 1000) - ts} ms')

            # await asyncio.sleep(10)
            
            # data = await edgex.cancel_orders(['665195325752869540'])
            # print(data)


async def place_order_with_stream():
    async with pybotters.Client(apis="./apis.json") as client:

        async with Edgex(client) as edgex:
            await edgex.sub_personal()
            # await edgex.sub_orderbook(symbols=["SOLUSD"])
            with edgex.store.orders.watch() as stream:
                ts = int(time.time() * 1000)
                oid = await edgex.place_order(
                    symbol="SOLUSD",
                    price=195,
                    quantity="0.3",
                    side="buy",
                    order_type="limit_gtc"
                )
                print(f'下单延迟: {int(time.time() * 1000) - ts} ms')

                async for data in stream:
                    print(data.operation, data.data)

async def watch_orders():
    async with pybotters.Client(apis="./apis.json") as client:

        async with Edgex(client) as edgex:
            await edgex.sub_personal()
            with edgex.store.orders.watch() as stream:
                async for data in stream:
                    print(data.operation, data.data)


async def watch_position():
    async with pybotters.Client(apis="./apis.json") as client:

        async with Edgex(client) as edgex:
            await edgex.sub_personal()
            print(edgex.userid, 'ready')
            with edgex.store.position.watch() as stream:
                async for data in stream:
                    print(data.operation, data.data)

async def test_update():
    async with pybotters.Client(apis="./apis.json") as client:

        async with Edgex(client) as edgex:
            await edgex.update('orders')
            # print(edgex.store.orders.find())

async def watch_ticker():
    async with pybotters.Client(apis="./apis.json") as client:

        async with Edgex(client) as edgex:
            await edgex.sub_ticker(all_contracts=True, periodic=True)
            print('ticker subscribed')
            await edgex.store.ticker.wait()
            print(edgex.store.ticker.find())
if __name__ == "__main__":
    asyncio.run(place_order2())