import inspect
import signal
import threading
import time

from flask import Flask, jsonify, request
from kaq_quant_common.utils import logger_utils
from werkzeug.serving import make_server

from .api_interface import ApiInterface


class ApiServerBase:
    """
    API服务器基类，用于动态发现和分派API方法。
    """

    def __init__(self, api: ApiInterface, host='0.0.0.0', port=5000):
        """
        初始化API服务器。

        :param api: 实现了ApiInterface的API实例。
        :param host: 服务器主机地址。
        :param port: 服务器端口。
        """
        self._app = Flask(__name__)
        self._api = api
        self._host = host
        self._port = port
        self._server = make_server(self._host, self._port, self._app)
        self._api_methods = self._discover_api_methods()
        self._logger = logger_utils.get_logger(self)

        @self._app.route('/api/<method_name>', methods=['POST'])
        def handle_request(method_name: str):
            """
            处理API请求。
            """
            if method_name not in self._api_methods:
                return jsonify({"error": f"Method '{method_name}' not found"}), 404

            method, request_model, response_model = self._api_methods[method_name]

            try:
                # 使用请求模型验证和解析JSON数据
                request_data = request_model(**request.json)
                # 调用API方法
                response_data = method(request_data)
                # 验证响应类型
                if not isinstance(response_data, response_model):
                    return jsonify({"error": "Invalid response type from method"}), 500
                # 返回JSON响应
                return jsonify(response_data.model_dump())
            except Exception as e:
                # 捕获请求处理过程中的异常
                return jsonify({"error": str(e)}), 400

    def _discover_api_methods(self):
        """
        发现并注册所有使用@api_method装饰器标记的API方法。
        """
        methods = {}
        for name, func in inspect.getmembers(self._api, predicate=inspect.ismethod):
            if hasattr(func, '_is_api_method') and func._is_api_method:
                methods[name] = (func, func._request_model, func._response_model)
        return methods

    def run(self):
        """
        启动API服务器。
        """
        self._logger.info(f"Starting server on {self._host}:{self._port}")
        self._server.serve_forever()

    def shutdown(self):
        """
        关闭API服务器。
        """
        self._logger.info(f"Shutting down server on {self._host}:{self._port}")
        self._server.shutdown()

    def run_with_thread(self, block=True):
        """
        启动API服务器在一个新线程中。
        """
        self._server_thread = threading.Thread(target=self.run)
        self._server_thread.name = "ApiServerThread"
        self._server_thread.daemon = True
        self._server_thread.start()
        time.sleep(1)

        if block:
            self.wait_for_termination()

    #
    def wait_for_termination(self):
        # 全局退出事件，用于传递终止信号
        exit_event = threading.Event()

        def handle_terminate_signal(signum, frame=None):
            """信号处理函数：捕获终止信号并触发退出事件"""
            self._logger.info(f"收到终止信号 {signum}")
            exit_event.set()
            # 优雅地停止服务器
            self.shutdown()

        # 监听信号
        # SIGTERM：Dagster通常发送此信号进行终止
        # SIGINT：对应Ctrl+C，用于本地测试
        signal.signal(signal.SIGTERM, handle_terminate_signal)
        signal.signal(signal.SIGINT, handle_terminate_signal)

        # 监听退出事件
        while not exit_event.is_set():
            time.sleep(1)

        self._logger.warning("ApiServer 线程退出")
