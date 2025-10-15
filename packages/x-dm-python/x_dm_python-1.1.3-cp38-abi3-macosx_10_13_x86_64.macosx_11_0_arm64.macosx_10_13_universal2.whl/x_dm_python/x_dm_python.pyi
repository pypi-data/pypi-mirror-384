"""
x_dm_python - Twitter DM 批量并发发送库的 Python 类型存根

此文件为 PyCharm/VSCode 等 IDE 提供精确的类型提示
"""
from typing import Optional

__version__: str

class DMResult:
    """
    单条私信发送结果

    Attributes:
        success: 是否发送成功
        user_id: 目标用户ID
        message: 发送的消息内容
        error_msg: 错误信息（成功时为空）
        http_status: HTTP 状态码
        event_id: Twitter 事件ID（成功时返回）
    """
    success: bool
    user_id: str
    message: str
    error_msg: str
    http_status: int
    event_id: Optional[str]

    def __init__(
        self,
        success: bool = False,
        user_id: str = "",
        message: str = "",
        error_msg: str = "",
        http_status: int = 0,
        event_id: Optional[str] = None,
    ) -> None: ...

    def __repr__(self) -> str: ...

class BatchDMResult:
    """
    批量私信发送结果

    Attributes:
        success_count: 成功发送的数量
        failure_count: 失败发送的数量
        results: 每条私信的详细结果
    """
    success_count: int
    failure_count: int
    results: list[DMResult]

    def __init__(
        self,
        success_count: int = 0,
        failure_count: int = 0,
        results: list[DMResult] = [],
    ) -> None: ...

    def __repr__(self) -> str: ...

class Twitter:
    """
    Twitter 客户端

    提供异步的私信发送功能。所有发送方法都是异步的，需要使用 await 调用。

    Example:
        ```python
        import asyncio
        import x_dm_python

        async def main():
            cookies = "ct0=xxx; auth_token=yyy; twid=u%3D123456789"
            client = x_dm_python.Twitter(cookies)

            # 发送单条私信
            result = await client.send_direct_message("123456789", "Hello!")
            print(f"成功: {result.success}")

            # 批量发送
            user_ids = ["123456789", "987654321"]
            batch_result = await client.send_batch_direct_messages(user_ids, "Hello everyone!")
            print(f"成功: {batch_result.success_count}, 失败: {batch_result.failure_count}")

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        cookies: str,
        proxy_url: Optional[str] = None,
        _logger_name: str = "twitter_dm",
    ) -> None:
        """
        创建 Twitter 客户端

        Args:
            cookies: Twitter 账号的 cookies 字符串，必须包含 ct0, auth_token, twid
            proxy_url: 可选的代理服务器 URL (格式: http://host:port 或 socks5://host:port)
            _logger_name: 日志记录器名称（保留参数，供兼容使用）

        Raises:
            RuntimeError: 当 cookies 格式无效或缺少必需字段时

        Example:
            ```python
            cookies = "ct0=abc123; auth_token=xyz789; twid=u%3D123456789"
            client = x_dm_python.Twitter(cookies)

            # 使用代理
            client_with_proxy = x_dm_python.Twitter(
                cookies,
                proxy_url="http://127.0.0.1:7890"
            )
            ```
        """
        ...

    async def send_direct_message(
        self,
        user_id: str,
        message: str,
        media_id: Optional[str] = None,
    ) -> DMResult:
        """
        发送单条私信（异步方法）

        Args:
            user_id: 目标用户ID（纯数字字符串）
            message: 消息内容（最大 10000 字符）
            media_id: 可选的媒体ID（来自 upload_image 返回的 media_id_string）

        Returns:
            DMResult: 发送结果，包含成功状态、错误信息等

        Raises:
            RuntimeError: 当发送失败时（网络错误、认证失败等）

        Example:
            ```python
            # 不带图片
            result = await client.send_direct_message("123456789", "你好！")

            # 带图片
            upload_result = await client.upload_image(image_bytes, "dm_image")
            result = await client.send_direct_message(
                "123456789",
                "看这张图片！",
                media_id=upload_result.media_id_string
            )

            if result.success:
                print(f"发送成功，事件ID: {result.event_id}")
            else:
                print(f"发送失败: {result.error_msg}")
            ```
        """
        ...

    async def send_batch_direct_messages(
        self,
        user_ids: list[str],
        message: str,
        client_transaction_ids: Optional[list[str]] = None,
        media_ids: Optional[list[Optional[str]]] = None,
    ) -> BatchDMResult:
        """
        批量发送私信（异步方法，并发执行）

        同时向多个用户发送相同的消息，使用并发执行提高效率。

        Args:
            user_ids: 目标用户ID列表（纯数字字符串）
            message: 消息内容（最大 10000 字符）
            client_transaction_ids: 可选的客户端事务ID列表（用于去重）
            media_ids: 可选的媒体ID列表（长度必须与 user_ids 一致，可包含 None）

        Returns:
            BatchDMResult: 批量发送结果，包含成功/失败数量和每条消息的详细结果

        Raises:
            RuntimeError: 当批量发送失败时

        Example:
            ```python
            # 不带图片的批量发送
            user_ids = ["123456789", "987654321", "555666777"]
            result = await client.send_batch_direct_messages(user_ids, "群发消息")

            # 带图片的批量发送（每个用户不同图片）
            batch_upload = await client.upload_image_multiple_times(
                image_bytes, "dm_image", 3
            )
            result = await client.send_batch_direct_messages(
                user_ids,
                "看这张图片！",
                media_ids=batch_upload.media_ids
            )

            print(f"成功: {result.success_count}, 失败: {result.failure_count}")
            for dm_result in result.results:
                if not dm_result.success:
                    print(f"用户 {dm_result.user_id} 发送失败: {dm_result.error_msg}")
            ```
        """
        ...

    def get_cookies(self) -> str:
        """
        获取当前 cookies 字符串

        Returns:
            str: 完整的 cookies 字符串

        Example:
            ```python
            cookies = client.get_cookies()
            print(cookies)
            ```
        """
        ...

    def validate_cookies(self) -> bool:
        """
        验证 cookies 是否有效

        检查 cookies 是否包含必需的认证信息（ct0, auth_token, user_id）

        Returns:
            bool: True 表示 cookies 有效，False 表示无效

        Example:
            ```python
            if client.validate_cookies():
                print("Cookies 有效")
            else:
                print("Cookies 无效或已过期")
            ```
        """
        ...

    async def upload_image(
        self,
        image_bytes: bytes,
        media_category: str,
    ) -> "UploadResult":
        """
        上传图片（异步方法）

        Args:
            image_bytes: 图片二进制数据（bytes）
            media_category: 媒体类别，可选值: "tweet_image", "dm_image", "banner_image"

        Returns:
            UploadResult: 上传结果，包含 media_id 和错误信息

        Raises:
            RuntimeError: 当上传失败时（网络错误、文件格式错误等）

        Example:
            ```python
            # 读取图片
            with open("image.jpg", "rb") as f:
                image_bytes = f.read()

            # 上传为私信图片
            result = await client.upload_image(image_bytes, "dm_image")

            if result.success:
                print(f"上传成功！media_id: {result.media_id_string}")
                # 使用 media_id 发送私信
                dm_result = await client.send_direct_message(
                    "123456789",
                    "看这张图片！",
                    media_id=result.media_id_string
                )
            else:
                print(f"上传失败: {result.error_msg}")
            ```
        """
        ...

    async def upload_image_multiple_times(
        self,
        image_bytes: bytes,
        media_category: str,
        count: int,
    ) -> "BatchUploadResult":
        """
        批量上传同一张图片多次（异步方法）

        通过添加随机扰动，每次上传获取独立的 media_id。
        适用于向多个用户发送"同一张"图片但需要不同 media_id 的场景。

        Args:
            image_bytes: 图片二进制数据（bytes）
            media_category: 媒体类别，可选值: "tweet_image", "dm_image", "banner_image"
            count: 上传次数（必须 > 0）

        Returns:
            BatchUploadResult: 批量上传结果，包含所有 media_id 和详细结果

        Raises:
            RuntimeError: 当批量上传失败时

        Example:
            ```python
            # 读取图片
            with open("image.jpg", "rb") as f:
                image_bytes = f.read()

            # 批量上传 5 次获取 5 个不同的 media_id
            result = await client.upload_image_multiple_times(
                image_bytes,
                "dm_image",
                5
            )

            print(f"成功上传: {result.success_count}/{5}")
            print(f"Media IDs: {result.media_ids}")

            # 使用这些 media_ids 发送批量私信
            user_ids = ["123", "456", "789", "012", "345"]
            dm_result = await client.send_batch_direct_messages(
                user_ids,
                "看这张图片！",
                media_ids=result.media_ids
            )
            ```
        """
        ...

class UploadResult:
    """
    单次图片上传结果

    Attributes:
        success: 是否上传成功
        media_id: 数字格式的媒体ID（可能为 None）
        media_id_string: 字符串格式的媒体ID（推荐使用）
        error_msg: 错误信息（成功时为空）
    """
    success: bool
    media_id: Optional[int]
    media_id_string: Optional[str]
    error_msg: str

    def __init__(
        self,
        success: bool = False,
        media_id: Optional[int] = None,
        media_id_string: Optional[str] = None,
        error_msg: str = "",
    ) -> None: ...

    def __repr__(self) -> str: ...

class BatchUploadResult:
    """
    批量图片上传结果

    Attributes:
        success_count: 成功上传的数量
        failure_count: 失败上传的数量
        media_ids: 成功上传的 media_id 列表（字符串格式）
        results: 每次上传的详细结果
    """
    success_count: int
    failure_count: int
    media_ids: list[str]
    results: list[UploadResult]

    def __init__(
        self,
        success_count: int = 0,
        failure_count: int = 0,
        media_ids: list[str] = [],
        results: list[UploadResult] = [],
    ) -> None: ...

    def __repr__(self) -> str: ...
