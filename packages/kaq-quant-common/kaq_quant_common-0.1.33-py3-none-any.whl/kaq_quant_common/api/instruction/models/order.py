# 定义model
# 下单请求
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from kaq_quant_common.api.instruction.models import (
    InstructionRequestBase,
    InstructionResponseBase,
)


# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ 下单
# 订单信息
class OrderInfo(BaseModel):
    # 交易对
    symbol: str
    # 现货/合约 'spot' or 'contract'
    spot_contract: str
    # 下单/修改订单 等 'open' or 'close'
    instruction_type: str
    # 保证金，？什么时候用
    margin: Optional[float] = 0.0
    # 补充保证金，？什么时候用
    supply_margin: Optional[float] = 0.0
    # 卖买方向 'buy' or 'sell'
    direction: str
    # 杠杆
    level: int
    # 数量(USDT)
    quantity: float
    # 限价单才用
    target_price: float
    # 当前价格，？什么时候用
    current_price: Optional[float] = 0.0
    # 交易类型 市价单/限价单 'market' or 'limit'
    trade_type: str
    # 风险等级
    risk_level: int
    # 是否强制平仓
    forced_liqu: bool
    # 有效期
    validity_period: Optional[str] = None
    # 策略类型
    strategy_type: Optional[str] = None


# 下单请求
class OrderRequest(InstructionRequestBase):
    orders: list[OrderInfo]


# 下单响应
class OrderResponse(InstructionResponseBase):
    order_id: str


# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ 划转


# 划转类型
class TransferType(Enum):
    # 资金&现货
    FUNDING_SPOT = 1
    # 资金&合约
    FUNDING_FUTURES = 2
    # 合约&现货
    SPOT_FUTURES = 3


# 划转请求
class TransferRequest(InstructionRequestBase):
    # 划转类型
    type: TransferType
    # 资产/币种
    assets: str
    # 划转数量
    amount: float
    # 划转方向 1正向，2反向
    direction: int


# 划转响应
class TransferResponse(InstructionResponseBase):
    transfer_id: str


# 查询合约账户余额请求
class ContractBalanceRequest(InstructionRequestBase):
    # 交易所
    exchange: str
    # 币种
    coin: str


# 查询合约账户余额响应
class ContractBalanceResponse(InstructionResponseBase):
    # 交易所
    exchange: str
    # 币种
    coin: str
    # 余额
    balance: float
