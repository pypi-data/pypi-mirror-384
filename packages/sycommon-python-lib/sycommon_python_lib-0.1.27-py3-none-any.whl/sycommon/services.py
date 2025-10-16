import asyncio
import logging
import yaml
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, applications
from pydantic import BaseModel
from typing import Any, Callable, Dict, List, Tuple, Union, Optional, AsyncGenerator
from sycommon.config.Config import SingletonMeta
from sycommon.models.mqlistener_config import RabbitMQListenerConfig
from sycommon.models.mqsend_config import RabbitMQSendConfig
from sycommon.rabbitmq.rabbitmq_service import RabbitMQService
from sycommon.tools.docs import custom_redoc_html, custom_swagger_ui_html


class Services(metaclass=SingletonMeta):
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _config: Optional[dict] = None
    _initialized: bool = False
    _registered_senders: List[str] = []
    _mq_tasks: List[asyncio.Task] = []
    _instance: Optional['Services'] = None
    _app: Optional[FastAPI] = None
    _user_lifespan: Optional[Callable] = None

    def __init__(self, config: dict, app: FastAPI):
        if not Services._config:
            Services._config = config
        Services._instance = self
        Services._app = app
        self._init_event_loop()

    def _init_event_loop(self):
        """初始化事件循环，确保全局只有一个循环实例"""
        if not Services._loop:
            try:
                Services._loop = asyncio.get_running_loop()
            except RuntimeError:
                Services._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(Services._loop)

    @classmethod
    def plugins(
        cls,
        app: FastAPI,
        config: Optional[dict] = None,
        middleware: Optional[Callable[[FastAPI, dict], None]] = None,
        nacos_service: Optional[Callable[[dict], None]] = None,
        logging_service: Optional[Callable[[dict], None]] = None,
        database_service: Optional[Union[
            Tuple[Callable[[dict, str], None], str],
            List[Tuple[Callable[[dict, str], None], str]]
        ]] = None,
        rabbitmq_listeners: Optional[List[RabbitMQListenerConfig]] = None,
        rabbitmq_senders: Optional[List[RabbitMQSendConfig]] = None
    ) -> FastAPI:
        load_dotenv()
        # 保存应用实例和配置
        cls._app = app
        cls._config = config
        cls._user_lifespan = app.router.lifespan_context
        # 设置文档
        applications.get_swagger_ui_html = custom_swagger_ui_html
        applications.get_redoc_html = custom_redoc_html
        # 设置app.state host, port
        if not cls._config:
            config = yaml.safe_load(open('app.yaml', 'r', encoding='utf-8'))
            cls._config = config
        app.host = cls._config.get('Host')
        app.post = cls._config.get('Port')

        # 立即配置非异步服务（在应用启动前）
        if middleware:
            middleware(app, config)

        if nacos_service:
            nacos_service(config)

        if logging_service:
            logging_service(config)

        if database_service:
            cls._setup_database_static(database_service, config)

        # 创建组合生命周期管理器
        @asynccontextmanager
        async def combined_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            # 1. 执行Services自身的初始化
            instance = cls(config, app)
            has_listeners = bool(
                rabbitmq_listeners and len(rabbitmq_listeners) > 0)
            has_senders = bool(rabbitmq_senders and len(rabbitmq_senders) > 0)

            try:
                await instance._setup_mq_async(
                    rabbitmq_listeners=rabbitmq_listeners,
                    rabbitmq_senders=rabbitmq_senders,
                    has_listeners=has_listeners,
                    has_senders=has_senders
                )
                cls._initialized = True
                logging.info("Services初始化完成")
            except Exception as e:
                logging.error(f"Services初始化失败: {str(e)}", exc_info=True)
                raise

            app.state.services = instance

            # 2. 执行用户定义的生命周期
            if cls._user_lifespan:
                async with cls._user_lifespan(app):
                    yield  # 应用运行阶段
            else:
                yield  # 没有用户生命周期时直接 yield

            # 3. 执行Services的关闭逻辑
            await cls.shutdown()
            logging.info("Services已关闭")

        # 设置组合生命周期
        app.router.lifespan_context = combined_lifespan

        return app

    @staticmethod
    def _setup_database_static(database_service, config):
        """静态方法：设置数据库服务"""
        if isinstance(database_service, tuple):
            db_setup, db_name = database_service
            db_setup(config, db_name)
        elif isinstance(database_service, list):
            for db_setup, db_name in database_service:
                db_setup(config, db_name)

    async def _setup_mq_async(
        self,
        rabbitmq_listeners: Optional[List[RabbitMQListenerConfig]] = None,
        rabbitmq_senders: Optional[List[RabbitMQSendConfig]] = None,
        has_listeners: bool = False,
        has_senders: bool = False,
    ):
        """异步设置MQ相关服务"""
        # 初始化RabbitMQ服务，传递状态
        RabbitMQService.init(self._config, has_listeners, has_senders)

        # 设置发送器，传递是否有监听器的标志
        if rabbitmq_senders:
            await self._setup_senders_async(rabbitmq_senders, has_listeners)

        # 设置监听器，传递是否有发送器的标志
        if rabbitmq_listeners:
            await self._setup_listeners_async(rabbitmq_listeners, has_senders)

        # 验证初始化结果
        if has_listeners:
            listener_count = len(RabbitMQService._clients)
            logging.info(f"监听器初始化完成，共启动 {listener_count} 个消费者")
            if listener_count == 0:
                logging.warning("未成功初始化任何监听器，请检查配置")

    async def _setup_senders_async(self, rabbitmq_senders, has_listeners: bool):
        Services._registered_senders = [
            sender.queue_name for sender in rabbitmq_senders]

        # 将是否有监听器的信息传递给RabbitMQService
        await RabbitMQService.setup_senders(rabbitmq_senders, has_listeners)
        logging.info(f"已注册的RabbitMQ发送器: {Services._registered_senders}")

    async def _setup_listeners_async(self, rabbitmq_listeners, has_senders: bool):
        await RabbitMQService.setup_listeners(rabbitmq_listeners, has_senders)

    @classmethod
    async def send_message(
        cls,
        queue_name: str,
        data: Union[str, Dict[str, Any], BaseModel, None],
        max_retries: int = 3,
        retry_delay: float = 1.0, **kwargs
    ) -> None:
        """发送消息，添加重试机制"""
        if not cls._initialized or not cls._loop:
            logging.error("Services not properly initialized!")
            raise ValueError("服务未正确初始化")

        for attempt in range(max_retries):
            try:
                if queue_name not in cls._registered_senders:
                    cls._registered_senders = RabbitMQService._sender_client_names
                    if queue_name not in cls._registered_senders:
                        raise ValueError(f"发送器 {queue_name} 未注册")

                sender = RabbitMQService.get_sender(queue_name)
                if not sender:
                    raise ValueError(f"发送器 '{queue_name}' 不存在")

                await RabbitMQService.send_message(data, queue_name, ** kwargs)
                logging.info(f"消息发送成功（尝试 {attempt+1}/{max_retries}）")
                return

            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(
                        f"消息发送失败（已尝试 {max_retries} 次）: {str(e)}", exc_info=True)
                    raise

                logging.warning(
                    f"消息发送失败（尝试 {attempt+1}/{max_retries}）: {str(e)}，"
                    f"{retry_delay}秒后重试..."
                )
                await asyncio.sleep(retry_delay)

    @staticmethod
    async def shutdown():
        """关闭所有服务"""
        # 取消所有MQ任务
        for task in Services._mq_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # 关闭RabbitMQ服务
        await RabbitMQService.shutdown()
