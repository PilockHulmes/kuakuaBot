from pydantic import BaseModel


class Config(BaseModel):
    """content_echo 插件配置"""

    # 生效群白名单
    group_whitelist: list[int] = [
        853041949,
        1020882307,
        244960293,
    ]

    # 消息计数差阈值：新消息与旧记录的消息计数差在此范围内才触发 echo
    counter_threshold: int = 200

    # Redis 记录过期时间（秒），默认 24 小时
    record_ttl: int = 86400

    # 默认发送的图片路径（相对于 bot 工作目录，即 kuakuaBot/ 下）
    echo_image_path: str = "assets/repeat.gif"

    # 按群配置不同图片（key=群号, value=图片路径），优先于此配置
    per_group_image: dict[int, str] = {}
