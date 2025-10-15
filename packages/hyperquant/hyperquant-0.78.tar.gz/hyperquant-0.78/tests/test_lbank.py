import asyncio
import json
import time
import zlib
from typing import Literal, Union

from aiohttp import ClientWebSocketResponse
from aiohttp.client_exceptions import ContentTypeError
import pybotters


def callback(msg, ws: ClientWebSocketResponse = None):
    # print("Received message:", msg)
    decompressed = zlib.decompress(msg, 16 + zlib.MAX_WBITS)
    text = decompressed.decode("utf-8")
    print(f"Decoded text: {text}")

def callback2(msg, ws: ClientWebSocketResponse = None):
    # print("Received message:", msg)
    # print(str(msg))
    data = json.loads(msg)  
    print(data.get('y'))


async def main():
    async with pybotters.Client() as client:
        # webData2
        client.ws_connect(
            "wss://ccws.rerrkvifj.com/ws/V3/",
            send_json={
                "dataType": 3,
                "depth": 200,
                "pair": "arb_usdt",
                "action": "subscribe",
                "subscribe": "depth",
                "msgType": 2,
                "limit": 10,
                "type": 10000,
            },
            hdlr_bytes=callback,
        )

        while True:
            await asyncio.sleep(1)


async def main2():
    async with pybotters.Client() as client:
        # webData2
        # x 为chanel, y为唯一标识, a为参数, z为版本号
        wsapp = client.ws_connect(
            "wss://uuws.rerrkvifj.com/ws/v3",
            send_json={'x': 3, 'y': '3000000001', 'a': {'i': 'SOLUSDT_0.01_25'}, 'z': 1},
            hdlr_bytes=callback2,
        )
        await wsapp._event.wait()

        async with pybotters.Client() as client2:
            client2.ws_connect(
                "wss://uuws.rerrkvifj.com/ws/v3",
                send_json={'x': 3, 'y': '3000000002', 'a': {'i': 'XRPUSDT_0.0001_25'}, 'z': 1},
                hdlr_bytes=callback2,
            )
            await wsapp.current_ws.send_json({'x': 3, 'y': '3000000002', 'a': {'i': 'XRPUSDT_0.0001_25'}, 'z': 1})

        while True:
            await asyncio.sleep(1)

from hyperquant.broker.lbank import Lbank

async def test_broker():
    async with pybotters.Client() as client:
        async with Lbank(client) as lb:
            print(lb.store.detail.find())


async def test_broker_detail():
    async with pybotters.Client() as client: 
        data = await client.post(
            "https://uuapi.rerrkvifj.com/cfd/agg/v1/instrument",
            headers={"source": "4", "versionflage": "true"},
            json={
            "ProductGroup": "SwapU"
            }
        ) 
        res = await data.json()
        print(res)

async def test_broker_subbook():
    async with pybotters.Client() as client:
        async with Lbank(client) as lb:
            symbols = [item['symbol'] for item in lb.store.detail.find()]
            symbols = symbols[10:30]
            print(symbols)

            await lb.sub_orderbook(symbols, limit=1)
            
            while True:
                print(lb.store.book.find({
                    "s": symbols[8]
                }))
                await asyncio.sleep(1)

async def test_update():
    async with pybotters.Client(apis='./apis.json') as client:
        async with Lbank(client) as lb:
            await lb.update('position')
            print(lb.store.position.find())
            # await lb.update('balance')
            # print(lb.store.balance.find())
            # await lb.update('detail')
            # print(lb.store.detail.find())
            # await lb.update('orders')
            # await lb.update('orders_finish')
  
            # print(lb.store.order_finish.find({
            #     'order_id': '1000632478428573'
            # }))

async def test_place():
    async with pybotters.Client(apis='./apis.json') as client:
        async with Lbank(client) as lb:
            order = await lb.place_order(
                "SOLUSDT",
                direction="buy",
                order_type='limit_gtc',
                price=182,
                volume=0.03,
            )
            print(order)



async def test_cancel():
    async with pybotters.Client(apis='./apis.json') as client:
        async with Lbank(client) as lb:
            res = await lb.cancel_order("1000624020664540")
            print(res)


async def order_sync_polling(
    broker: Lbank,
    *,
    symbol: str,
    direction: Literal["buy", "sell"] = "buy",
    order_type: Literal["market", "limit_gtc", "limit_ioc", "limit_GTC", "limit_IOC"] = "limit_gtc",
    price: float | None = None,
    volume: float | None = None,
    window_sec: float = 5.0,
    grace_sec: float = 5.0,
    poll_interval: float = 0.5
) :
    
    """
    返回
    {'order_id': '1000633291976722', 'instrument_id': 'SOLUSDT', 'position_id': '1000633291830781', 'direction': '1', 'offset_flag': '0', 'trade_time': 1760203736, 'avg_price': 183.95000000000002, 'volume': 0.03, 'turnover': 5.5185, 'fee': 0.0033111, 'trade_count': 1}
    或者
    {'order_id': '1000633291976722', 'trade_count': 0}
    """

    norm_type = order_type.lower()
    started = int(time.time() * 1000)
    resp = await broker.place_order(
        symbol,
        direction=direction,
        order_type=norm_type,
        price=price,
        volume=volume,
    )
    
    latency = int(time.time() * 1000) - started
    print(resp)

    order_id = resp.get("orderSysID")
    # print(f"下单延迟 {latency} ms, 订单号: {order_id}")

    if not order_id:
        raise RuntimeError(f"place_order 返回缺少 order_id: {resp}")


    position_id = resp.get("positionID")
    if not position_id:
        raise RuntimeError(f"place_order 返回缺少 position_id: {resp}")
    
    trade_resp = None

    if 'volumeRemain' in resp and float(resp['volumeRemain']) == 0 and float(resp.get('turnover', 0)) != 0:
        return {
            "order_id": order_id,
            "trade_count": 1,
            "volume": volume,
            "avg_price": float(resp.get('tradePrice', 0)),
            "turnover": float(resp.get('turnover', 0)),
            "fee": float(resp.get('fee', 0)),
            "position_id": position_id,
            "direction": direction,
            "offset_flag": resp.get('offsetFlag', '0'),
            "trade_time": resp.get('updateTime'),
        }

    if 'ioc' in norm_type:
        return {
            "order_id": order_id,
            "trade_count": 0
        }

    async def _poll_orders(timeout_sec: float) -> dict | None:
        nonlocal trade_resp
        async with asyncio.timeout(timeout_sec):
            while True:
                trade_resp = await broker.query_order(order_id)
                traded_volume = float(trade_resp.get("volume", 0))
                if traded_volume == volume:
                    return
                await asyncio.sleep(poll_interval)

    try:
        await _poll_orders(window_sec)
    
    except TimeoutError:
        pass

        for _attempt in range(3):
            try:
                await broker.cancel_order(order_id)
                break
            except Exception as e:
                if '不存在' in str(e):
                    break
                else:
                    print(f'撤单失败, 重试 {_attempt+1}/3: {e}')
        
        try:
            await _poll_orders(window_sec)
        except TimeoutError:
            pass

    return trade_resp


async def test_order_sync_polling():
    async with pybotters.Client(apis="./apis.json") as client:
        async with Lbank(client) as lb:
            await lb.sub_orderbook(["SOLUSDT"], limit=1)
            await lb.store.book.wait()
            bid0 = float(lb.store.book.find({"s": "SOLUSDT", 'S': 'b'})[0]['p'])
            # bid0 = bid0 - 0.01
            bid0 = bid0 + 1
            # bid0 = bid0 - 1
            print(bid0)

            snapshot = await order_sync_polling(
                lb,
                symbol="SOLUSDT",
                direction="sell",
                order_type="market",
                price=bid0,
                volume=0.03,
                window_sec=3.0,
                grace_sec=1,
                poll_interval=1
            )
            print(snapshot)

            # position_id = snapshot.get("position_id")
            # if not position_id:
            #     print('没有 position_id')

            # position = None
            # for _ in range(5):
            #     await lb.update("position")
            #     position = lb.store.position.get({"position_id": position_id})
            #     if position:
            #         break
            #     await asyncio.sleep(0.1)

            # print(position)

async def test_query_order():
    async with pybotters.Client(apis='./apis.json') as client:
        async with Lbank(client) as lb:
            res = await lb.query_order("1000633355403954")
            print(res)

if __name__ == "__main__":
    asyncio.run(test_order_sync_polling())
