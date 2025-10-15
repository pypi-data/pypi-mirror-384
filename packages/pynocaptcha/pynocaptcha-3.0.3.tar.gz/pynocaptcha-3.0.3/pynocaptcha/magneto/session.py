# -*- coding: utf-8 -*-

import re
import sys


from typing import Dict, Optional, Union, Tuple, List

if sys.version_info >= (3, 8):  # pragma: no cover (py38+)
    from typing import Literal
else:  # pragma: no cover (py38+)
    from typing_extensions import Literal

import rnet
import random
import json
from urllib.parse import urlencode
from .headers import parse_sec_ch_ua, ACCEPT_LANGUAGE_MAP
from .response import Response
from .cookies import Cookie


class Session:
    
    def __init__(
        self, 
        user_agent: Union[int, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
        cookies: Optional[Dict[str, str]] = None, proxy: Optional[str] = None, ipinfo: dict = {}, timeout: int = 15,
        allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None, sync: bool = True
    ):
        self.cookies = Cookie(cookies or {})
        
        if not user_agent:
            version = random.randint(115, 137)
            user_agent = random.choice([
                f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36",
                f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36',  
                f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36 Edg/{version}.0.0.0',
                f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36 Edg/{version}.0.0.0",
            ])

        if isinstance(user_agent, tuple):
            user_agent_version, user_agent_os, user_agent_brand = user_agent        
            if not user_agent_version:
                user_agent_version = random.randint(115, 137)
            if isinstance(user_agent_version, tuple):
                user_agent_version = random.randint(user_agent_version[0], user_agent_version[1])
            user_agent = {
                "macos": {
                    "chrome": f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{user_agent_version}.0.0.0 Safari/537.36',
                    "edge": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{user_agent_version}.0.0.0 Safari/537.36 Edg/{user_agent_version}.0.0.0",
                },
                "windows": {
                    "chrome": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{user_agent_version}.0.0.0 Safari/537.36",
                    "edge": f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{user_agent_version}.0.0.0 Safari/537.36 Edg/{user_agent_version}.0.0.0',
                },
            }[user_agent_os or random.choice(["macos", "windows"])][user_agent_brand or random.choice(["chrome", "edge"])]
        
        self.user_agent = user_agent

        sec_ch_ua_ptf = '"macOS"' if 'Mac' in user_agent else '"Windows"'
        sec_ch_ua = parse_sec_ch_ua(user_agent)
        
        self.client_hints = {
            'sec-ch-ua': sec_ch_ua,
            'sec-ch-ua-platform': sec_ch_ua_ptf,
            'user-agent': user_agent, 
            'accept-language': 'zh-CN,zh;q=0.9'
        }
        
        self._chrome_version = int(re.search(r'Chrome\/(\d+)\.\d+\.\d+\.\d+', user_agent)[1])
            
        if 'Edg' in user_agent:
            impersonate_brand = "Edge"
            impersonate_versions = [122, 127, 131, 134]
        else:
            impersonate_brand = "Chrome"
            impersonate_versions = [114, 116, 117, 118, 119, 120, 123, 124, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136]
        
        min_version = None
        impersonate_version = None
        for v in impersonate_versions:
            cv = abs(v - self._chrome_version)
            if not min_version or cv < min_version:
                min_version = cv
                impersonate_version = v
                
        impersonate = f'{impersonate_brand}{impersonate_version}'
        
        self.proxy = proxy
        proxies = []
        if proxy:
            if not proxy.startswith("http"):
                if "://" in proxy:
                    proxy = proxy.split("://")[1]
            
            self.proxy = proxy            
            proxies.append(rnet.Proxy.all(url=proxy))

        http_version_cfg = {
            "http1_only": False, "http2_only": False
        }
        if http_version == "http1":
            http_version_cfg["http1_only"] = True
        elif http_version == "http2":
            http_version_cfg["http2_only"] = True
            
        self._session = (rnet.BlockingClient if sync else rnet.Client)(
            impersonate=rnet.ImpersonateOption(
                impersonate=getattr(rnet.Impersonate, impersonate),
                impersonate_os=rnet.ImpersonateOS.MacOS if "Mac" in user_agent else rnet.ImpersonateOS.Windows,
            ),
            referer=True,
            user_agent=user_agent,
            timeout=timeout,
            cookie_store=False,
            no_keepalive=False,
            verify=verify,
            allow_redirects=allow_redirects,
            **http_version_cfg,
            proxies=proxies
        )
        
        self.ipinfo = ipinfo or {}
        
        if self.ipinfo.get("country"):
            self.client_hints['accept-language'] = ACCEPT_LANGUAGE_MAP.get(self.ipinfo["country"], 'zh-CN,zh;q=0.9')
    
    def __getattr__(self, name):
        """
        当访问 Session 没有定义的属性或方法时，尝试从 self._session 获取。
        这样可以支持 self._session 的所有方法和属性。
        """
        # 获取 self._session 的属性或方法
        attr = getattr(self._session, name)

        # 如果是方法，返回一个包装器以确保调用时正确传递参数
        if callable(attr):
            def wrapper(*args, **kwargs):
                return attr(*args, **kwargs)
            return wrapper
        else:
            return attr

    def update_ipinfo(self):
        try:
            resp = self._session.get("https://ipinfo.io/json", headers={
                "user-agent": self.user_agent,
            }, timeout=5).json()
            self.ipinfo.update({
                "country": resp["country"].lower(),
                "ip": resp.get("ip"),
                "timezone": resp.get("timezone"),
                "geolocation": resp.get("loc")
            })
            self.client_hints['accept-language'] = ACCEPT_LANGUAGE_MAP.get(self.ipinfo["country"], 'zh-CN,zh;q=0.9')
        except:
            pass
            
    def complete_headers(self, headers: Union[Dict[str, str], List[str], str]):
        """
        补全请求头
        :param headers: 传入的请求头
        :return
        """
        processed_headers = rnet.HeaderMap({})
        
        if isinstance(headers, str):
            headers = headers.split("\n")
        
        # 补全 cookie
        if isinstance(headers, list):
            for header in headers:
                key, value = [_.strip() for _ in header.split(":", 1)]
                if key.lower() == "cookie":
                    set_cookies = value.split(";")
                    for set_cookie in set_cookies:
                        set_cookie_key, set_cookie_value = set_cookie.strip().split("=", 1)
                        self.cookies[set_cookie_key] = set_cookie_value
                    continue                        

                processed_headers.append(key, value)
            
            if len(self.cookies) > 0:
                processed_headers.append('Cookie', self.cookies.to_str())
            
            return processed_headers
        
        set_cookies = headers.get("Cookie") or headers.get("cookie")
        if set_cookies:
            for set_cookie in set_cookies.split(";"):
                set_cookie_key, set_cookie_value = set_cookie.strip().split("=", 1)
                self.cookies[set_cookie_key] = set_cookie_value
        
        if len(self.cookies) > 0:
            if 'Cookie' in headers:           
                headers['Cookie'] = self.cookies.to_str()
            else:
                headers['cookie'] = self.cookies.to_str()
        
        # 处理 priority 124 开始有 priority
        priority = headers.get('priority') or headers.get('Priority')
        
        if self._chrome_version <= 123 and priority:
            if 'Priority' in headers:
                del headers['Priority']
                    
            if 'priority' in headers:
                del headers['priority']
        
        # 补全 accept
        set_accept = headers.get('accept') or headers.get('Accept')
        if not set_accept:
            headers['Accept'] = '*/*'
        
        # 补全 accept-language
        accept_language = None
        if self.ipinfo.get('country'):
            accept_language = ACCEPT_LANGUAGE_MAP.get(self.ipinfo['country'], "zh-CN,zh;q=0.9")

        # ipnifo 格式
        elif self.ipinfo.get('language'):
            accept_language = self.ipinfo['language'] + ',' + self.ipinfo['language'].split('-')[0] + ';q=0.9'
        
        set_accept_language = headers.get('accept-language') or headers.get('Accept-Language')
        if accept_language:
            if not set_accept_language:
                headers['Accept-Language'] = accept_language
            else:
                if ';' not in set_accept_language and set_accept_language != accept_language:
                    headers['Accept-Language'] = accept_language
                    if 'accept-language' in headers:
                        del headers['accept-language']
        
        # 更新 ua 以及 client_hints
        if 'User-Agent' in headers:
            headers['User-Agent'] = self.user_agent
        else:
            headers['user-agent'] = self.user_agent
        
        if 'sec-ch-ua-platform' in headers:
            headers['sec-ch-ua-platform'] = self.client_hints['sec-ch-ua-platform']
        else:
            headers['Sec-Ch-Ua-Platform'] = self.client_hints['sec-ch-ua-platform']

        if 'sec-ch-ua' in headers:
            headers['sec-ch-ua'] = self.client_hints['sec-ch-ua']
        else:
            headers['Sec-Ch-Ua'] = self.client_hints['sec-ch-ua']
        
        for key, value in headers.items():
            processed_headers.append(key, value)
                
        return processed_headers
    
    def set_headers_order(self, headers: Union[Dict[str, str], rnet.HeaderMap]):
        """
        请求头排序
        :param headers: 用户传入的请求头
        :return
        """
        if isinstance(headers, rnet.HeaderMap):
            headers_order = [k.decode() for k, _ in headers.items()][::-1]
        else:
            headers_order = list(headers.keys())
        
        if self._chrome_version > 130:
            # cookie 在 priority 前面
            if 'priority' in headers_order and 'cookie' in headers_order:
                priority_idx = headers_order.index('priority')
                cookie_idx = headers_order.index('cookie')
                
                if cookie_idx > priority_idx:        
                    headers_order[priority_idx] = 'cookie'
                    headers_order[cookie_idx] = 'priority'
        
        self._session.update(headers_order=headers_order)

    def _process_get_arguments(self, **kwargs):
        if kwargs.get("params"):
            kwargs["query"] = []
            for k, v in kwargs["params"].items():
                kwargs['query'].append((k, v))

        headers = kwargs.get('headers') or {}
        
        # 补全请求头
        headers = self.complete_headers(headers)
        
        # 请求头排序
        self.set_headers_order(headers)

        kwargs['headers'] = headers
        
        return {**kwargs}

    def _process_post_arguments(self, **kwargs):
        headers = kwargs.get('headers') or {}
            
        if kwargs.get("params"):
            kwargs["query"] = []
            for k, v in kwargs["params"].items():
                kwargs['query'].append((k, v))
            del kwargs["params"]

        if kwargs.get("data"):
            kwargs["body"] = urlencode(kwargs["data"]).encode()
            del kwargs["data"]
            
            if isinstance(headers, dict):
                if 'Content-Type' in headers:
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
                else:
                    headers['content-type'] = 'application/x-www-form-urlencoded'
            elif isinstance(headers, list):
                if any([header.lower().startswith('content-type') for header in headers]) == 0:
                    headers.append('content-type: application/x-www-form-urlencoded')
                        
        if kwargs.get('json'):
            kwargs["body"] = json.dumps(kwargs["json"], separators=(",", ":")).encode()
            del kwargs["json"]

            if isinstance(headers, dict):
                if 'Content-Type' in headers:
                    headers['Content-Type'] = 'application/json'
                else:
                    headers['content-type'] = 'application/json'
            elif isinstance(headers, list):
                if any([header.lower().startswith('content-type') for header in headers]) == 0:
                    headers.append('content-type: application/json')
                        
        if kwargs.get("body"):
            content_length = str(len(kwargs['body']))
            
            if isinstance(headers, dict):
                if 'Content-Length' in headers:
                    headers['Content-Length'] = content_length
                else:
                    headers["content-length"] = content_length
            else:
                if any([header.lower().startswith('content-length') for header in headers]) == 0:
                    headers.insert(0, f'content-length: {content_length}')
        
        # 补全请求头
        headers = self.complete_headers(headers)
        
        # 请求头排序
        self.set_headers_order(headers)

        kwargs['headers'] = headers
        
        return {**kwargs}
    
    def get(self, url: str, *args, **kwargs) -> Response:
        resp = Response(self._session.get(url, *args, **self._process_get_arguments(**kwargs)))
        self.cookies.update(resp.cookies)
        return resp
    
    def post(self, url: str, *args, **kwargs) -> Response:
        # 发起请求
        resp = Response(self._session.post(url, *args, **self._process_post_arguments(**kwargs)))
        self.cookies.update(resp.cookies)
        return resp


class AsyncSession(Session):

    def __init__(
        self,
        user_agent: Union[int, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
        cookies: Optional[Dict[str, str]] = None, proxy: Optional[str] = None, ipinfo: dict = {}, timeout: int = 15,
        allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None
    ):
        super().__init__(
            user_agent=user_agent, cookies=cookies, proxy=proxy, ipinfo=ipinfo, timeout=timeout,
            allow_redirects=allow_redirects, verify=verify, http_version=http_version, sync=False
        )
        
    async def __aenter__(self):
        return self

    def __enter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __await__(self):
        return self
    
    async def update_ipinfo(self):
        try:
            resp = await (await self._session.get("https://ipinfo.io/json", headers={
                "user-agent": self.user_agent,
            }, timeout=5)).json()
            self.ipinfo.update({
                "country": resp["country"].lower(),
                "ip": resp.get("ip"),
                "timezone": resp.get("timezone"),
                "geolocation": resp.get("loc")
            })
            self.client_hints['accept-language'] = ACCEPT_LANGUAGE_MAP.get(self.ipinfo["country"], 'zh-CN,zh;q=0.9')
        except:
            pass

    async def get(self, url: str, *args, **kwargs) -> Response:
        resp = Response(await self._session.get(url, *args, **self._process_get_arguments(**kwargs)))
        self.cookies.update(resp.cookies)
        return resp

    async def post(self, url: str, *args, **kwargs) -> Response:
        resp = Response(await self._session.post(url, *args, **self._process_post_arguments(**kwargs)))
        self.cookies.update(resp.cookies)
        return resp
