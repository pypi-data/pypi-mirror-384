# -*- coding: UTF-8 -*-

from .base import BaseCracker


class IncapsulaReese84Cracker(BaseCracker):
    
    cracker_name = "incapsula"
    cracker_version = "reese84"    

    """
    incapsula cracker
    :param href: 触发 incapsula 盾验证的首页地址
    :param user_agent: 请求流程使用 ua
    :param script: href 返回的 js 脚本
    调用示例:
    cracker = IncapsulaCracker(
        user_token="xxx",
        href="https://mhotshow.hkticketing.com/dothisse-Ban-alour-is-tooth-chame-Intome-Thou-pe",
        script="(function(){})()",
        user_agent="Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.48 Mobile Safari/537.36",
        # debug=True,
        # proxy=proxy,
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["href", "user_agent"]
    # 可选参数
    option_params = {
        "script": "",
        "submit": True,
        "update": False,
        "cookies": {}
    }


class IncapsulaUtmvcCracker(BaseCracker):
    
    cracker_name = "incapsula"
    cracker_version = "utmvc"    

    """
    incapsula cracker
    :param script: Incapsula js 脚本字符串
    :param cookies: 携带 incap_sess_xxx 的 cookies, {"incap_ses_xxx": "xaxa"}
    调用示例:
    cracker = IncapsulaUtmvcCracker(
        script=script,
        cookies={},
        
        user_token="xxx",

        # debug=True,
        # check_useful=True,
        # proxy=proxy,
        # submit=False
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["href", "cookies", "user_agent", "script"]
    # 可选参数
    option_params = {
        "proxy": "",
        "submit": False
    }


class IncapsulaRbzidCracker(BaseCracker):
    
    cracker_name = "incapsula"
    cracker_version = "rbzid"    

    """
    incapsula cracker
    :param href: 触发 incapsula 盾验证的首页地址
    :param user_agent: 请求流程使用 ua
    :param script: href 返回的 js 脚本
    """
    
    # 必传参数
    must_check_params = ["href", "user_agent", "script"]

