# -*- coding: UTF-8 -*-

from .base import BaseCracker


class DiscordCracker(BaseCracker):
    
    cracker_name = "discord"
    cracker_version = "guild"    

    """
    discord cracker
    :param authorization: discord 账号登录凭证
    :param guild_id: 群 id
    :param cookies: 
    调用示例:
    cracker = DiscordCracker(
        user_token="xxx",
        authorization="MTExNzI1NDQ3NzA2NjU0MzE5NQ.xxx",
        guild_id='645607528297922560',
        # guild_name='fusionlist'
        # debug=True,
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["authorization"]
    # 可选参数
    option_params = {
        "guild_id": "",
        "guild_name": ""
    }
