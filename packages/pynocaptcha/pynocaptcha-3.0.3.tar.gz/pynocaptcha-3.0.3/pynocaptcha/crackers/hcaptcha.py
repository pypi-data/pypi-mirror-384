# -*- coding: UTF-8 -*-


from .base import BaseCracker


class HcaptchaCracker(BaseCracker):
    
    cracker_name = "hcaptcha"
    cracker_version = "universal"    

    """
    hcaptcha cracker
    :param sitekey: hcaptcha 对接网站的 key
    :param rqtoken: 验证码配置接口有返回 captcha_rqdata、captcha_rqtoken 的请携带该值(如 discord 加频道)
    :param user_agent: 请求流程使用 ua, 必须使用 MacOS Firefox User-Agent, 否则可能破解失败
    :param referer: 触发 hcaptcha 验证的页面地址
    :param mode: 验证模式, 默认 picture 图片验证模式, 可选 question 题库模式
    调用示例:
    cracker = HcaptchaCracker(
        user_token="xxx",
        sitekey='f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34',
        rqdata="",
        referer="https://discord.com/login",

        # debug=True,
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["sitekey", "referer"]
    # 默认可选参数
    option_params = {
        "mode": "picture",   # 验证模式, 默认图片验证, 可选 question 题库验证
        "rqdata": "",
        "need_ekey": False,
        "region": None,
        "domain": "hcaptcha.com",
    }


class HcaptchaV2Cracker(BaseCracker):
    
    cracker_name = "hcaptcha"
    cracker_version = "v2"    

    """
    hcaptcha cracker
    :param sitekey: hcaptcha 对接网站的 key
    :param rqtoken: 验证码配置接口有返回 captcha_rqdata、captcha_rqtoken 的请携带该值(如 discord 加频道)
    :param user_agent: 请求流程使用 ua, 必须使用 MacOS Firefox User-Agent, 否则可能破解失败
    :param referer: 触发 hcaptcha 验证的页面地址
    :param mode: 验证模式, 默认 picture 图片验证模式, 可选 question 题库模式
    调用示例:
    cracker = HcaptchaCracker(
        user_token="xxx",
        sitekey='f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34',
        rqdata="",
        referer="https://discord.com/login",

        # debug=True,
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["sitekey", "referer"]
    # 默认可选参数
    option_params = {
        "action": None,
        "rqdata": "",
        "need_ekey": False,
        "title": None,
        "extra": {},
        "region": None,
        "ip": None,
        "timezone": None,
        "geolocation": None,
    }
