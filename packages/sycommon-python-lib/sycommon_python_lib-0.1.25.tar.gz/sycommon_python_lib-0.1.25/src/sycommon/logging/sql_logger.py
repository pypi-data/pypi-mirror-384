from sqlalchemy import event
from sqlalchemy.engine import Engine
from sycommon.logging.kafka_log import SYLogger
import time
from datetime import datetime
from decimal import Decimal


class SQLTraceLogger:
    @staticmethod
    def setup_sql_logging(engine: Engine):
        """为 SQLAlchemy 引擎注册事件监听器，绑定 trace_id 到 SQL 日志"""
        def serialize_params(params):
            """处理特殊类型参数的序列化"""
            if isinstance(params, (list, tuple)):
                return [SQLTraceLogger.serialize_params(p) for p in params]
            elif isinstance(params, dict):
                return {k: SQLTraceLogger.serialize_params(v) for k, v in params.items()}
            elif isinstance(params, datetime):
                return params.isoformat()
            elif isinstance(params, Decimal):
                return float(params)
            else:
                return params

        # 监听 SQL 语句执行后事件（计算耗时并输出日志）
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            try:
                # 从连接的 execution_options 中获取开始时间
                start_time = conn._execution_options.get(
                    "_start_time", time.time())
                execution_time = (time.time() - start_time) * 1000

                # 构建 SQL 日志信息
                sql_log = {
                    "type": "SQL",
                    "statement": statement,
                    "parameters": serialize_params(parameters),
                    "execution_time_ms": round(execution_time, 2),
                }

                SYLogger.info(f"SQL 执行: {sql_log}")
            except Exception as e:
                SYLogger.error(f"SQL 日志处理失败: {str(e)}")

        # 监听 SQL 执行开始事件（记录开始时间到连接的 execution_options）
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            try:
                # 通过连接对象的 execution_options 设置开始时间
                # 这里会创建一个新的执行选项副本，避免修改不可变对象
                conn = conn.execution_options(_start_time=time.time())
            except Exception as e:
                SYLogger.error(f"SQL 开始时间记录失败: {str(e)}")
