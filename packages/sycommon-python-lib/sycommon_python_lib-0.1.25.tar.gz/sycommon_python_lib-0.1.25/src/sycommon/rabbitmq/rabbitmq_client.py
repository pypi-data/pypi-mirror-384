import asyncio
import json
from typing import Callable, Coroutine, Optional, Dict, Any, Union, Set
from aio_pika import Message, DeliveryMode, ExchangeType
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractQueue,
    AbstractIncomingMessage,
    ConsumerTag,
)
from aiormq.exceptions import ChannelInvalidStateError, ConnectionClosed

from sycommon.logging.kafka_log import SYLogger
from sycommon.models.mqmsg_model import MQMsgModel
from sycommon.rabbitmq.rabbitmq_pool import RabbitMQConnectionPool

# 最大重试次数限制
MAX_RETRY_COUNT = 3

logger = SYLogger


class RabbitMQClient:
    """
    RabbitMQ客户端（基于连接池），支持集群多节点配置
    提供自动故障转移、连接恢复和消息可靠性保障
    """

    def __init__(
        self,
        connection_pool: RabbitMQConnectionPool,
        exchange_name: str = "system.topic.exchange",
        exchange_type: str = "topic",
        queue_name: Optional[str] = None,
        routing_key: str = "#",
        durable: bool = True,
        auto_delete: bool = False,
        auto_parse_json: bool = True,
        create_if_not_exists: bool = True,
        connection_timeout: int = 10,
        rpc_timeout: int = 10,
        reconnection_delay: int = 1,
        max_reconnection_attempts: int = 5,
        prefetch_count: int = 2,
        consumption_stall_threshold: int = 10
    ):
        """
        初始化RabbitMQ客户端（依赖连接池）

        :param connection_pool: 连接池实例
        """
        # 连接池依赖
        self.connection_pool = connection_pool

        # 交换器和队列参数
        self.exchange_name = exchange_name
        self.exchange_type = ExchangeType(exchange_type)
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.durable = durable
        self.auto_delete = auto_delete

        # 行为控制参数
        self.auto_parse_json = auto_parse_json
        self.create_if_not_exists = create_if_not_exists
        self.connection_timeout = connection_timeout
        self.rpc_timeout = rpc_timeout
        self.prefetch_count = prefetch_count

        # 重连参数
        self.reconnection_delay = reconnection_delay
        self.max_reconnection_attempts = max_reconnection_attempts

        # 消息处理参数
        self.consumption_stall_threshold = consumption_stall_threshold

        # 通道和资源对象（从池获取）
        self.channel: Optional[AbstractChannel] = None
        self.exchange: Optional[AbstractExchange] = None
        self.queue: Optional[AbstractQueue] = None

        # 状态跟踪
        self.actual_queue_name: Optional[str] = None
        self._exchange_exists = False
        self._queue_exists = False
        self._queue_bound = False
        self._is_consuming = False
        self._closed = False
        self._consumer_tag: Optional[ConsumerTag] = None
        self._last_activity_timestamp = asyncio.get_event_loop().time()
        self._last_message_processed = asyncio.get_event_loop().time()

        # 任务和处理器
        self.message_handler: Optional[Callable[
            [Union[Dict[str, Any], str], AbstractIncomingMessage],
            Coroutine[Any, Any, None]
        ]] = None
        self._consuming_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None

        # 消息处理跟踪
        self._processing_message_ids: Set[str] = set()

    @property
    def is_connected(self) -> bool:
        """检查当前通道是否有效"""
        return (not self._closed and
                self.channel is not None and
                not self.channel.is_closed and
                self.exchange is not None)

    def _update_activity_timestamp(self) -> None:
        """更新最后活动时间戳"""
        self._last_activity_timestamp = asyncio.get_event_loop().time()

    def _update_message_processed_timestamp(self) -> None:
        """更新最后消息处理时间戳"""
        self._last_message_processed = asyncio.get_event_loop().time()

    async def _get_channel(self) -> AbstractChannel:
        """从通道池获取通道（使用上下文管理器）"""
        if not self.connection_pool.channel_pool:
            raise Exception("连接池未初始化，请先调用init_pools")

        # 使用async with获取通道，并通过变量返回
        async with self.connection_pool.channel_pool.acquire() as channel:
            return channel

    async def _check_exchange_exists(self, channel: AbstractChannel) -> bool:
        """检查交换机是否存在"""
        try:
            # 使用被动模式检查交换机
            await asyncio.wait_for(
                channel.declare_exchange(
                    name=self.exchange_name,
                    type=self.exchange_type,
                    passive=True
                ),
                timeout=self.rpc_timeout
            )
            return True
        except Exception:
            return False

    async def _check_queue_exists(self, channel: AbstractChannel) -> bool:
        """检查队列是否存在"""
        if not self.queue_name:
            return False
        try:
            # 使用被动模式检查队列
            await asyncio.wait_for(
                channel.declare_queue(
                    name=self.queue_name,
                    passive=True
                ),
                timeout=self.rpc_timeout
            )
            return True
        except Exception:
            return False

    async def _bind_queue(self, channel: AbstractChannel, queue: AbstractQueue, exchange: AbstractExchange) -> bool:
        """将队列绑定到交换机"""
        bind_routing_key = self.routing_key if self.routing_key else '#'

        for attempt in range(MAX_RETRY_COUNT + 1):
            try:
                await asyncio.wait_for(
                    queue.bind(
                        exchange,
                        routing_key=bind_routing_key
                    ),
                    timeout=self.rpc_timeout
                )
                logger.info(
                    f"队列 '{self.queue_name}' 已绑定到交换机 '{self.exchange_name}'，路由键: {bind_routing_key}")
                return True
            except Exception as e:
                logger.warning(
                    f"队列绑定失败（第{attempt+1}次尝试）: {str(e)}")
            if attempt < MAX_RETRY_COUNT:
                await asyncio.sleep(1)
        return False

    async def connect(self, force_reconnect: bool = False, declare_queue: bool = True) -> None:
        """
        从连接池获取资源并初始化（交换机、队列）
        """
        logger.debug(
            f"连接参数 - force_reconnect={force_reconnect}, "
            f"declare_queue={declare_queue}, create_if_not_exists={self.create_if_not_exists}"
        )

        # 如果已连接且不强制重连，则直接返回
        if self.is_connected and not force_reconnect:
            return

        # 取消正在进行的重连任务
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()

        # 重置状态
        self._exchange_exists = False
        self._queue_exists = False
        self._queue_bound = False

        retries = 0
        last_exception = None

        while retries < self.max_reconnection_attempts:
            try:
                # 从池获取通道
                self.channel = await self._get_channel()
                await self.channel.set_qos(prefetch_count=self.prefetch_count)

                # 处理交换机
                exchange_exists = await self._check_exchange_exists(self.channel)
                if not exchange_exists:
                    if self.create_if_not_exists:
                        # 创建交换机
                        self.exchange = await asyncio.wait_for(
                            self.channel.declare_exchange(
                                name=self.exchange_name,
                                type=self.exchange_type,
                                durable=self.durable,
                                auto_delete=self.auto_delete
                            ),
                            timeout=self.rpc_timeout
                        )
                        logger.info(f"已创建交换机 '{self.exchange_name}'")
                    else:
                        raise Exception(
                            f"交换机 '{self.exchange_name}' 不存在且不允许自动创建")
                else:
                    # 获取已有交换机
                    self.exchange = await self.channel.get_exchange(self.exchange_name)
                    logger.info(f"使用已存在的交换机 '{self.exchange_name}'")

                # 处理队列
                if declare_queue and self.queue_name:
                    queue_exists = await self._check_queue_exists(self.channel)

                    if not queue_exists:
                        if not self.create_if_not_exists:
                            raise Exception(
                                f"队列 '{self.queue_name}' 不存在且不允许自动创建")

                        # 创建队列
                        self.queue = await asyncio.wait_for(
                            self.channel.declare_queue(
                                name=self.queue_name,
                                durable=self.durable,
                                auto_delete=self.auto_delete,
                                exclusive=False
                            ),
                            timeout=self.rpc_timeout
                        )
                        self.actual_queue_name = self.queue_name
                        logger.info(f"已创建队列 '{self.queue_name}'")
                    else:
                        # 获取已有队列
                        self.queue = await self.channel.get_queue(self.queue_name)
                        self.actual_queue_name = self.queue_name
                        logger.info(f"使用已存在的队列 '{self.queue_name}'")

                    # 绑定队列到交换机
                    if self.queue and self.exchange:
                        bound = await self._bind_queue(self.channel, self.queue, self.exchange)
                        if not bound:
                            raise Exception(f"队列 '{self.queue_name}' 绑定到交换机失败")
                else:
                    # 不声明队列时的状态处理
                    self.queue = None
                    self.actual_queue_name = None
                    logger.debug(f"跳过队列 '{self.queue_name}' 的声明和绑定")

                # 验证连接状态
                if not self.is_connected:
                    raise Exception("连接验证失败，状态异常")

                # 如果之前在消费，重新开始消费
                if self._is_consuming and self.message_handler:
                    await self.start_consuming()

                # 启动连接监控和保活任务
                self._start_monitoring()
                self._start_keepalive()

                self._update_activity_timestamp()
                logger.info(f"RabbitMQ客户端初始化成功 (队列: {self.actual_queue_name})")
                return

            except Exception as e:
                last_exception = e
                logger.warning(f"资源初始化失败: {str(e)}，重试中...")
                # 释放当前通道（放回池并重新获取）
                self.channel = None
                retries += 1
                if retries < self.max_reconnection_attempts:
                    await asyncio.sleep(self.reconnection_delay)

        logger.error(f"最终初始化失败: {str(last_exception)}")
        raise Exception(
            f"经过{self.max_reconnection_attempts}次重试后仍无法初始化客户端。最后错误: {str(last_exception)}")

    def _start_monitoring(self) -> None:
        """启动连接和消费监控任务"""
        if self._closed or (self._monitor_task and not self._monitor_task.done()):
            return

        async def monitor():
            while not self._closed and self.channel:
                try:
                    # 检查通道状态
                    if self.channel.is_closed:
                        logger.warning("检测到通道已关闭，尝试重建")
                        await self._recreate_channel()
                        continue

                    # 检查消费停滞
                    if self._is_consuming:
                        current_time = asyncio.get_event_loop().time()
                        if current_time - self._last_message_processed > self.consumption_stall_threshold:
                            if self._processing_message_ids:
                                logger.warning(
                                    f"消费停滞，但有 {len(self._processing_message_ids)} 个消息正在处理，暂不重启")
                            else:
                                # 确实无消息处理，再重启
                                await self.stop_consuming()
                                await asyncio.sleep(1)
                                await self.start_consuming()
                except Exception as e:
                    logger.error(f"监控任务出错: {str(e)}")
                    await asyncio.sleep(1)

                await asyncio.sleep(30)

        self._monitor_task = asyncio.create_task(monitor())

    async def _recreate_channel(self) -> None:
        try:
            # 无需手动释放，上下文管理器会自动处理
            self.channel = await self._get_channel()
            await self.channel.set_qos(prefetch_count=self.prefetch_count)

            # 重新获取交换机
            self.exchange = await self.channel.get_exchange(self.exchange_name)

            # 重新绑定队列
            if self.queue_name:
                self.queue = await self.channel.get_queue(self.queue_name)
                if self.queue and self.exchange:
                    await self._bind_queue(self.channel, self.queue, self.exchange)

            # 重新开始消费
            if self._is_consuming and self.message_handler:
                await self.start_consuming()

            logger.info("通道已重建并恢复服务")
            self._update_activity_timestamp()
        except Exception as e:
            logger.error(f"通道重建失败: {str(e)}，触发重连")
            await self.connect(force_reconnect=True)

    def _start_keepalive(self) -> None:
        """启动连接保活任务"""
        if self._closed or (self._keepalive_task and not self._keepalive_task.done()):
            return

        async def keepalive():
            while not self._closed and self.is_connected:
                current_time = asyncio.get_event_loop().time()
                # 检查是否超过指定时间无活动
                if current_time - self._last_activity_timestamp > self.connection_pool.heartbeat * 1.5:
                    logger.debug(
                        f"连接 {self.connection_pool.heartbeat*1.5}s 无活动，执行保活检查")
                    try:
                        if self.channel.is_closed:
                            logger.warning("连接已关闭，触发重连")
                            await self.connect(force_reconnect=True)
                            return

                        # 轻量级操作保持连接活跃
                        await asyncio.wait_for(
                            self.channel.declare_exchange(
                                name=self.exchange_name,
                                type=self.exchange_type,
                                passive=True
                            ),
                            timeout=5
                        )
                        self._update_activity_timestamp()
                    except Exception as e:
                        logger.warning(f"保活检查失败: {str(e)}，触发重连")
                        await self.connect(force_reconnect=True)

                await asyncio.sleep(self.connection_pool.heartbeat / 2)

        self._keepalive_task = asyncio.create_task(keepalive())

    async def _schedule_reconnect(self) -> None:
        """安排重新连接"""
        if self._reconnect_task and not self._reconnect_task.done():
            return

        logger.info(f"将在 {self.reconnection_delay} 秒后尝试重新连接...")

        async def reconnect():
            try:
                await asyncio.sleep(self.reconnection_delay)
                if not self._closed:
                    await self.connect(force_reconnect=True)
            except Exception as e:
                logger.error(f"重连任务失败: {str(e)}")
                if not self._closed:
                    await self._schedule_reconnect()

        self._reconnect_task = asyncio.create_task(reconnect())

    async def close(self) -> None:
        """关闭客户端并释放资源"""
        self._closed = True
        self._is_consuming = False

        # 取消所有任务
        for task in [self._keepalive_task, self._reconnect_task,
                     self._consuming_task, self._monitor_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # 重置状态
        self.channel = None
        self.exchange = None
        self.queue = None
        self._consumer_tag = None
        self._processing_message_ids.clear()

        logger.info("RabbitMQ客户端已关闭")

    async def publish(
        self,
        message_body: Union[str, Dict[str, Any]],
        routing_key: Optional[str] = None,
        content_type: str = "application/json",
        headers: Optional[Dict[str, Any]] = None,
        delivery_mode: DeliveryMode = DeliveryMode.PERSISTENT
    ) -> None:
        """发布消息（从池获取通道，自动重试）"""
        if not self.is_connected:
            logger.warning("连接已关闭，尝试重连后发布消息")
            await self.connect(force_reconnect=True)

        if not self.channel or not self.exchange:
            raise Exception("RabbitMQ连接未初始化")

        # 处理消息体
        if isinstance(message_body, dict):
            message_body_str = json.dumps(message_body, ensure_ascii=False)
            if content_type == "text/plain":
                content_type = "application/json"
        else:
            message_body_str = str(message_body)

        # 创建消息对象
        message = Message(
            body=message_body_str.encode(),
            content_type=content_type,
            headers=headers or {},
            delivery_mode=delivery_mode
        )

        # 发布消息（带重试机制）
        retry_count = 0
        max_retries = 2
        while retry_count < max_retries:
            try:
                # 从池获取新通道用于发布（避免长时间占用消费通道）
                async with self.connection_pool.channel_pool.acquire() as publish_channel:
                    exchange = await publish_channel.get_exchange(self.exchange_name)
                    confirmed = await exchange.publish(
                        message,
                        routing_key=routing_key or self.routing_key or '#',
                        mandatory=True,
                        timeout=5.0
                    )
                    if not confirmed:
                        raise Exception("消息未被服务器确认接收")

                self._update_activity_timestamp()
                logger.debug(f"消息已发布到交换机 '{self.exchange_name}'")
                return
            except (ConnectionClosed, ChannelInvalidStateError):
                retry_count += 1
                logger.warning(f"连接已关闭，尝试重连后重新发布 (重试次数: {retry_count})")
                await self.connect(force_reconnect=True)
            except Exception as e:
                retry_count += 1
                logger.error(f"消息发布失败 (重试次数: {retry_count}): {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(1)

        raise Exception(f"消息发布失败，经过{retry_count}次重试仍未成功")

    # 以下方法（消息消费相关）逻辑与原有保持一致，仅适配连接池
    def set_message_handler(self, handler):
        self.message_handler = handler

    async def start_consuming(self) -> ConsumerTag:
        if self._is_consuming:
            logger.debug("已经在消费中，返回现有consumer_tag")
            if self._consumer_tag:
                return self._consumer_tag
            # 如果_is_consuming为True但无consumer_tag，重置状态并重新启动
            logger.warning("检测到消费状态异常（无consumer_tag），重置状态后重试")
            self._is_consuming = False  # 重置状态

        if not self.is_connected:
            await self.connect()

        if not self.queue:
            raise Exception("队列未初始化，无法开始消费")

        if not self.message_handler:
            raise Exception("未设置消息处理函数")

        self._is_consuming = True
        logger.info(f"开始消费队列: {self.actual_queue_name}")

        try:
            # 调用队列的consume方法，确保获取到consumer_tag
            self._consumer_tag = await self.queue.consume(
                self._message_wrapper,
                no_ack=False  # 手动确认消息
            )

            # 确保consumer_tag有效
            if not self._consumer_tag:
                raise Exception("未能获取到有效的consumer_tag")

            logger.info(
                f"消费者已启动，队列: {self.actual_queue_name}, tag: {self._consumer_tag}")
            return self._consumer_tag
        except Exception as e:
            self._is_consuming = False  # 异常时重置状态
            logger.error(f"启动消费失败: {str(e)}", exc_info=True)
            raise

    async def _safe_cancel_consumer(self) -> bool:
        if not self._consumer_tag or not self.queue or not self.channel:
            return True

        try:
            await asyncio.wait_for(
                self.queue.cancel(self._consumer_tag),
                timeout=self.rpc_timeout
            )
            logger.info(f"消费者 {self._consumer_tag} 已取消")
            return True
        except Exception as e:
            logger.error(f"取消消费者异常: {str(e)}")
            return False

    async def stop_consuming(self) -> None:
        if not self._is_consuming:
            return

        self._is_consuming = False

        if self._consumer_tag and self.queue:
            await self._safe_cancel_consumer()

        # 等待所有正在处理的消息完成
        if self._processing_message_ids:
            logger.info(
                f"等待 {len(self._processing_message_ids)} 个正在处理的消息完成...")
            while self._processing_message_ids and not self._closed:
                await asyncio.sleep(0.1)

        # 清理状态
        self._consumer_tag = None
        self._processing_message_ids.clear()

        logger.info(f"已停止消费队列: {self.actual_queue_name}")

    async def _parse_message(self, message: AbstractIncomingMessage) -> Union[Dict[str, Any], str]:
        try:
            body_str = message.body.decode('utf-8')
            self._update_activity_timestamp()

            if self.auto_parse_json:
                return json.loads(body_str)
            return body_str
        except json.JSONDecodeError:
            logger.warning(f"消息解析JSON失败，返回原始字符串")
            return body_str
        except Exception as e:
            logger.error(f"消息解析出错: {str(e)}")
            return message.body.decode('utf-8')

    async def _message_wrapper(self, message: AbstractIncomingMessage) -> None:
        if not self.message_handler or not self._is_consuming:
            logger.warning("未设置消息处理器或已停止消费")
            # await message.ack()
            return

        message_id = message.message_id or str(id(message))
        if message_id in self._processing_message_ids:
            logger.warning(f"检测到重复处理的消息ID: {message_id}，直接确认")
            await message.ack()
            return

        self._processing_message_ids.add(message_id)

        try:
            logger.debug(f"收到队列 {self.actual_queue_name} 的消息: {message_id}")

            parsed_data = await self._parse_message(message)
            await self.message_handler(MQMsgModel(** parsed_data), message)

            await message.ack()
            self._update_activity_timestamp()
            self._update_message_processed_timestamp()
            logger.debug(f"消息 {message_id} 处理完成并确认")

        except Exception as e:
            current_headers = message.headers or {}
            retry_count = current_headers.get('x-retry-count', 0)
            retry_count += 1

            logger.error(
                f"消息 {message_id} 处理出错（第{retry_count}次重试）: {str(e)}",
                exc_info=True
            )

            if retry_count >= MAX_RETRY_COUNT:
                logger.error(
                    f"消息 {message_id} 已达到最大重试次数({MAX_RETRY_COUNT}次)，标记为失败")
                await message.ack()
                self._update_activity_timestamp()
                return

            new_headers = current_headers.copy()
            new_headers['x-retry-count'] = retry_count

            new_message = Message(
                body=message.body,
                content_type=message.content_type,
                headers=new_headers,
                delivery_mode=message.delivery_mode
            )

            await message.reject(requeue=False)

            if self.exchange:
                await self.exchange.publish(
                    new_message,
                    routing_key=self.routing_key or '#',
                    mandatory=True,
                    timeout=5.0
                )
                self._update_activity_timestamp()
                logger.info(f"消息 {message_id} 已重新发布，当前重试次数: {retry_count}")
        finally:
            if message_id in self._processing_message_ids:
                self._processing_message_ids.remove(message_id)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
