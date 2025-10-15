# -*- coding: UTF-8 -*-


from .base import BaseCracker


class AwsUniversalCracker(BaseCracker):
    cracker_name = "aws"
    cracker_version = "universal"

    """
    aws universal cracker
    :param href: 触发验证的页面地址
    :param user_agent: 请求头
    调用示例:
    cracker = AwsUniversalCracker(
        user_token="xxx",
        href="xxx",

        # debug=True,
        # proxy=proxy,
    )
    ret = cracker.crack()
    """

    # 必传参数
    must_check_params = ["href"]
    # 默认可选参数
    option_params = {
        "user_agent": "",
        "only_sense" : False,
        "challenge_url": "",
        "api_key": "",
        "html": ""
    }
