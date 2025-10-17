from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from tortoise.expressions import Q

from nekro_agent.core.config import config
from nekro_agent.models.db_chat_channel import DBChatChannel
from nekro_agent.models.db_chat_message import DBChatMessage
from nekro_agent.models.db_user import DBUser
from nekro_agent.schemas.message import Ret
from nekro_agent.services.user.deps import get_current_active_user
from nekro_agent.services.user.perm import Role, require_role

router = APIRouter(prefix="/chat-channel", tags=["ChatChannel"])


@router.get("/list", summary="获取聊天频道列表")
@require_role(Role.Admin)
async def get_chat_channel_list(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    chat_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    _current_user: DBUser = Depends(get_current_active_user),
) -> Ret:
    """获取聊天频道列表

    排序逻辑：
    - 按最后活跃时间排序，最后活跃时间 = max(conversation_start_time, 最后消息时间)
    - 这样重置的聊天频道会根据重置时间合理排序，同时考虑历史消息的影响

    统计逻辑：
    - 消息数量：仅统计conversation_start_time之后的消息（重置后的有效消息）
    - 最后消息时间：从整个消息表中查询，不受重置影响
    """
    query = DBChatChannel

    # 搜索条件
    if search:
        query = query.filter(
            Q(chat_key__contains=search) | Q(channel_name__contains=search),
        )
    if chat_type:
        query = query.filter(chat_key__contains=f"{chat_type}_")
    if is_active is not None:
        query = query.filter(is_active=is_active)

    # 获取所有符合条件的频道
    channels = await query.all()

    # 获取每个频道的统计信息
    channel_info_list = []
    for channel in channels:
        # 1. 计算重置后的消息数量（从conversation_start_time开始）
        message_count = await DBChatMessage.filter(
            chat_key=channel.chat_key,
            create_time__gte=channel.conversation_start_time,
        ).count()

        # 2. 获取整个聊天频道中的最后一条消息（不限制conversation_start_time）
        last_message = await DBChatMessage.filter(chat_key=channel.chat_key).order_by("-create_time").first()

        # 3. 计算最后活跃时间：max(conversation_start_time, 最后消息时间)
        conversation_start_time = channel.conversation_start_time
        if conversation_start_time.tzinfo is not None:
            conversation_start_time = conversation_start_time.replace(tzinfo=None)

        if last_message:
            last_message_time = last_message.create_time
            if last_message_time.tzinfo is not None:
                last_message_time = last_message_time.replace(tzinfo=None)
            # 取conversation_start_time和最后消息时间中更晚的那个
            last_active_time = max(conversation_start_time, last_message_time)
        else:
            # 如果没有消息，使用conversation_start_time作为活跃时间
            last_active_time = conversation_start_time

        channel_info_list.append(
            {
                "channel": channel,
                "message_count": message_count,
                "last_active_time": last_active_time,
                "last_message_time": last_message_time if last_message else None,
            },
        )

    # 按最后活跃时间排序（最近活跃的在前）
    channel_info_list.sort(key=lambda x: x["last_active_time"], reverse=True)

    # 分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_channels = channel_info_list[start_idx:end_idx]

    # 构建返回结果
    result = []
    for info in paged_channels:
        channel = info["channel"]
        result.append(
            {
                "id": channel.id,
                "chat_key": channel.chat_key,
                "channel_name": channel.channel_name,
                "is_active": channel.is_active,
                "chat_type": channel.chat_type.value,
                "message_count": info["message_count"],
                "create_time": channel.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "update_time": channel.update_time.strftime("%Y-%m-%d %H:%M:%S"),
                # 保持前端接口兼容：last_message_time显示实际的最后消息时间
                "last_message_time": (
                    info["last_message_time"].strftime("%Y-%m-%d %H:%M:%S") if info["last_message_time"] is not None else None
                ),
            },
        )

    return Ret.success(
        msg="获取成功",
        data={
            "total": len(channels),
            "items": result,
        },
    )


@router.get("/detail/{chat_key}", summary="获取聊天频道详情")
@require_role(Role.Admin)
async def get_chat_channel_detail(chat_key: str, _current_user: DBUser = Depends(get_current_active_user)) -> Ret:
    """获取聊天频道详情"""
    channel = await DBChatChannel.get_or_none(chat_key=chat_key)
    if not channel:
        return Ret.fail(msg="聊天频道不存在")

    # 获取聊天频道数据
    message_count = await DBChatMessage.filter(chat_key=chat_key, create_time__gte=channel.conversation_start_time).count()

    # 获取最近一条消息的时间
    last_message = await DBChatMessage.filter(chat_key=chat_key).order_by("-create_time").first()
    last_message_time = last_message.create_time if last_message else None

    # 获取参与用户数
    unique_users = await DBChatMessage.filter(chat_key=chat_key).distinct().values_list("sender_id", flat=True)

    return Ret.success(
        msg="获取成功",
        data={
            "id": channel.id,
            "chat_key": channel.chat_key,
            "channel_name": channel.channel_name,
            "is_active": channel.is_active,
            "chat_type": channel.chat_type.value,
            "message_count": message_count,
            "unique_users": len(unique_users),
            "create_time": channel.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "update_time": channel.update_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_message_time": last_message_time.strftime("%Y-%m-%d %H:%M:%S") if last_message_time else None,
            "conversation_start_time": channel.conversation_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "preset_id": channel.preset_id,
        },
    )


@router.post("/{chat_key}/active", summary="设置聊天频道激活状态")
@require_role(Role.Admin)
async def set_chat_channel_active(
    chat_key: str,
    is_active: bool,
    _current_user: DBUser = Depends(get_current_active_user),
) -> Ret:
    """设置聊天频道激活状态"""
    channel = await DBChatChannel.get_or_none(chat_key=chat_key)
    if not channel:
        return Ret.fail(msg="聊天频道不存在")

    await channel.set_active(is_active)
    return Ret.success(msg="设置成功")


@router.post("/{chat_key}/reset", summary="重置聊天频道状态")
@require_role(Role.Admin)
async def reset_chat_channel(
    chat_key: str,
    _current_user: DBUser = Depends(get_current_active_user),
) -> Ret:
    """重置聊天频道状态"""
    channel = await DBChatChannel.get_or_none(chat_key=chat_key)
    if not channel:
        return Ret.fail(msg="聊天频道不存在")

    await channel.reset_channel()
    return Ret.success(msg="重置成功")


@router.get("/{chat_key}/messages", summary="获取聊天频道消息列表")
@require_role(Role.Admin)
async def get_chat_channel_messages(
    chat_key: str,
    before_id: Optional[int] = None,
    page_size: int = 32,
    _current_user: DBUser = Depends(get_current_active_user),
) -> Ret:
    """获取聊天频道消息列表"""
    channel = await DBChatChannel.get_or_none(chat_key=chat_key)
    if not channel:
        return Ret.fail(msg="聊天频道不存在")

    # 查询消息，只返回conversation_start_time之后的消息
    query = DBChatMessage.filter(chat_key=chat_key, create_time__gte=channel.conversation_start_time)
    if before_id:
        query = query.filter(id__lt=before_id)

    # 统计总数
    total = await query.count()

    # 查询消息
    messages = await query.order_by("-id").limit(page_size)

    return Ret.success(
        msg="获取成功",
        data={
            "total": total,
            "items": [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "sender_name": msg.sender_name,
                    "content": msg.content_text,
                    "create_time": msg.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for msg in messages
            ],
        },
    )


@router.post("/{chat_key}/preset", summary="设置聊天频道人设")
@require_role(Role.Admin)
async def set_chat_channel_preset(
    chat_key: str,
    preset_id: Optional[int] = None,
    _current_user: DBUser = Depends(get_current_active_user),
) -> Ret:
    """设置聊天频道人设，传入 preset_id=None 则使用默认人设"""
    channel = await DBChatChannel.get_or_none(chat_key=chat_key)
    if not channel:
        return Ret.fail(msg="聊天频道不存在")

    # 使用模型的 set_preset 方法
    result_msg = await channel.set_preset(preset_id)
    return Ret.success(msg=result_msg)
