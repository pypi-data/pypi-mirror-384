from typing import Optional, List
from aio_pika import connect_robust, Channel
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool

from sycommon.logging.kafka_log import SYLogger

logger = SYLogger


class RabbitMQConnectionPool:
    """RabbitMQ连接池管理，负责创建和管理连接池与通道池"""

    def __init__(
        self,
        hosts: List[str],
        port: int,
        username: str,
        password: str,
        virtualhost: str = "/",
        connection_pool_size: int = 2,
        channel_pool_size: int = 10,
        heartbeat: int = 10,
        app_name: str = ""
    ):
        self.hosts = [host.strip() for host in hosts if host.strip()]
        if not self.hosts:
            raise ValueError("至少需要提供一个RabbitMQ主机地址")
        self.port = port
        self.username = username
        self.password = password
        self.virtualhost = virtualhost
        self.app_name = app_name or "rabbitmq-client"
        self.heartbeat = heartbeat

        # 连接池和通道池
        self.connection_pool: Optional[Pool] = None
        self.channel_pool: Optional[Pool] = None
        self.connection_pool_size = connection_pool_size
        self.channel_pool_size = channel_pool_size

    async def init_pools(self):
        """初始化连接池和通道池"""
        # 连接创建函数（支持集群节点轮询）
        async def create_connection() -> AbstractRobustConnection:
            # 轮询选择主机（简单负载均衡）
            hosts = self.hosts.copy()
            while hosts:
                host = hosts.pop(0)
                try:
                    return await connect_robust(
                        host=host,
                        port=self.port,
                        login=self.username,
                        password=self.password,
                        virtualhost=self.virtualhost,
                        heartbeat=self.heartbeat,
                        client_properties={
                            "connection_name": f"{self.app_name}@{host}"
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"连接主机 {host}:{self.port} 失败，尝试下一个节点: {str(e)}")
                    if not hosts:
                        raise  # 所有节点都失败时抛出异常

        # 初始化连接池
        self.connection_pool = Pool(
            create_connection,
            max_size=self.connection_pool_size
        )

        # 通道创建函数
        async def create_channel() -> Channel:
            async with self.connection_pool.acquire() as connection:
                channel = await connection.channel()
                return channel

        # 初始化通道池
        self.channel_pool = Pool(
            create_channel,
            max_size=self.channel_pool_size
        )

        logger.info(
            f"RabbitMQ连接池初始化完成 - 连接池大小: {self.connection_pool_size}, "
            f"通道池大小: {self.channel_pool_size}, 集群节点: {self.hosts}"
        )

    async def close(self):
        """关闭连接池和通道池"""
        if self.channel_pool:
            await self.channel_pool.close()
        if self.connection_pool:
            await self.connection_pool.close()
        logger.info("RabbitMQ连接池已关闭")

    async def __aenter__(self):
        await self.init_pools()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
