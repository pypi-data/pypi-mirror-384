# -*- coding: UTF-8 -*-

from .base import BaseCracker


class ReCaptchaUniversalCracker(BaseCracker):
    
    cracker_name = "recaptcha"
    cracker_version = "universal"    

    """
    recaptcha universal cracker
    :param sitekey: 验证码对接 key
    :param referer: 触发验证码页面地址
    :param size: reload 接口中的 size 参数, 只有 invisible 和 normal 两个选项
    :param title: 触发验证码页面 document.title, 默认空, 传了成功率更高且更快
    调用示例:
    cracker = ReCaptchaUniversalCracker(
        user_token="xxx",
        sitekey="xxx",
        referer="xxx",
        size="invisible",

        # debug=True,
        # proxy=proxy,
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["sitekey", "referer", "size", "title"]
    # 默认可选参数
    option_params = {
        "hl": "zh-CN",
        "action": None,
        "ubd": False,
        "sa": None,
    }


class ReCaptchaEnterpriseCracker(ReCaptchaUniversalCracker):
    
    cracker_name = "recaptcha"
    cracker_version = "enterprise"    

    """
    recaptcha cracker
    :param sitekey: 验证码对接 key
    :param referer: 触发验证码页面地址
    :param size: reload 接口中的 size 参数, 只有 invisible 和 normal 两个选项
    :param title: 触发验证码页面 document.title, 默认空, 传了成功率更高且更快
    调用示例:
    cracker = ReCaptchaUniversalCracker(
        user_token="xxx",
        sitekey="xxx",
        referer="xxx",
        size="invisible",

        # debug=True,
        # proxy=proxy,
    )
    ret = cracker.crack()
    """
    
    
class ReCaptchaSteamCracker(ReCaptchaEnterpriseCracker):
    
    cracker_name = "recaptcha"
    cracker_version = "steam"

    """
    recaptcha cracker
    :param sitekey: 验证码对接 key
    :param referer: 触发验证码页面地址
    :param size: reload 接口中的 size 参数, 只有 invisible 和 normal 两个选项
    :param title: 触发验证码页面 document.title, 默认空, 传了成功率更高且更快
    :param s: steam 首页返回的 s 值
    调用示例:
    cracker = ReCaptchaUniversalCracker(
        user_token="xxx",
        sitekey="xxx",
        referer="xxx",
        size="invisible",
        s="xxx",

        # debug=True,
        # proxy=proxy,
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["sitekey", "referer", "size", "title", "s"]


class ReCaptchaAppCracker(BaseCracker):
    
    cracker_name = "recaptcha"
    cracker_version = "app"

    """
    recaptcha cracker
    :param sitekey: 验证码对接 key
    :param apk: 触发验证码页面地址
    :param action: 
    调用示例:
    cracker = ReCaptchaUniversalCracker(
        user_token="xxx",
        sitekey="xxx",
        apk="xxx",
        action="",

        # debug=True,
        # proxy=proxy,
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["sitekey", "apk"]
    # 可选参数
    option_params = {
        "action": ""
    }
