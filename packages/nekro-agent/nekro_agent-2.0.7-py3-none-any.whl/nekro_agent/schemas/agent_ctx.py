from types import ModuleType
from typing import TYPE_CHECKING, Any, Dict, Optional

from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
from pydantic import BaseModel, Field

from nekro_agent.adapters.utils import adapter_utils
from nekro_agent.core.config import CoreConfig, config
from nekro_agent.models.db_preset import DBPreset
from nekro_agent.tools.file_utils import FileSystem

if TYPE_CHECKING:
    from nekro_agent.adapters.interface import BaseAdapter
    from nekro_agent.models.db_chat_channel import DBChatChannel
    from nekro_agent.models.db_user import DBUser


class WebhookRequest(BaseModel):
    """Webhook 请求模型，用于封装传入的 Webhook 数据。"""

    headers: Dict[str, str] = Field(..., description="Webhook 请求头")
    body: Dict[str, Any] = Field(..., description="Webhook 请求体")


class AgentCtx(BaseModel):
    """
    Agent 上下文（AgentCtx）

    `AgentCtx` 是 Nekro Agent 中一个至关重要的概念，它封装了 Agent 在执行任务时所需的所有上下文信息。
    无论是在处理来自聊天软件的消息，还是响应一个 Webhook 事件，`AgentCtx` 都提供了统一的接口来访问相关数据和功能。

    插件开发者可以通过 `AgentCtx` 对象安全地与 Nekro Agent 的核心功能进行交互，
    例如读写文件、获取配置等，而无需关心底层的具体实现。

    在插件实践中通常以 `_ctx` 作为变量名提供给插件扩展方法使用。
    """

    container_key: Optional[str] = Field(default=None, description="沙盒容器的唯一标识，用于隔离不同聊天频道的运行环境。")
    from_chat_key: Optional[str] = Field(default=None, description="来源聊天的唯一标识，用于追溯消息来源。")
    webhook_request: Optional[WebhookRequest] = Field(
        default=None,
        description="当 Agent 由 Webhook 触发时，这里会包含 Webhook 的请求数据。",
    )
    channel_id: Optional[str] = Field(default=None, description="当前聊天频道的频道 ID，例如 QQ 群号或 用户 ID 等。")
    channel_name: Optional[str] = Field(default=None, description="当前聊天频道的频道名称，例如 QQ 群名或 用户名等。")
    channel_type: Optional[str] = Field(default=None, description="当前聊天频道的频道类型，例如 `group` 或 `private` 等。")
    adapter_key: Optional[str] = Field(default=None, description="当前聊天频道所使用的适配器标识，例如 `onebot_v11` 等。")
    _db_chat_channel: Optional["DBChatChannel"] = None  # 当前聊天频道的数据库聊天频道实例
    _trigger_db_user: Optional["DBUser"] = None  # 触发本次 Agent 的 DBUser 实例

    @property
    def chat_key(self) -> str:
        """
        聊天频道唯一ID。

        这是当前聊天频道的唯一标识符，通常由 `adapter_key` 和 `channel_id` 组成。

        Example:
            >>> _ctx.chat_key
            'onebot_v11-group_12345678'
        """
        if not self.from_chat_key:
            raise ValueError("missing from_chat_key")
        return self.from_chat_key

    @property
    def db_chat_channel(self) -> Optional["DBChatChannel"]:
        """
        当前聊天频道的数据库聊天频道实例。
        """
        return self._db_chat_channel

    @property
    def db_user(self) -> Optional["DBUser"]:
        """
        触发本次 Agent 的数据库用户实例。
        """
        return self._trigger_db_user

    @property
    def adapter(self) -> "BaseAdapter":
        """
        消息关联适配器实例。

        通过此适配器实例，插件可以获取适配器相关信息或调用适配器相关方法。
        """
        if not self.adapter_key:
            raise ValueError("missing adapter_key")
        return adapter_utils.get_adapter(self.adapter_key)

    @property
    def fs(self) -> FileSystem:
        """文件系统工具

        用于在插件和 AI 之间安全地传递文件。

        - `mixed_forward_file`: **插件 -> AI**。当插件需要生成一个文件（如图、文档）并返回给 AI 时使用。
          它接收 URL、bytes 等多种格式，自动处理后返回一个 AI 可用的沙盒路径。
        - `get_file`: **AI -> 插件**。当 AI 调用插件并传入一个沙盒文件路径作为参数时，插件使用此方法
          将该路径转换为宿主机上可读写的绝对路径。

        Example:
            >>> # 案例 1: 插件生成文件并返回给 AI (参考 `draw.py`)
            >>> #
            >>> # 插件通过 API 获取了一张图片
            >>> image_url = "https://nekro-agent-dev.oss-cn-beijing.aliyuncs.com/images/NA_logo.png"
            >>> # `mixed_forward_file` 将其转换为 AI 可用的沙盒路径
            >>> sandbox_path = await _ctx.fs.mixed_forward_file(image_url, file_name="logo.png")
            >>> logger.info(sandbox_path)
            /app/uploads/logo.png
            >>> # 插件函数可以直接 `return sandbox_path`，AI 就能接收到这个文件。
            ...
            >>> # ---
            ...
            >>> # 案例 2: AI 提供文件给插件处理
            >>> # 假设 AI 调用插件: `analyze_image(image_path="/app/shared/photo.jpg")`
            >>> ai_provided_path = "/app/shared/photo.jpg"
            >>> # 插件使用 `get_file` 将沙盒路径转换为宿主机可访问的真实路径
            >>> host_path = _ctx.fs.get_file(ai_provided_path)
            >>> logger.info(host_path)  # doctest: +SKIP
            /path/to/project/data/sandbox_shared/sandbox_xxxx/photo.jpg
            >>> # 现在插件就可以读取这个文件了
            >>> # with open(host_path, "rb") as f:
            ... #     file_content = f.read()
        """
        if not self.container_key:
            return FileSystem(self.chat_key, f"sandbox_{self.chat_key}")
        return FileSystem(self.chat_key, self.container_key)

    @property
    def ms(self):
        """消息模块

        提供对底层 `nekro_agent.api.message` 模块的直接访问。
        主要用于需要手动指定 `chat_key` 的高级场景，例如**向其他聊天频道发送消息**。

        当你需要向当前聊天频道以外的聊天频道发送通知或消息时，应使用此模块。
        便捷方法如 `_ctx.send_text()` 默认只能向当前聊天频道发送。

        Example:
            >>> # 假设插件需要向一个监控频道发送状态更新
            >>> monitor_chat_key = "onebot_v11-group_987654321"
            >>>
            >>> # 使用 `_ctx.ms` 来向指定聊天频道发送消息
            >>> await _ctx.ms.send_text(monitor_chat_key, "System status: OK", _ctx)
            >>>
            >>> # 注意：调用底层模块时，需要手动传入 `_ctx` 对象。
        """
        from nekro_agent.api import message

        return message

    async def get_core_config(self) -> CoreConfig:
        """
        获取当前生效的核心配置实例。

        核心配置由 `系统基本设定 -> 适配器设定 -> 聊天频道设定` 三层配置混合生成，
        聊天频道设定优先级最高。插件可以通过此方法获取配置项。

        Example:
            >>> core_config = await ctx.get_core_config()
            >>> logger.info(core_config.ENABLE_NEKRO_CLOUD)
            True
        """
        if self._db_chat_channel is None:
            raise ValueError("未找到关联的数据库聊天频道")
        return await self._db_chat_channel.get_effective_config()

    async def get_onebot_v11_bot(self) -> OneBotV11Bot:
        """
        获取 OneBot V11 Bot 实例。

        注意：此方法仅适用于 OneBot V11 适配器！

        Example:
            >>> if ctx.adapter_key == "onebot_v11":
            ...     bot = await ctx.get_onebot_v11_bot()
            ...     await bot.send_private_msg(user_id=12345, message="Hello from Nekro Agent!")
        """
        if self.adapter_key != "onebot_v11":
            raise ValueError("获取 OneBot V11 Bot 实例失败，当前适配器不是 OneBot V11")
        from nekro_agent.adapters.onebot_v11.core.bot import get_bot

        return get_bot()

    async def send_text(self, content: str, *, record: bool = True):
        """发送文本消息到当前聊天频道。

        这是一个便捷方法，封装了 `message.send_text`，自动填充聊天频道信息。

        Args:
            content (str): 要发送的文本内容。
            record (bool): 是否将此消息记录到对话历史中，供 AI 后续参考。默认为 True。
                对于一些提示性、非关键性的消息，可以设置为 False，避免干扰 AI 的主线任务。

        Example:
            >>> await _ctx.send_text("Hello, this is a message from a plugin.")
            >>> await _ctx.send_text("正在处理，请稍候...", record=False)
        """
        await self.ms.send_text(self.chat_key, content, self, record=record)

    async def send_image(self, file_path: str, *, record: bool = True):
        """发送图片到当前聊天频道。

        这是一个便捷方法，封装了 `message.send_image`，自动填充聊天频道信息。

        Args:
            file_path (str): 图片的沙盒路径。通常由 `_ctx.fs` 工具生成。
            record (bool): 是否将此消息记录到对话历史中。默认为 True。

        Example:
            >>> # 1. 使用 fs 工具获取一个 AI 可用的图片路径
            >>> image_sandbox_path = await _ctx.fs.mixed_forward_file("https://nekro-agent-dev.oss-cn-beijing.aliyuncs.com/images/NA_logo.png")
            >>> # 2. 发送图片
            >>> await _ctx.send_image(image_sandbox_path)
        """
        await self.ms.send_image(self.chat_key, file_path, self, record=record)

    async def send_file(self, file_path: str, *, record: bool = True):
        """发送文件到当前聊天频道。

        这是一个便捷方法，封装了 `message.send_file`，自动填充聊天频道信息。

        Args:
            file_path (str): 文件的沙盒路径。通常由 `_ctx.fs` 工具生成。
            record (bool): 是否将此消息记录到对话历史中。默认为 True。

        Example:
            >>> # 1. 在插件共享目录创建一个文件
            >>> file_on_host = _ctx.fs.shared_path / "report.txt"
            >>> with open(file_on_host, "w") as f:
            ...     f.write("This is a report.")
            >>> # 2. 将其转换为 AI 可用的路径
            >>> file_sandbox_path = _ctx.fs.forward_file(file_on_host)
            >>> # 3. 发送文件
            >>> await _ctx.send_file(file_sandbox_path)
        """
        await self.ms.send_file(self.chat_key, file_path, self, record=record)

    async def push_system(self, message: str, trigger_agent: bool = False):
        """推送系统消息

        这是一个便捷方法，封装了 `message.push_system`，自动填充聊天频道信息。

        Args:
            message (str): 要推送的系统消息内容。
            trigger_agent (bool): 是否触发 AI 响应。默认为 False。

        Example:
            >>> # 推送处理结果并触发 AI 响应
            >>> await _ctx.push_system_message("Search result of 'xxx' is: xxx. Please check the result.", trigger_agent=True)
        """
        await self.ms.push_system(self.chat_key, message, self, trigger_agent=trigger_agent)

    async def get_preset_by_id(self, preset_id: int) -> Optional[DBPreset]:
        """根据人设ID获取人设数据对象

        Args:
            preset_id (int): 人设ID，-1表示未选择

        Returns:
            DBPreset | None: 人设数据对象，如果不存在或为-1则返回None

        Example:
            >>> preset = await _ctx.get_preset_by_id(123)
            >>> if preset:
            ...     logger.info(f"人设名称: {preset.title}")
            ...     logger.info(f"人设内容: {preset.content}")
        """
        if preset_id == -1:
            return None

        return await DBPreset.get_or_none(id=preset_id)

    async def get_effective_preset_by_id(self, preset_id: int = -1):
        """根据人设ID获取生效的人设数据对象

        与 get_preset_by_id 的区别：
        - get_preset_by_id: 当 preset_id 为 -1 时返回 None
        - get_effective_preset_by_id: 当 preset_id 为 -1 时返回默认人设

        Args:
            preset_id (int): 人设ID，-1表示使用默认人设

        Returns:
            DBPreset | DefaultPreset: 人设数据对象，如果为-1则返回默认人设

        Example:
            >>> preset = await _ctx.get_effective_preset_by_id(-1)
            >>> logger.info(f"生效人设名称: {preset.title}")  # 总是有值
        """

        if preset_id == -1:
            # 返回默认人设，使用当前聊天频道的默认人设逻辑
            if self._db_chat_channel:
                return await self._db_chat_channel.get_preset()
            # 如果没有聊天频道上下文，返回系统默认人设

            from nekro_agent.models.db_chat_channel import DefaultPreset

            return DefaultPreset(name=config.AI_CHAT_PRESET_NAME, content=config.AI_CHAT_PRESET_SETTING)

        # 尝试获取指定的人设
        preset = await DBPreset.get_or_none(id=preset_id)
        if preset:
            return preset

        # 如果指定的人设不存在，也返回默认人设
        if self._db_chat_channel:
            return await self._db_chat_channel.get_preset()

        from nekro_agent.models.db_chat_channel import DefaultPreset

        return DefaultPreset(name=config.AI_CHAT_PRESET_NAME, content=config.AI_CHAT_PRESET_SETTING)

    async def set_preset(self, preset_id: Optional[int] = None) -> bool:
        """设置当前生效的人设"""
        from nekro_agent.models.db_chat_channel import DBChatChannel

        if not self.chat_key:
            raise ValueError("未找到关联的聊天频道")
        if not self._db_chat_channel:
            self._db_chat_channel = await DBChatChannel.get_channel(chat_key=self.chat_key)
        if preset_id == -1:
            preset_id = None
        if self._db_chat_channel.preset_id == preset_id:
            return False
        await self._db_chat_channel.set_preset(preset_id)
        return True

    async def current_preset(self):
        """当前生效的人设"""
        return await self.get_effective_preset_by_id()

    @classmethod
    def create_by_db_chat_channel(
        cls,
        db_chat_channel: "DBChatChannel",
        container_key: Optional[str] = None,
        from_chat_key: Optional[str] = None,
        webhook_request: Optional[WebhookRequest] = None,
    ) -> "AgentCtx":
        """从数据库聊天频道创建 AgentCtx (内部方法)"""
        return cls(
            container_key=container_key,
            from_chat_key=from_chat_key or db_chat_channel.chat_key,
            channel_id=db_chat_channel.channel_id,
            channel_name=db_chat_channel.channel_name,
            channel_type=db_chat_channel.channel_type,
            adapter_key=db_chat_channel.adapter_key,
            webhook_request=webhook_request,
            _db_chat_channel=db_chat_channel,
        )

    @classmethod
    async def create_by_chat_key(
        cls,
        chat_key: str,
        container_key: Optional[str] = None,
        from_chat_key: Optional[str] = None,
        webhook_request: Optional[WebhookRequest] = None,
    ) -> "AgentCtx":
        """从聊天频道创建 AgentCtx (内部方法)"""
        from nekro_agent.models.db_chat_channel import DBChatChannel

        db_chat_channel = await DBChatChannel.get_channel(chat_key=chat_key)
        return cls.create_by_db_chat_channel(db_chat_channel, container_key, from_chat_key, webhook_request)

    @classmethod
    async def create_by_webhook(
        cls,
        webhook_request: WebhookRequest,
    ) -> "AgentCtx":
        """从 Webhook 请求创建 AgentCtx (内部方法)"""
        return cls(webhook_request=webhook_request)
