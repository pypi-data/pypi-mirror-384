# 定义 服务器api
from abc import abstractmethod

from kaq_quant_common.api.api_interface import ApiInterface, api_method
from kaq_quant_common.api.api_server_base import ApiServerBase
from kaq_quant_common.api.instruction.models.order import (
    OrderRequest,
    OrderResponse,
    TransferRequest,
    TransferResponse,
)


class InstructionServerBase(ApiServerBase, ApiInterface):

    def __init__(self, host='0.0.0.0', port=5000):
        super().__init__(self, host, port)

    # 下单
    @api_method(OrderRequest, OrderResponse)
    def order(self, request: OrderRequest) -> OrderResponse:
        return self._on_order(request)

    @abstractmethod
    def _on_order(self, request: OrderRequest) -> OrderResponse:
        """
        下单
        """
        pass

    # 划转
    @api_method(TransferRequest, TransferResponse)
    def transfer(self, request: TransferRequest) -> TransferResponse:
        return self._on_transfer(request)

    @abstractmethod
    def _on_transfer(self, request: TransferRequest) -> TransferResponse:
        """
        划转
        """
        pass
