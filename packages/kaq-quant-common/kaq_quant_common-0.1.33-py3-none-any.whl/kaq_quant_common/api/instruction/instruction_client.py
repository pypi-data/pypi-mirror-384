# 定义 客户端
from kaq_quant_common.api.api_client_base import ApiClientBase
from kaq_quant_common.api.instruction.models.order import (
    OrderRequest,
    OrderResponse,
    TransferRequest,
    TransferResponse,
)


class InstructionClient(ApiClientBase):

    # 下单
    def order(self, request: OrderRequest) -> OrderResponse:
        return self._make_request('order', request, OrderResponse)

    # 划转
    def transfer(self, request: TransferRequest) -> TransferResponse:
        return self._make_request('transfer', request, TransferResponse)
