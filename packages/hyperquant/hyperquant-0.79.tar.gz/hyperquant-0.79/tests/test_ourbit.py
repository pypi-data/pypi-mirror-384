import pybotters

from hyperquant.broker.ourbit import OurbitSpot
from hyperquant.broker.ourbit import OurbitSwap

async def download_orders():
    async with pybotters.Client(
        apis={
            "ourbit": [
                "WEB3bf088f8b2f2fae07592fe1a6240e2d798100a9cb2a91f8fda1056b6865ab3ee"
            ]
        }
    ) as client:
        # 时间区间 (毫秒)
        start_time = 1757254540000   # 起始
        end_time = 1757433599999     # 结束

        page_size = 100              # 接口最大 100
        page_num = 1
        all_results = []

        while True:
            url = (
                "https://www.ourbit.com/api/platform/spot/deal/deals"
                f"?endTime={end_time}&pageNum={page_num}&pageSize={page_size}&startTime={start_time}"
            )
            res = await client.fetch("GET", url)
            result_list = res.data["data"]["resultList"]
            got = len(result_list)
            print(f"page {page_num} -> {got} items")
            all_results.extend(result_list)

            if got < page_size:      # 最后一页
                break
            page_num += 1

        print(f"total collected: {len(all_results)}")

        # 写入汇总数据
        import json
        with open("deals.json", "w") as f:
            json.dump(
                {
                    "data": {
                        "resultList": all_results,
                        "total": len(all_results),
                        "pageSize": page_size,
                        "pagesFetched": page_num
                    }
                },
                f,
                indent=2
            )
        print("Saved to deals.json")

async def test_detail():
    async with pybotters.Client() as client:
        ob = OurbitSpot(client)
        await ob.__aenter__()
        print(ob.store.detail.get({
            'name': 'OPEN'
        }))

async def test_ourbit_wrap():
    async with pybotters.Client(
        apis={
            "ourbit": [
                "WEBa07743126a6cc69a896a501404ae8357e4116059ebc5bde75020881dc53a24ba"
            ]
        }
    ) as client:
        ob = OurbitSpot(client)
        await ob.__aenter__()
        await ob.update('balance')
        print(ob.store.balance.find())


import asyncio
import time
from hyperquant.broker.ourbit import OurbitSpot
import pybotters
from hyperquant.logkit import get_logger

logger = get_logger('test_order_sync', './data/logs/test_order_sync.log', show_time=True)


# 等待指定 oid 的最终 delete，超时抛 TimeoutError
async def wait_delete(stream: pybotters.StoreStream, oid: str, seconds: float):
    async with asyncio.timeout(seconds):
        while True:
            change = await stream.__anext__()
            # print(change.operation, change.data)
            if change.operation == "delete" and change.data.get("order_id") == oid:
                return change.data  # 内含 state / avg_price / deal_quantity 等累计字段


async def order_sync(
    ob: OurbitSpot| OurbitSwap,
    symbol: str = "SOL_USDT",
    side: str = "buy",
    order_type: str = "market",  # "market" / "limit"
    usdt_amount: float | None = None,  # 市价可填
    quantity: float | None = None,  # 市价可填
    price: float | None = None,  # 限价必填
    window_sec: float = 2.0,  # 主等待窗口（限价可设为 5.0）
    grace_sec: float = 2,  # 撤单后宽限
):
    with ob.store.orders.watch() as stream:
        # 下单（只保留最简两种入参形态）
        try:
            if isinstance(ob, OurbitSwap):
                oid = await ob.place_order(
                    symbol,
                    side,
                    order_type=order_type,
                    usdt_amount=usdt_amount,
                    quantity=quantity,
                    price=price
                )
        except Exception as e:
            return {"symbol": symbol, "state": "error", "error": str(e)}

        # 步骤1：主窗口内等待这单的最终 delete
        try:
            return await wait_delete(stream, oid, window_sec)
        except TimeoutError:
            # 步骤2：到点撤单（市价通常用不到；限价才有意义）
            for i in range(3):
                try:
                    await ob.cancel_order(oid)
                    break
                except Exception:
                    pass
                await asyncio.sleep(0.1)
            # 固定宽限内再等“迟到”的最终 delete
            try:
                return await wait_delete(stream, oid, grace_sec)
            except TimeoutError:
                return {"order_id": oid, "symbol": symbol, "state": "timeout"}


async def test_order_sync_spot():
    async with pybotters.Client(
        apis={
            "ourbit": [
                "WEB3bf088f8b2f2fae07592fe1a6240e2d798100a9cb2a91f8fda1056b6865ab3ee"
            ]
        }
    ) as client:
        ob = OurbitSpot(client)
        await ob.__aenter__()
        await ob.sub_personal()  # 私有频道
        ob.store.book.limit = 3
        await ob.sub_orderbook(["SOL_USDT"])  # 订单簿频道
        # # 示例：市价
        # now= time.time()
        result = await order_sync( ob, symbol="SOL_USDT", side="buy", order_type="market", usdt_amount=8, price=200, window_sec=2)
        print(result)
        

async def test_order_sync_swap():
    async with pybotters.Client(
        apis={
            "ourbit": [
                "WEBb401428e69af1815808e470be0a4f4e8a70a5c5cc0b0df0a33220f689167c629"
            ]
        }
    ) as client:
        ob = OurbitSwap(client)
        await ob.__aenter__()
        await ob.sub_personal()  # 私有频道
 
        # await ob.sub_orderbook(["SOL_USDT"])  # 订单簿频道
        # # 示例：市价
        # now= time.time()
        result = await order_sync( ob, symbol="SOL_USDT", side="buy", order_type="market", usdt_amount=8, price=200, window_sec=3)
        print(result)


async def test_order_close_swap():
    async with pybotters.Client(
        apis={
            "ourbit": [
                "WEBb401428e69af1815808e470be0a4f4e8a70a5c5cc0b0df0a33220f689167c629"
            ]
        }
    ) as client:
        ob = OurbitSwap(client)
        await ob.__aenter__()
        # await ob.sub_personal()  # 私有频道
        # result = await order_sync( ob, symbol="SOL_USDT", side="buy", order_type="market", usdt_amount=8, price=200, window_sec=3)
        # print(result)
        oid = await ob.place_order(
            "SOL_USDT",
            "buy",
            order_type="limit_GTC",
            size=1,
            price=200
        )

        print(oid)

        # print(oid)
        # await ob.update('position')
        # print(ob.store.position.find())

        # await ob.place_order('SOL_USDT', 'close_sell', 1, position_id=6062178)

async def test_sub_book():
    async with pybotters.Client(
    ) as client:
        ob = OurbitSwap(client)
        await ob.__aenter__()
        ob.store.book.limit = 1
        await ob.sub_orderbook(["BIO_USDT", "MAIGA_USDT", "TST_USDT"])  # 订单簿频道
        while True:
            await asyncio.sleep(1)
            print(ob.store.book.sorted(query={"S": 'b'}, limit=1))
          


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_sub_book())