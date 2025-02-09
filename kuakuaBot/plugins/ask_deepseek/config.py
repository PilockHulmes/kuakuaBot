from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""
    group_whilelist: list[int] = [
        1020882307, # 喵呜测试机器人的群
    ]
    
    qq_user_whilelist: list[int] = [
        392206976, # me
    ]