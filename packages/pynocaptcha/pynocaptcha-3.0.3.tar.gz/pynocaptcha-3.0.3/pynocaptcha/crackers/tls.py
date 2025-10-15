# -*- coding: UTF-8 -*-

from .base import BaseCracker


class TlsV1Cracker(BaseCracker):
    
    cracker_name = "tls"
    cracker_version = "v1"    

    """
    tls v1 cracker
    :param url: 请求的 url 地址
    :param method: 请求方法, get/post
    :param headers: 请求的请求头, 可以是字符串或对象, 不传默认的请求头为 { 'User-Agent': '随机 ua' }
    :param cookies: 示例: { "value": "_abck=xxx; bm_sz=xxx", "uri": "https://example.com" }
    :param proxy: 请求流程使用的代理, 支持 protocol: http/https/socks5, 无验证代理格式: {protocol}://{ip}:{port}, 有验证代理格式: {protocol}://{user}:{password}@{ip}:{port}
    :param data: post 请求流程的 post 表单, 可以是字符串或对象, { '1': '2', '3': '4' } / '1=2&3=4'	
    :param json: post 请求流程的 json 数据, 示例 { '1': '2', '3': '4' }
    :param timeout: 请求超时时间（秒）, 默认 15 秒
    :param http2: 是否 http2 协议, 默认 false
    :param redirect: 是否重定向, 默认 true
    :param ja3: 自定义 ja3 指纹, 不传表现为最新 chrome 的随机指纹
    调用示例:
    cracker = TlsV1Cracker(
        user_token="xxx",
        url="https://www.baidu.com",
        
        # debug=True,
        # proxy=proxy,
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["url"]
    # 可选参数
    option_params = {
        "method": "get",
        "headers": None,
        "cookies": None,
        "proxy": None,
        "data": None,
        "json": None,
        "timeout": 15,
        "http2": False,
        "redirect": True,
        "ja3": None
    }
