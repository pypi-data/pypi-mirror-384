import io
import os
import time
import inspect
from urllib.parse import urljoin

import aiohttp
from sycommon.logging.kafka_log import SYLogger
from sycommon.synacos.nacos_service import NacosService

"""
支持异步Feign客户端
    方式一: 使用 @feign_client 和 @feign_request 装饰器
    方式二: 使用 feign 函数
"""

# 示例Feign客户端接口
# 1. 定义完整的Feign客户端接口
# @feign_client(service_name="product-service", path_prefix="/api/v2")
# class ProductServiceClient:
#     """商品服务Feign客户端示例，涵盖所有参数类型"""
#
#     # ------------------------------
#     # 场景1: Path参数 + Query参数
#     # 请求示例: GET /products/{product_id}/reviews?status=APPROVED&page=1&size=10
#     # ------------------------------
#     @feign_request("GET", "/products/{product_id}/reviews")
#     async def get_product_reviews(
#         self,
#         product_id: int,  # Path参数 (URL路径中的占位符)
#         status: Optional[str] = None,  # Query参数 (URL查询字符串)
#         page: int = 1,  # Query参数 (默认值)
#         size: int = 10  # Query参数 (默认值)
#     ) -> Dict[str, Any]:
#         """获取商品评价列表"""
#         pass
#
#     # ------------------------------
#     # 场景2: 仅Query参数
#     # 请求示例: GET /products?category=electronics&min_price=100&max_price=500&sort=price_asc
#     # ------------------------------
#     @feign_request("GET", "/products")
#     async def search_products(
#         self,
#         category: str,  # 必选Query参数
#         min_price: Optional[float] = None,  # 可选Query参数
#         max_price: Optional[float] = None,  # 可选Query参数
#         sort: str = "created_desc"  # 带默认值的Query参数
#     ) -> Dict[str, Any]:
#         """搜索商品（仅查询参数）"""
#         pass
#
#     # ------------------------------
#     # 场景3: JSON Body参数 (POST)
#     # 请求示例: POST /products (请求体为JSON)
#     # ------------------------------
#     @feign_request("POST", "/products", headers={"s-y-version": "2.1"})
#     async def create_product(
#         self,
#         product_data: Dict[str, Any]  # JSON请求体
#     ) -> Dict[str, Any]:
#         """创建商品（JSON请求体）"""
#         pass
#
#     # ------------------------------
#     # 场景4: Path参数 + JSON Body (PUT)
#     # 请求示例: PUT /products/{product_id} (请求体为JSON)
#     # ------------------------------
#     @feign_request("PUT", "/products/{product_id}")
#     async def update_product(
#         self,
#         product_id: int,  # Path参数
#         update_data: Dict[str, Any]  # JSON请求体
#     ) -> Dict[str, Any]:
#         """更新商品信息"""
#         pass
#
#     # ------------------------------
#     # 场景5: FormData表单提交 (x-www-form-urlencoded)
#     # 请求示例: POST /products/batch-status (表单字段)
#     # ------------------------------
#     @feign_request(
#         "POST",
#         "/products/batch-status",
#         headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )
#     async def batch_update_status(
#         self,
#         product_ids: str,  # 表单字段 (多个ID用逗号分隔)
#         status: str,  # 表单字段 (目标状态)
#         operator: str  # 表单字段 (操作人)
#     ) -> Dict[str, Any]:
#         """批量更新商品状态（表单提交）"""
#         pass
#
#     # ------------------------------
#     # 场景6: 文件上传 + 表单字段混合
#     # 请求示例: POST /products/{product_id}/images (multipart/form-data)
#     # ------------------------------
#     @feign_upload(field_name="image_file")  # 指定文件表单字段名
#     @feign_request("POST", "/products/{product_id}/images")
#     async def upload_product_image(
#         self,
#         product_id: int,  # Path参数
#         file_path: str,  # 本地文件路径（会被转为文件上传）
#         image_type: str,  # 表单字段（图片类型）
#         is_primary: bool = False,  # 表单字段（是否主图）
#         remark: Optional[str] = None  # 可选表单字段
#     ) -> Dict[str, Any]:
#         """上传商品图片（文件+表单字段）"""
#         pass
#
#     # ------------------------------
#     # 场景7: 多Path参数 + DELETE请求
#     # 请求示例: DELETE /products/{product_id}/skus/{sku_id}
#     # ------------------------------
#     @feign_request("DELETE", "/products/{product_id}/skus/{sku_id}")
#     async def delete_product_sku(
#         self,
#         product_id: int,  # Path参数1
#         sku_id: int  # Path参数2
#     ) -> Dict[str, Any]:
#         """删除商品SKU（多路径参数）"""
#         pass
#
#     # ------------------------------
#     # 场景8: 复杂JSON Body + Query参数
#     # 请求示例: POST /products/filter?include_out_of_stock=false
#     # ------------------------------
#     @feign_request("POST", "/products/filter")
#     async def advanced_filter(
#         self,
#         filter_condition: Dict[str, Any],  # JSON请求体（复杂筛选条件）
#         include_out_of_stock: bool = False,  # Query参数
#         page: int = 1,  # Query参数
#         size: int = 20  # Query参数
#     ) -> Dict[str, Any]:
#         """高级筛选商品（JSON体+查询参数）"""
#         pass
#
#
# # 2. 完整调用示例
# async def feign_complete_demo():
#     # ------------------------------
#     # 调用场景1: Path参数 + Query参数
#     # ------------------------------
#     reviews = await ProductServiceClient().get_product_reviews(
#         product_id=10086,  # Path参数
#         status="APPROVED",  # Query参数
#         page=1,
#         size=20
#     )
#     print(f"场景1 - 商品评价: {reviews.get('total', 0)}条评价")
#
#     # ------------------------------
#     # 调用场景2: 仅Query参数
#     # ------------------------------
#     electronics = await ProductServiceClient().search_products(
#         category="electronics",  # 必选Query
#         min_price=1000,
#         max_price=5000,
#         sort="price_asc"
#     )
#     print(f"场景2 - 搜索结果: {len(electronics.get('items', []))}个商品")
#
#     # ------------------------------
#     # 调用场景3: JSON Body参数 (POST)
#     # ------------------------------
#     new_product = await ProductServiceClient().create_product({
#         "name": "无线蓝牙耳机",
#         "category": "electronics",
#         "price": 299.99,
#         "stock": 500,
#         "attributes": {
#             "brand": "Feign",
#             "battery_life": "24h"
#         }
#     })
#     print(f"场景3 - 新建商品: ID={new_product.get('id')}")
#     product_id = new_product.get('id')  # 用于后续示例
#
#     # ------------------------------
#     # 调用场景4: Path参数 + JSON Body (PUT)
#     # ------------------------------
#     if product_id:
#         updated = await ProductServiceClient().update_product(
#             product_id=product_id,
#             update_data={
#                 "price": 279.99,  # 降价
#                 "stock": 600
#             }
#         )
#         print(f"场景4 - 商品更新: 状态={updated.get('success')}")
#
#     # ------------------------------
#     # 调用场景5: FormData表单提交
#     # ------------------------------
#     batch_result = await ProductServiceClient().batch_update_status(
#         product_ids="1001,1002,1003",  # 多个ID用逗号分隔
#         status="ON_SALE",
#         operator="system"
#     )
#     print(f"场景5 - 批量更新: 成功{batch_result.get('success_count')}个")
#
#     # ------------------------------
#     # 调用场景6: 文件上传 + 表单字段
#     # ------------------------------
#     if product_id:
#         upload_result = await ProductServiceClient().upload_product_image(
#             product_id=product_id,
#             file_path="/tmp/product_main.jpg",  # 本地图片路径
#             image_type="main",
#             is_primary=True,
#             remark="商品主图"
#         )
#         print(f"场景6 - 图片上传: URL={upload_result.get('image_url')}")
#
#     # ------------------------------
#     # 调用场景7: 多Path参数 + DELETE
#     # ------------------------------
#     delete_result = await ProductServiceClient().delete_product_sku(
#         product_id=10086,
#         sku_id=5001
#     )
#     print(f"场景7 - 删除SKU: {delete_result.get('message')}")
#
#     # ------------------------------
#     # 调用场景8: 复杂JSON Body + Query参数
#     # ------------------------------
#     filtered = await ProductServiceClient().advanced_filter(
#         filter_condition={  # 复杂JSON条件
#             "categories": ["electronics", "home"],
#             "price_range": {"min": 500, "max": 3000},
#             "tags": ["new", "promotion"]
#         },
#         include_out_of_stock=False,  # Query参数
#         page=1,
#         size=10
#     )
#     print(f"场景8 - 高级筛选: {filtered.get('total')}个匹配商品")


def feign_client(service_name: str, path_prefix: str = "", default_timeout: float | None = None):
    """Feign客户端装饰器，每次请求后自动关闭会话"""
    def decorator(cls):
        class FeignWrapper:
            def __init__(self):
                self.service_name = service_name
                self.path_prefix = path_prefix
                self.default_timeout = default_timeout
                self.nacos_manager = None  # 延迟初始化Nacos
                self.session = None  # 延迟初始化aiohttp会话

            def __getattr__(self, name):
                """动态获取方法并包装为Feign调用，请求后自动关闭会话"""
                func = getattr(cls, name)

                async def wrapper(*args, **kwargs):
                    # 确保会话初始化
                    if self.session is None:
                        self.session = aiohttp.ClientSession()
                    if self.nacos_manager is None:
                        self.nacos_manager = NacosService(None)

                    try:
                        # 1. 解析参数
                        sig = inspect.signature(func)
                        param_names = list(sig.parameters.keys())
                        try:
                            if param_names and param_names[0] == 'self':
                                bound_args = sig.bind(self, *args, **kwargs)
                            else:
                                bound_args = sig.bind(*args, **kwargs)
                            bound_args.apply_defaults()
                            params = dict(bound_args.arguments)
                            params.pop('self', None)
                            SYLogger.debug(f"解析参数: {params}")
                        except TypeError as e:
                            SYLogger.error(f"参数绑定失败: {str(e)}")
                            raise

                        # 2. 构建请求
                        request_meta = getattr(func, "_feign_meta", {})
                        method = request_meta.get("method", "GET")
                        path = request_meta.get("path", "")
                        headers = request_meta.get("headers", {}).copy()
                        timeout = kwargs.pop('timeout', self.default_timeout)

                        full_path = f"{self.path_prefix}{path}"
                        for param_name, param_value in params.items():
                            if param_value is not None:
                                full_path = full_path.replace(
                                    f"{{{param_name}}}", str(param_value))

                        is_json_request = method.upper() in ["POST", "PUT", "PATCH"] and \
                            not request_meta.get("is_upload", False)
                        if is_json_request and "Content-Type" not in headers:
                            headers["Content-Type"] = "application/json"

                        # 3. 服务发现
                        version = headers.get('s-y-version')
                        instances = self.nacos_manager.get_service_instances(
                            self.service_name, target_version=version)
                        if not instances:
                            raise RuntimeError(
                                f"未找到服务 {self.service_name} 的健康实例")

                        instance = instances[int(time.time()) % len(instances)]
                        base_url = f"http://{instance['ip']}:{instance['port']}"
                        url = urljoin(base_url, full_path)
                        SYLogger.info(f"请求: {method} {url}")

                        # 4. 准备请求参数
                        query_params = {k: v for k, v in params.items()
                                        if f"{{{k}}}" not in path and v is not None}
                        request_data = None
                        files = None

                        if request_meta.get("is_upload", False):
                            files = aiohttp.FormData()
                            file_path = params.get('file_path')
                            if file_path and os.path.exists(file_path):
                                file_field = request_meta.get(
                                    "upload_field", "file")
                                with open(file_path, 'rb') as f:
                                    files.add_field(
                                        file_field,
                                        f.read(),
                                        filename=os.path.basename(file_path)
                                    )
                            for key, value in params.items():
                                if key != 'file_path' and value is not None:
                                    files.add_field(key, str(value))
                            headers.pop('Content-Type', None)
                        elif is_json_request:
                            body_params = [k for k in params if k not in query_params
                                           and f"{{{k}}}" not in path]
                            if body_params:
                                request_data = params[body_params[0]] if len(body_params) == 1 else \
                                    {k: params[k] for k in body_params}

                        # 5. 发送请求并获取响应
                        async with self.session.request(
                            method=method,
                            url=url,
                            headers=headers,
                            params=query_params,
                            json=request_data if not files else None,
                            data=files,
                            timeout=timeout
                        ) as response:
                            return await self._handle_response(response)

                    finally:
                        # 请求完成后自动关闭会话
                        if self.session:
                            await self.session.close()
                            self.session = None  # 重置会话，下次调用重新创建
                            SYLogger.info(
                                f"自动关闭aiohttp会话: {self.service_name}")

                return wrapper

            async def _handle_response(self, response):
                """处理响应结果（保持不变）"""
                status = response.status
                if 200 <= status < 300:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        return await response.read()
                else:
                    error_msg = await response.text()
                    SYLogger.error(f"响应错误: {status} - {error_msg}")
                    raise RuntimeError(f"HTTP {status}: {error_msg}")

        return FeignWrapper
    return decorator


def feign_request(method: str, path: str, headers: dict = None):
    """定义请求元数据的装饰器"""
    def decorator(func):
        func._feign_meta = {
            "method": method.upper(),
            "path": path,
            "headers": headers.copy() if headers else {}
        }
        return func
    return decorator


def feign_upload(field_name: str = "file"):
    """处理文件上传的装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            file_path = kwargs.get('file_path')
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"文件路径不存在: {file_path}")
            with open(file_path, 'rb') as f:
                files = {field_name: (os.path.basename(file_path), f.read())}
                kwargs['files'] = files
                return await func(*args, **kwargs)
        return wrapper
    return decorator


async def feign(service_name, api_path, method='GET', params=None, headers=None, file_path=None,
                path_params=None, body=None, files=None, form_data=None, timeout=None):
    """
    feign 函数，显式设置JSON请求的Content-Type头
    """
    session = aiohttp.ClientSession()
    try:
        # 初始化headers，确保是可修改的字典
        headers = headers.copy() if headers else {}

        # 处理JSON请求的Content-Type
        is_json_request = method.upper() in ["POST", "PUT", "PATCH"] and not (
            files or form_data or file_path)
        if is_json_request and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        nacos_service = NacosService(None)
        version = headers.get('s-y-version')

        # 获取服务实例
        instances = nacos_service.get_service_instances(
            service_name, target_version=version)
        if not instances:
            SYLogger.error(f"nacos:未找到 {service_name} 的健康实例")
            return None

        # 简单轮询负载均衡
        instance = instances[int(time.time()) % len(instances)]

        SYLogger.info(f"nacos:开始调用服务: {service_name}")
        SYLogger.info(f"nacos:请求头: {headers}")

        ip = instance.get('ip')
        port = instance.get('port')

        # 处理path参数
        if path_params:
            for key, value in path_params.items():
                api_path = api_path.replace(f"{{{key}}}", str(value))

        url = f"http://{ip}:{port}{api_path}"
        SYLogger.info(f"nacos:请求地址: {url}")

        try:
            # 处理文件上传
            if files or form_data or file_path:
                data = aiohttp.FormData()
                if form_data:
                    for key, value in form_data.items():
                        data.add_field(key, value)
                if files:
                    for field_name, (filename, content) in files.items():
                        data.add_field(field_name, content, filename=filename)
                if file_path:
                    filename = os.path.basename(file_path)
                    with open(file_path, 'rb') as f:
                        data.add_field('file', f, filename=filename)
                # 移除Content-Type，让aiohttp自动处理
                headers.pop('Content-Type', None)
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=timeout
                ) as response:
                    return await _handle_feign_response(response)
            else:
                # 普通JSON请求
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=body,
                    timeout=timeout
                ) as response:
                    return await _handle_feign_response(response)
        except aiohttp.ClientError as e:
            SYLogger.error(
                f"nacos:请求服务接口时出错ClientError path: {api_path} error:{e}")
            return None
    except Exception as e:
        import traceback
        SYLogger.error(
            f"nacos:请求服务接口时出错 path: {api_path} error:{traceback.format_exc()}")
        return None
    finally:
        await session.close()


async def _handle_feign_response(response):
    """处理Feign请求的响应"""
    if response.status == 200:
        content_type = response.headers.get('Content-Type')
        if 'application/json' in content_type:
            return await response.json()
        else:
            content = await response.read()
            return io.BytesIO(content)
    else:
        error_msg = await response.text()
        SYLogger.error(f"nacos:请求失败，状态码: {response.status}，响应内容: {error_msg}")
        return None
