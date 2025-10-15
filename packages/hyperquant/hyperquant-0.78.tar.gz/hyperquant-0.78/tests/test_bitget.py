import asyncio
import time
from typing import Literal

import pybotters
from hyperquant.broker.models.bitget import BitgetDataStore
pybotters.auth

async def test_update():
    async with pybotters.Client() as client:
        store = BitgetDataStore()
        # await store.initialize(
        #     client.get("https://api.bitget.com/api/v2/mix/market/contracts?productType=usdt-futures")
        # )
        # print(store.detail.find())
        await store.initialize(
            client.get(
                "https://api.bitget.com/api/v2/mix/market/tickers?productType=usdt-futures"
            )
        )
        print(store.ticker.find({"symbol": "BTCUSDT"}))


async def subscribe_book():

    async with pybotters.Client() as client:
        store = BitgetDataStore()
        client.ws_connect(
            "wss://ws.bitget.com/v2/ws/public",
            send_json={
                "op": "subscribe",
                "args": [
                    {"instType": "SPOT", "channel": "books1", "instId": "BTCUSDT"}
                ]
            },
            hdlr_json=store.onmessage
        )

        while True:
            await asyncio.sleep(1)
            print(store.book.find())

from hyperquant.broker.bitget import Bitget
async def test_broker_update():

    async with pybotters.Client() as client:
        bg = Bitget(client)
        store = BitgetDataStore()
        # await bg.update('all')
        # print(bg.store.detail.find())
        await bg.update('ticker')
        print(bg.store.ticker.find())

async def test_broker_sub_orderbook():
    async with pybotters.Client() as client:
        bg = Bitget(client)
        await bg.sub_orderbook(['BTCUSDT', 'ETHUSDT'])
        while True:
            await asyncio.sleep(1)
            print(bg.store.book.find())

async def test_order():
    async with pybotters.Client(apis='./apis.json') as client:
        bg = Bitget(client)
        await bg.__aenter__()
        ts = time.time() * 1000
        res = await bg.place_order(
            'SOLUSDT',
            direction='long',
            order_type='limit_gtc',
            volume=0.1,
            price=185
        )
        # print(res)
        print(f'订单延迟: {time.time() * 1000 - ts} ms')

async def test_sub_personal():
    async with pybotters.Client(apis='./apis.json') as client:
        bg = Bitget(client)
        await bg.__aenter__()
        await bg.sub_personal()
 
        # # 监听订单变化
        # with bg.store.orders.watch() as stream:
        #     async for change in stream:
        #         print("Orders changed:", change)

        # 监听持仓变化
        with bg.store.positions.watch() as stream:
            async for change in stream:
                print("Positions changed:", change)

async def order_sync_polling(
    broker: Bitget,
    *,
    symbol: str,
    direction: Literal["buy", "sell", "long", "short"] = "buy",
    order_type: Literal[
        "market",
        "limit_gtc",
        "limit_ioc",
        "limit_fok",
        "limit_post_only",
        "limit",
    ] = "limit_gtc",
    price: float | None = None,
    volume: float | None = None,
    margin_mode: Literal["isolated", "crossed"] = "crossed",
    product_type: str = "USDT-FUTURES",
    margin_coin: str = "USDT",
    window_sec: float = 5.0,
    grace_sec: float = 5.0,
) -> dict:
    """
    基于 Bitget 私有 WS 的订单轮询：window 期内等待终态，超时后撤单并返回结果。
    """

    norm_type = order_type.lower()
    if norm_type not in {
        "market",
        "limit",
        "limit_gtc",
        "limit_ioc",
        "limit_fok",
        "limit_post_only",
    }:
        raise ValueError(f"unsupported order_type: {order_type}")

    order = None
    try:
        async with asyncio.timeout(window_sec):
            # 监控订单
            with broker.store.orders.watch() as stream:
                started = int(time.time() * 1000)
                resp = await broker.place_order(
                    symbol,
                    direction=direction,
                    order_type=norm_type,
                    price=price,
                    volume=volume,
                    margin_mode=margin_mode,
                    product_type=product_type,
                    margin_coin=margin_coin,
                )
                latency = int(time.time() * 1000) - started
                print(f"下单延迟 {latency} ms")

                order_id = resp.get("orderId")
                
                if not order_id:
                    raise RuntimeError(f"place_order 返回缺少 order_id: {resp}")
                while True:
                    change = await stream.__anext__()

                    if change.data.get("orderId") == order_id:
                        order = change.data
                        print(change.operation)
                        if change.operation == "delete":
                            return change.data
    except TimeoutError:
        pass    

    for i in range(3):
        try:
            await broker.cancel_order(order_id, symbol=symbol, margin_mode='crossed')
            break
        except Exception as e:
            print(f"撤单异常: {e}")
        await asyncio.sleep(1.0)

    return order

async def test_order_sync_polling():
    async with pybotters.Client(apis="./apis.json") as client:
        bg = Bitget(client)
        await bg.__aenter__()
        await bg.sub_personal()

        result = await order_sync_polling(
            bg,
            symbol="SOLUSDT",
            direction="long",
            order_type="limit_gtc",
            price=185,
            volume=0.1,
            window_sec=5.0,
            grace_sec=5.0,
        )
        print(result)


if __name__ == "__main__":
    asyncio.run(test_order_sync_polling())
