REST 均为 https://uuapi.rerrkvifj.com

# 下单示例

## 下单参数示例
```json
https://uuapi.rerrkvifj.com/cfd/cff/v1/SendOrderInsert

{
  "InstrumentID": "SOLUSDT",        // 交易品种代码
  "ExchangeID": "Exchange",         // 交易所标识
  "Direction": "0",                 // 买卖方向，0表示开多（买入），1表示开空（卖出）
  "OffsetFlag": "0",                // 开平标志，0表示开仓
  "OrderPriceType": "0",            // 报价类型，0表示限价，4表示市价
  "OrderType": "0",                 // 订单类型, 配合OrderPriceType
  "Price": 202.27,                  // 价格，限价单必填，市价单可不填
  "Volume": 0.03,                   // 数量
  "orderProportion": "0.0000"       // 下单比例，通常为"0.0000"
}
```

### 参数说明及调整
- **Direction**：  
  - `0` 表示开多（买入）  
  - `1` 表示开空（卖出）

- **OrderPriceType**：  
  - `0` 表示限价单  
  - `4` 表示市价单

- **OrderType**：  
  - `0` 表示普通限价单（包括FAK限价单，需根据交易所规则设置）  
  - `1` 表示市价单

- **Price**：  
  - 限价单需要填写具体价格  
  - 市价单可省略或不填写价格字段

- **OffsetFlag**：  
  - `0` 表示开仓

根据上述参数的不同组合，可以实现以下订单类型：

| 订单类型   | Direction | OrderPriceType | OrderType | Price      | 说明                 |
|------------|-----------|----------------|-----------|------------|----------------------|
| 限价开多   | 0         | 0              | 0         | 具体价格   | 买入限价单           |
| 限价开空   | 1         | 0              | 0         | 具体价格   | 卖出限价单           |
| 市价开多   | 0         | 4              | 1         | 不填或忽略 | 买入市价单           |
| 市价开空   | 1         | 4              | 1         | 不填或忽略 | 卖出市价单           |
| 限价FAK开多| 0         | 0              | 1         | 具体价格   | 限价立即成交否则撤销 |
| 限价FAK开空| 1         | 0              | 1         | 具体价格   | 限价立即成交否则撤销 |

请根据实际需求调整对应字段值完成下单。

# 撤单示例

https://uuapi.rerrkvifj.com/cfd/action/v1.0/SendOrderAction
{
    "OrderSysID": "1000623558020554",
    "ActionFlag": "1"
}

{
    "code": 200,
    "data": {
        "offsetFlag": "0",
        "orderType": "0",
        "reserveMode": "0",
        "fee": "0",
        "frozenFee": "0",
        "ddlnTime": "0",
        "userID": "lbank_exchange_user",
        "masterAccountID": "",
        "exchangeID": "Exchange",
        "accountID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
        "orderSysID": "1000623558020554",
        "volumeRemain": "0",
        "price": "180",
        "businessValue": "1758806193849",
        "frozenMargin": "0",
        "instrumentID": "SOLUSDT",
        "posiDirection": "2",
        "volumeMode": "1",
        "volume": "0.05",
        "insertTime": "1758806193",
        "copyMemberID": "",
        "position": "0",
        "leverage": "100",
        "businessResult": "",
        "availableUse": "0",
        "orderStatus": "6",
        "frozenMoney": "0",
        "remark": "def",
        "reserveUse": "0",
        "sessionNo": "122",
        "isCrossMargin": "1",
        "closeProfit": "0",
        "businessNo": "1001748583265110",
        "relatedOrderSysID": "",
        "positionID": "1000623558020554",
        "mockResp": false,
        "deriveSource": "0",
        "copyOrderID": "",
        "currency": "USDT",
        "turnover": "0",
        "frontNo": "-62",
        "direction": "0",
        "orderPriceType": "0",
        "volumeCancled": "0.05",
        "updateTime": "1758806302",
        "localID": "04f55ebabde94ab980b6",
        "volumeTraded": "0",
        "minVolume": "0",
        "appid": "WEB",
        "tradeUnitID": "e1b03fb1-6849-464f-a",
        "businessType": "P",
        "memberID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
        "timeCondition": "0",
        "copyProfit": "0"
    },
    "message": "成功"
}

# 查询存在订单

GET

https://uuapi.rerrkvifj.com/cfd/query/v1.0/Order?ProductGroup=SwapU&ExchangeID=Exchange&pageIndex=1&pageSize=1000

{
    "code": 200,
    "data": {
        "data": [
            {
                "MinVolume": "0.0",
                "BusinessNo": "1001748588060854",
                "PositionID": "1000623560990310",
                "DeriveSource": "0",
                "BusinessType": "P",
                "IsCrossMargin": "1",
                "OrderType": "0",
                "Currency": "USDT",
                "Turnover": "0.0",
                "Leverage": "25.0",
                "FrozenMargin": "0.312",
                "AvailableUse": "0.0",
                "PosiDirection": "2",
                "InsertTime": "1758806564",
                "Price": "3900.0",
                "Volume": "0.002",
                "VolumeRemain": "0.002",
                "VolumeMode": "1",
                "ReserveMode": "0",
                "TradeUnitID": "e1b03fb1-6849-464f-a",
                "VolumeTraded": "0.0",
                "CloseProfit": "0.0",
                "InstrumentID": "ETHUSDT",
                "Direction": "0",
                "OrderPriceType": "0",
                "OffsetFlag": "0",
                "OrderStatus": "4",
                "FrozenMoney": "0.0",
                "UserID": "lbank_exchange_user",
                "OrderSysID": "1000623560990310",
                "seq": 96749124311,
                "ExchangeID": "Exchange",
                "AccountID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                "seriesNo": 746725156597,
                "FrontNo": "-61",
                "FrozenFee": "0.00468",
                "Fee": "0.0",
                "VolumeCancled": "0.0",
                "MemberID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                "ReserveUse": "0.0",
                "UpdateTime": "1758806564",
                "SessionNo": "132",
                "TimeCondition": "0"
            }
        ]
    },
    "message": "成功"
}

# balance相关

https://uuapi.rerrkvifj.com/cfd/agg/v1/sendQryAll

POST
{
    "productGroup": "SwapU",
    "instrumentID": "ETHUSDT",
    "asset": "USDT"
}

{
    "code": 200,
    "data": {
        "fundingRateTimestamp": 28800,
        "isMarketAcount": 0,
        "longMaxVolume": 10000000000000000,
        "role": 2,
        "openingTime": 1609545600000,
        "isCrossMargin": 1,
        "longLeverage": 25,
        "shortLastVolume": 10000000000000000,
        "longLastVolume": 10000000000000000,
        "onTime": 1609459200000,
        "shortMaintenanceMarginRate": "0.0025",
        "state": 3,
        "markedPrice": "4001.45",
        "assetBalance": {
            "reserveAvailable": "0.0",
            "balance": "9.902",
            "frozenMargin": "0.312",
            "reserveMode": "0",
            "totalCloseProfit": "1.17458",
            "available": "9.58532",
            "crossMargin": "0.0",
            "reserve": "0.0",
            "frozenFee": "0.00468",
            "marginAble": "0.0",
            "realAvailable": "9.58532"
        },
        "longMaxLeverage": 200,
        "shortMaintenanceMarginQuickAmount": "0",
        "shortLastAmount": "3190712",
        "unrealProfitCalType": "2",
        "longLastAmount": "3190704.2",
        "shortMaxVolume": 10000000000000000,
        "shortLeverage": 25,
        "calMarkedPrice": "4001.45",
        "longMaintenanceMarginRate": "0.0025",
        "wsToken": "fbccde456ddf0b5f6ca9e743d5ba7ed69a58c3feacf8dca8dfaf01f6f0ebc5cb",
        "shortMaxLeverage": 200,
        "marketPriceSlippage": "0",
        "nextFundingRateTimestamp": 1758816000000,
        "longMaintenanceMarginQuickAmount": "0",
        "forbidTrade": false,
        "limitPriceSlippage": "0",
        "defaultPositionType": "2",
        "lastPrice": "4001.31",
        "fundingRate": "0.00008413"
    },
    "message": "成功"
}

# 查询仓位

https://uuapi.rerrkvifj.com/cfd/query/v1.0/Position?ProductGroup=SwapU&Valid=1&pageIndex=1&pageSize=1000

GET

{
    "code": 200,
    "data": {
        "data": [
            {
                "ProductGroup": "SwapU",
                "BusinessNo": "1001748597347805",
                "PositionID": "1000623560990310",
                "BeginTime": "1758807062",
                "TotalCloseProfit": "0.0",
                "PreLongFrozen": "0.0",
                "IsCrossMargin": "1",
                "Remark": "def",
                "LongFrozen": "0.0",
                "Currency": "USDT",
                "Leverage": "25.0",
                "FrozenMargin": "0.0",
                "AvailableUse": "0.0",
                "LongFrozenMargin": "0.0",
                "Position": "0.003",
                "PosiDirection": "2",
                "InsertTime": "1758806564",
                "ShortFrozen": "0.0",
                "ClearCurrency": "USDT",
                "estimateLiquidationPrice": "696.58",
                "OpenPrice": "3993.11",
                "ReserveMode": "0",
                "maintainMarginQuickCalcAmt": "0",
                "TradeFee": "0.0",
                "PriceCurrency": "USDT",
                "AdlLevel": 0,
                "TradeUnitID": "e1b03fb1-6849-464f-a",
                "CloseProfit": "0.0",
                "PositionFee": "0.0",
                "maintainMarginRatio": "0.0025",
                "InstrumentID": "ETHUSDT",
                "DdlnTime": "0",
                "UseMargin": "0.4791732",
                "PreShortFrozen": "0.0",
                "PrePosition": "0.0",
                "UserID": "lbank_exchange_user",
                "SettlementGroup": "SwapU",
                "TotalPositionCost": "11.97933",
                "ShortFrozenMargin": "0.0",
                "liquidationMaintainMarginRatio": "0.003029370513099002",
                "seq": 96782589847,
                "ExchangeID": "Exchange",
                "FORCECLOSEPRICE": "696.58",
                "AccountID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                "seriesNo": 746734939724,
                "MemberID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                "ClosePosition": "0.0",
                "ReserveUse": "0.0",
                "HighestPosition": "0.003",
                "UpdateTime": "1758807085",
                "PositionCost": "11.97933"
            }
        ]
    },
    "message": "成功"
}

# 查询order
https://uuapi.rerrkvifj.com/cfd/query/v1.0/Order?ProductGroup=SwapU&ExchangeID=Exchange&pageIndex=1&pageSize=1000
GET

{
    "code": 200,
    "data": {
        "data": [
            {
                "MinVolume": "0.0",
                "BusinessNo": "1001748607944829",
                "PositionID": "1000623560990310",
                "DeriveSource": "0",
                "BusinessType": "P",
                "IsCrossMargin": "1",
                "OrderType": "0",
                "Currency": "USDT",
                "Turnover": "0.0",
                "Leverage": "25.0",
                "FrozenMargin": "0.312",
                "AvailableUse": "0.0",
                "PosiDirection": "2",
                "InsertTime": "1758807645",
                "Price": "3900.0",
                "Volume": "0.002",
                "VolumeRemain": "0.002",
                "VolumeMode": "1",
                "ReserveMode": "0",
                "TradeUnitID": "e1b03fb1-6849-464f-a",
                "VolumeTraded": "0.0",
                "CloseProfit": "0.0",
                "InstrumentID": "ETHUSDT",
                "Direction": "0",
                "OrderPriceType": "0",
                "OffsetFlag": "0",
                "OrderStatus": "4",
                "FrozenMoney": "0.0",
                "UserID": "lbank_exchange_user",
                "OrderSysID": "1000623569367319",
                "seq": 96820243534,
                "ExchangeID": "Exchange",
                "AccountID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                "seriesNo": 746746071299,
                "FrontNo": "-61",
                "FrozenFee": "0.00468",
                "Fee": "0.0",
                "VolumeCancled": "0.0",
                "MemberID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                "ReserveUse": "0.0",
                "UpdateTime": "1758807645",
                "SessionNo": "131",
                "TimeCondition": "0"
            }
        ]
    },
    "message": "成功"
}



# 查询已经完成order

https://uuapi.rerrkvifj.com/cfd/cff/v1/FinishOrder?ProductGroup=SwapU&pageIndex=1&pageSize=20&startTime=1756310400000&endTime=1758902399999

{
    "code": 200,
    "data": {
        "list": {
            "totalPages": 1,
            "hasNext": false,
            "page": {
                "pageNo": 1,
                "start": 0,
                "pageSize": 20
            },
            "totalCount": 7,
            "resultList": [
                {
                    "ProductGroup": "SwapU",
                    "MinVolume": 0,
                    "BusinessNo": 1001749297328566,
                    "PositionID": "1000623859178785",
                    "Tradable": 1,
                    "DeriveSource": "0",
                    "BusinessType": "P",
                    "IsCrossMargin": 1,
                    "Remark": "def",
                    "OrderType": "0",
                    "Currency": "USDT",
                    "Turnover": 0,
                    "TimeSortNo": 1001173607638696,
                    "Leverage": 25,
                    "FrozenMargin": 0,
                    "AvailableUse": "0",
                    "Priority": 100,
                    "TriggerOrderID": "",
                    "ImplySortNo": 0,
                    "PosiDirection": "2",
                    "InsertTime": 1758848015,
                    "Price": 3800,
                    "Volume": 0.002,
                    "VolumeRemain": 0,
                    "VolumeMode": "1",
                    "ReserveMode": "0",
                    "TradeUnitID": "e1b03fb1-6849-464f-a",
                    "VolumeTraded": 0,
                    "CloseProfit": 0,
                    "LocalID": "e2c6aa732bad45d7b055",
                    "BidPrice1ByInsert": 3914.51,
                    "AskPrice1ByInsert": 3914.52,
                    "InstrumentID": "ETHUSDT",
                    "Direction": "0",
                    "OrderPriceType": "0",
                    "OffsetFlag": "0",
                    "OrderStatus": "6",
                    "BusinessValue": "1758848015793",
                    "FrozenMoney": 0,
                    "UserID": "lbank_exchange_user",
                    "SettlementGroup": "SwapU",
                    "CloseOrderID": "",
                    "OrderSysID": "1000623859178785",
                    "ExchangeID": "Exchange",
                    "BusinessResult": "",
                    "AccountID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                    "APPID": "WEB",
                    "FrontNo": -68,
                    "FrozenFee": 0,
                    "Fee": 0,
                    "ProductID": "",
                    "VolumeCancled": 0.002,
                    "MemberID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                    "ReserveUse": "0",
                    "UpdateTime": 1758848689,
                    "LastPriceByInsert": 3914.51,
                    "SessionNo": 31,
                    "MasterAccountID": "",
                    "TimeCondition": "0",
                    "RelatedOrderSysID": ""
                },
                {
                    "ProductGroup": "SwapU",
                    "MinVolume": 0,
                    "BusinessNo": 1001748597347805,
                    "PositionID": "1000623560990310",
                    "Tradable": 1,
                    "DeriveSource": "0",
                    "BusinessType": "P",
                    "IsCrossMargin": 1,
                    "Remark": "def",
                    "OrderType": "0",
                    "Currency": "USDT",
                    "Turnover": 0,
                    "TimeSortNo": 1001173309756605,
                    "Leverage": 25,
                    "FrozenMargin": 0,
                    "AvailableUse": "0",
                    "Priority": 100,
                    "TriggerOrderID": "",
                    "ImplySortNo": 0,
                    "PosiDirection": "2",
                    "InsertTime": 1758806564,
                    "Price": 3900,
                    "Volume": 0.002,
                    "VolumeRemain": 0,
                    "VolumeMode": "1",
                    "ReserveMode": "0",
                    "TradeUnitID": "e1b03fb1-6849-464f-a",
                    "VolumeTraded": 0,
                    "CloseProfit": 0,
                    "LocalID": "173076ab813244049a79",
                    "BidPrice1ByInsert": 4001.27,
                    "AskPrice1ByInsert": 4001.28,
                    "InstrumentID": "ETHUSDT",
                    "Direction": "0",
                    "OrderPriceType": "0",
                    "OffsetFlag": "0",
                    "OrderStatus": "6",
                    "BusinessValue": "1758806564970",
                    "FrozenMoney": 0,
                    "UserID": "lbank_exchange_user",
                    "SettlementGroup": "SwapU",
                    "CloseOrderID": "",
                    "OrderSysID": "1000623560990310",
                    "ExchangeID": "Exchange",
                    "BusinessResult": "",
                    "AccountID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                    "APPID": "WEB",
                    "FrontNo": -61,
                    "FrozenFee": 0,
                    "Fee": 0,
                    "ProductID": "",
                    "VolumeCancled": 0.002,
                    "MemberID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                    "ReserveUse": "0",
                    "UpdateTime": 1758807085,
                    "LastPriceByInsert": 4001.28,
                    "SessionNo": 132,
                    "MasterAccountID": "",
                    "TimeCondition": "0",
                    "RelatedOrderSysID": ""
                },
                {
                    "ProductGroup": "SwapU",
                    "MinVolume": 0,
                    "BusinessNo": 1001748583265110,
                    "PositionID": "1000623558020554",
                    "Tradable": 1,
                    "DeriveSource": "0",
                    "BusinessType": "P",
                    "IsCrossMargin": 1,
                    "Remark": "def",
                    "OrderType": "0",
                    "Currency": "USDT",
                    "Turnover": 0,
                    "TimeSortNo": 1001173306789092,
                    "Leverage": 100,
                    "FrozenMargin": 0,
                    "AvailableUse": "0",
                    "Priority": 100,
                    "TriggerOrderID": "",
                    "ImplySortNo": 0,
                    "PosiDirection": "2",
                    "InsertTime": 1758806193,
                    "Price": 180,
                    "Volume": 0.05,
                    "VolumeRemain": 0,
                    "VolumeMode": "1",
                    "ReserveMode": "0",
                    "TradeUnitID": "e1b03fb1-6849-464f-a",
                    "VolumeTraded": 0,
                    "CloseProfit": 0,
                    "LocalID": "04f55ebabde94ab980b6",
                    "BidPrice1ByInsert": 199.34,
                    "AskPrice1ByInsert": 199.35,
                    "InstrumentID": "SOLUSDT",
                    "Direction": "0",
                    "OrderPriceType": "0",
                    "OffsetFlag": "0",
                    "OrderStatus": "6",
                    "BusinessValue": "1758806193849",
                    "FrozenMoney": 0,
                    "UserID": "lbank_exchange_user",
                    "SettlementGroup": "SwapU",
                    "CloseOrderID": "",
                    "OrderSysID": "1000623558020554",
                    "ExchangeID": "Exchange",
                    "BusinessResult": "",
                    "AccountID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                    "APPID": "WEB",
                    "FrontNo": -62,
                    "FrozenFee": 0,
                    "Fee": 0,
                    "ProductID": "",
                    "VolumeCancled": 0.05,
                    "MemberID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                    "ReserveUse": "0",
                    "UpdateTime": 1758806302,
                    "LastPriceByInsert": 199.46,
                    "SessionNo": 122,
                    "MasterAccountID": "",
                    "TimeCondition": "0",
                    "RelatedOrderSysID": ""
                }
            ]
        }
    },
    "message": "成功"
}