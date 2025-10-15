# -*- coding: UTF-8 -*-

from typing import Any

from curl_cffi import requests
from loguru import logger


class BaseCracker:
    
    # 破解器
    cracker_name = "base"
    
    # 破解版本
    cracker_version = "universal"
    
    # 必须参数列表
    must_check_params = []
    
    # 可选参数
    option_params = {}
    
    # 需要删除的多余参数
    delete_params = []
    
    _extra_data = None
    
    def __init__(
        self,   
        show_ad=True, 
        user_token: str = None,
        developer_id: str = None,   
        internal_host: bool = False,
        # user_agent: str = None,
        # cookies: dict = {},
        # proxy: str = None, 
        # timeout: int = 30,
        # debug: bool = False,
        # check_useful: bool = False,
        # max_retry_times: int = 3,
        # internal=True,
        # auth=False,
        **kwargs
    ) -> None:
        """
        :param user_token: nocaptcha.io 用户 token
        :param developer_id: nocaptcha.io 用户上级代理 token
        :param user_agent: 请求流程使用 ua
        :param proxy: 请求流程代理, 不传默认使用系统代理, 某些强制要求代理一致或者特定区域的站点请传代理, 支持协议 http/https/socks5, 代理格式: {protocol}://{ip}:{port}（如有账号验证：{protocol}://{user}:{password}@{ip}:{port}）
        :param timeout: 破解接口超时时间(秒)
        :param debug: 是否开启 debug 模式
        :param check_useful: 检查破解是否成功
        :param max_retry_times: 最大重试次数
        :param internal: 是否使用国内代理
        :param auth: 是否大户通道验证模式
        :param internal_host: 是否使用国内域名 api.nocaptcha.cn, 默认 api.nocaptcha.io
        """
        if show_ad:
            logger.debug("感谢选择 nocaptcha, 我们只做别人做不到的(手动狗头)~")
            logger.debug("欢迎推荐注册, 官网地址: https://www.nocaptcha.io/")
        self.user_token = user_token
        if not self.user_token:
            raise Exception("缺少用户凭证")
        self.developer_id = developer_id
        self.cookies = kwargs.get("cookies") or {}
        self.user_agent = kwargs.get("user_agent")
        self.proxy = kwargs.get("proxy")
        self.timeout = kwargs.get("timeout") or 30
        self.debug = kwargs.get("debug", False)
        self.check_useful = kwargs.get("check_useful", False)
        self.max_retry_times = kwargs.get("max_retry_times", 3)
        self.api_host = 'api.nocaptcha.cn' if internal_host else 'api.nocaptcha.io'
        self.wanda_args = {
            "internal": kwargs.get('internal', True),
            "is_auth": kwargs.get('auth', False),
            "timeout": self.timeout
        }
        for k in self.must_check_params:
            _v = kwargs.get(k)
            if not hasattr(self, k) or getattr(self, k) is None:
                setattr(self, k, _v)
            if _v is not None:
                self.wanda_args.update({ k: _v })
        for k, v in self.option_params.items():
            _v = kwargs.get(k, v)
            if not hasattr(self, k) or getattr(self, k) is None:
                setattr(self, k, _v)
            if _v is not None:
                self.wanda_args.update({ k: _v })
        
        for k in self.delete_params:
            if k in self.wanda_args:
                del self.wanda_args[k]

        for k in self.must_check_params:
            if getattr(self, k) is None:
                raise AttributeError(f"缺少参数 {k}, 请检查")

        if self.user_agent:
            self.wanda_args["user_agent"] = self.user_agent
        if self.cookies:
            self.wanda_args["cookies"] = self.cookies
        if self.proxy:
            self.wanda_args["proxy"] = self.proxy

        self.request()
        
    def request(self):
        pass
    
    def response(self, result: Any):
        return result
        
    def check(self, ret):
        return True

    def extra(self):
        return self._extra_data
    
    def fix_headers(self, headers: dict):
        for k, _ in headers.items():
            k = k.lower()
            if k in [
                "sec-ch-ua", 
                "accept-language",
                'sec-ch-ua-arch',
                'sec-ch-ua-bitness',
                'sec-ch-ua-full-version',
                'sec-ch-ua-full-version-list',
                'sec-ch-ua-mobile',
                'sec-ch-ua-model',
                'sec-ch-ua-platform',
                'sec-ch-ua-platform-version',
                "user-agent",
            ] and self._extra_data.get(k):
                headers[k] = self._extra_data[k]            

    def crack(self):
        headers = {
            "User-Token": self.user_token
        }
        if self.developer_id:
            headers["Developer-Id"] = self.developer_id
        
        retry_times = 0        
        resp = {}
        while retry_times < self.max_retry_times:
            try:
                resp = requests.post(
                    f"http://{self.api_host}/api/wanda/{self.cracker_name}/{self.cracker_version}", 
                    headers=headers, json=self.wanda_args, timeout=self.timeout
                ).json()
                if self.debug:
                    logger.info(resp)
                break
            except Exception as e:
                if self.debug:
                    logger.error(e)
                retry_times += 1
        wanda_ret = resp.get("data")
        self._extra_data = resp.get("extra")
        if not wanda_ret:
            if self.debug:
                logger.error(resp.get("msg"))
            return
        ret = self.response(wanda_ret)
        if self.check_useful:
            if self.check(wanda_ret):
                if self.debug:
                    logger.success("crack success")
            else:
                retry_times += 1
                if retry_times < self.max_retry_times:
                    return self.crack()
                else:
                    logger.error("crack fail")
        return ret
