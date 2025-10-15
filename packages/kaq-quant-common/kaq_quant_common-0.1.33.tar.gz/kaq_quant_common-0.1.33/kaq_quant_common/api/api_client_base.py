import requests
from pydantic import BaseModel
from typing import Type, TypeVar
from kaq_quant_common.utils import logger_utils

R = TypeVar('R', bound=BaseModel)

class ApiClientBase:
    """
    api 客户端
    """
    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip('/')
        self._logger = logger_utils.get_logger(self)

    # 发送请求
    def _make_request(self, method_name: str, request_data: BaseModel, response_model: Type[R]) -> R:
        url = f"{self._base_url}/api/{method_name}"
        try:
            # 发送post请求
            response = requests.post(url, json=request_data.model_dump())
            # 如果不成功则抛出异常
            response.raise_for_status()
            # 返回请求结果
            return response_model(**response.json())
        except requests.exceptions.RequestException as e:
            self._logger.error(f"An error occurred: {e}")
            raise