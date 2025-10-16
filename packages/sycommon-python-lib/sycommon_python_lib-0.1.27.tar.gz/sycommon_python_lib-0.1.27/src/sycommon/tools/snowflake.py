import uuid


class Snowflake:
    """基于UUID生成兼容Java long类型的唯一ID"""
    _MAX_JAVA_LONG = 9223372036854775807  # Java long最大值（18位）

    @staticmethod
    def next_id() -> str:
        """生成不超过Java long最大值的唯一ID字符串（18位以内）"""
        while True:
            # 生成UUID并转换为整数
            uuid_int = int(uuid.uuid4().hex, 16)

            # 取低63位，并强制限制不超过Java long最大值
            id_num = uuid_int & ((1 << 63) - 1)  # 取低63位
            id_num = min(id_num, Snowflake._MAX_JAVA_LONG)  # 强制限制最大值

            # 转换为字符串并验证长度（确保18位以内）
            id_str = str(id_num)
            if len(id_str) <= 18:
                return id_str


# 使用示例
if __name__ == "__main__":
    # 生成1000个ID并验证
    for _ in range(1000):
        id_str = Snowflake.next_id()
        id_num = int(id_str)
        print(f"ID: {id_str} (长度: {len(id_str)})")
        assert len(id_str) <= 18, f"ID长度超过18位: {id_str}"
        assert id_num <= Snowflake._MAX_JAVA_LONG, f"ID超过Java long最大值: {id_num}"
