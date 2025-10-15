# -*- coding: utf-8 -*-

from typing import Dict, Any, Union

import rnet
from json import loads


class Response():
    
    def __init__(self, response: Union[rnet.BlockingResponse, rnet.Response]):
        self._response = response
        self._text: str = None
        self._headers: Dict[str, str] = None
        self._async = isinstance(response, rnet.Response)

    def __getattr__(self, name):
        """
        当访问 Response 没有定义的属性或方法时，尝试从 self._response 获取。
        这样可以支持 self._response 的所有方法和属性。
        """
        # 获取 self._response 的属性或方法
        attr = getattr(self._response, name)

        # 如果是方法，返回一个包装器以确保调用时正确传递参数
        if callable(attr):
            def wrapper(*args, **kwargs):
                return attr(*args, **kwargs)
            return wrapper
        else:
            return attr
        
    @property
    def status_code(self) -> int:
        return self._response.status_code.as_int()
        
    @property
    def cookies(self) -> Dict[str, str]:
        return {
            cookie.name: cookie.value for cookie in self._response.cookies
        }
    
    @property
    def headers(self) -> Dict[str, str]:
        if self._headers is None:
            self._headers = {}
            for header_key, header_value in self._response.headers.items():
                self._headers[header_key.decode()] = header_value.decode()
        return self._headers
    
    @property
    def text(self) -> str:
        if self._text is None:
            if self._async:
                raise Exception("Using async_text instead")
            else:
                self._text = self._response.text()
                self._response.close()
        return self._text

    async def async_text(self) -> str:
        if self._text is None:
            if not self._async:
                self._text = self._response.text()
                self._response.close()
            else:
                try:
                    self._text = await self._response.text()
                finally:
                    await self._response.close()
        return self._text

    def json(self) -> Dict[str, Any]:
        return loads(self.text)

    async def async_json(self) -> Dict[str, Any]:
        await self.async_text()
        return self.json()
