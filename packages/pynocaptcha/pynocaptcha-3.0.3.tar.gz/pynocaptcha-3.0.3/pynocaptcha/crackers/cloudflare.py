# -*- coding: UTF-8 -*-

from .base import BaseCracker


class CloudFlareCracker(BaseCracker):
    
    cracker_name = "cloudflare"
    cracker_version = "universal"    

    """
    cloudflare cracker
    :param href: 触发 cloudfalre 验证的首页地址
    :param user_agent: 请求流程使用 ua, 不传
    :param headers: 触发验证必须的 headers, 默认 {} 
    :param cookies: 触发验证必须的 cookies, 默认 {} 
    :param html: 是否需要返回 html
    :param alpha: 是否 alpha 模式, true 会更快
    :param timeout: 最大破解超时时间
    调用示例:
    cracker = CloudFlareCracker(
        href=href,
        user_token="xxx",
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["href"]
    # 默认可选参数
    option_params = {
        "branch": "Master",
        "user_agent": None,
        "headers": {},
        "cookies": {},
        "html": False,
        "sitekey": "",
        "alpha": False,
        "action": None,
        "cdata": None,
        "timeout": 30
    }
