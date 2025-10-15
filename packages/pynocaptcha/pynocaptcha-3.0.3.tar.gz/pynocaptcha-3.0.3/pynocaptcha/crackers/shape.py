# -*- coding: UTF-8 -*-

import sys

from typing import Optional, Literal, Union, Tuple, Dict, List, Any

if sys.version_info >= (3, 8):  # pragma: no cover (py38+)
    from typing import Literal
else:  # pragma: no cover (py38+)
    from typing_extensions import Literal

import re
import json
from loguru import logger
from curl_cffi import requests

from ..magneto.response import Response
from ..magneto.session import Session, AsyncSession


def crack_shape_v1(
    user_token: str, href: str, proxy: Optional[str] = None,
    script_url: Optional[str] = None, script_regexp: Optional[str] = None, 
    vmp_url: Optional[str] = None, vmp_regexp: Optional[str] = None, fast: bool = False,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[Session] = None, cookies: Dict[str, str] = {},
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[Session, Dict[str, str], Dict[str, Any]]:   
    if not session:
        session = Session(
            user_agent=user_agent, 
            proxy=proxy, 
            ipinfo=ipinfo, 
            cookies=cookies, 
            timeout=timeout, 
            allow_redirects=allow_redirects, 
            verify=verify, 
            http_version=http_version
        )
        if not ipinfo:
            session.update_ipinfo()

    if not extra:
        extra.update(session.client_hints)
        
    user_agent = session.user_agent
    proxy = session.proxy
    
    domain = href.split("/")[2]
    nocaptcha_host = "api.nocaptcha.cn" if internal_host else "api.nocaptcha.io"
    if not script_url:
        data = {
            "method": "read",
            "key": domain,
        }
        site_arg = requests.post(
            f"http://{nocaptcha_host}/api/wanda/shape/p",
            json=data
        ).text
        
        if site_arg:
            site_arg = json.loads(site_arg)
            script_url = site_arg.get("script_url")
            vmp_url = site_arg.get("vmp_url")
            vmp_regexp = site_arg.get("vmp_regexp")
    
    origin = "/".join(href.split("/")[0:3])

    if not script_url:
        headers = [
            f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
            "sec-ch-ua-mobile: ?0",
            f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
            "upgrade-insecure-requests: 1",
            f"user-agent: {user_agent}",
            "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-site: none",
            "sec-fetch-mode: navigate",
            "sec-fetch-user: ?1",
            "sec-fetch-dest: document",
            "accept-encoding: gzip, deflate, br, zstd",
            f"accept-language: {session.client_hints['accept-language']}",
            "priority: u=0, i"
        ]
        if script_regexp:
            headers = [
                f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                f"user-agent: {user_agent}",
                f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                "sec-ch-ua-mobile: ?0",
                "accept: */*",
                "sec-fetch-site: same-origin",
                "sec-fetch-mode: no-cors",
                "sec-fetch-dest: script",
                f"referer: {href}",
                "accept-encoding: gzip, deflate, br, zstd",
                f"accept-language: {session.client_hints['accept-language']}",
                "priority: u=1"
            ]
            html = session.get(href, headers=headers).text
            script_url = re.findall(script_regexp, html)[1]
                
    if not script_url.startswith('http'):
        script_url = origin + script_url
    
    try:
        headers = [
            f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
            f"user-agent: {user_agent}",
            f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
            "sec-ch-ua-mobile: ?0",
            "accept: */*",
            "sec-fetch-site: same-origin",
            "sec-fetch-mode: no-cors",
            "sec-fetch-dest: script",
            f"referer: {href}",
            "accept-encoding: gzip, deflate, br, zstd",
            f"accept-language: {session.client_hints['accept-language']}",
            "priority: u=1"
        ]
        resp = session.get(script_url, headers=headers)
        if resp.status_code != 200:
            raise Warning(f"初始脚本状态码异常: {resp.status_code}")
        script = resp.text
        if script == "fail":
            raise Warning("初始脚本获取异常")
    except Warning as e:
        raise e
    except:
        raise Warning("初始脚本获取失败")
    
    if not vmp_url:
        if vmp_regexp:
            try:
                vmp_url = re.search(vmp_regexp, script)[1]
            except:
                raise Warning('vmp 地址获取失败')
    
    vmp_script = None
    if vmp_url:
        if not vmp_url.startswith("http"):
            vmp_url = origin + vmp_url
        try:
            vmp_resp = session.get(vmp_url, headers=headers)
            if vmp_resp.status_code != 200:
                raise Warning("vmp 脚本请求失败")
            
            vmp_script = vmp_resp.text
        except:
            raise Warning("vmp 获取失败")
    
    nocaptcha_resp = requests.post(
        f'http://{nocaptcha_host}/api/wanda/shape/v1', headers={
            'user-token': user_token,
            **({ "Developer-Id": developer_id } if developer_id else {})
        }, json={
            'is_auth': auth,
            "branch": branch,
            "href": href,
            "script_url": script_url,
            "script_content": script,
            "vmp_url": vmp_url,
            "vmp_content": vmp_script,
            "user_agent": user_agent,
            **session.ipinfo,
            "fast": fast,
            "cookies": session.cookies,
        }
    ).json()
    if debug:
        logger.debug(nocaptcha_resp)
    if nocaptcha_resp["status"]:
        extra.update(nocaptcha_resp["extra"])
        shape_headers = nocaptcha_resp["data"]
        return session, shape_headers, extra
    else:
        raise Warning(f'计算失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')


async def async_crack_shape_v1(
    user_token: str, href: str, proxy: Optional[str] = None,
    script_url: Optional[str] = None, script_regexp: Optional[str] = None,
    vmp_url: Optional[str] = None, vmp_regexp: Optional[str] = None, fast: bool = False,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[AsyncSession] = None, cookies: Dict[str, str] = {},
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[AsyncSession, Dict[str, str], Dict[str, Any]]:    
    if not session:
        session = AsyncSession(
            user_agent=user_agent, 
            proxy=proxy, 
            ipinfo=ipinfo, 
            cookies=cookies, 
            timeout=timeout, 
            allow_redirects=allow_redirects, 
            verify=verify, 
            http_version=http_version
        )
        if not ipinfo:
            await session.update_ipinfo()

    if not extra:
        extra.update(session.client_hints)
        
    user_agent = session.user_agent
    proxy = session.proxy
    
    nocaptcha_host = "api.nocaptcha.cn" if internal_host else "api.nocaptcha.io"
    domain = href.split("/")[2]
    async with requests.AsyncSession() as _session:
        if not script_url:
            data = {
                "method": "read",
                "key": domain,
            }
            site_arg = (await _session.post(
                f"http://{nocaptcha_host}/api/wanda/shape/p",
                json=data
            )).text
            
            if site_arg:
                site_arg = json.loads(site_arg)
                script_url = site_arg.get("script_url")
                vmp_url = site_arg.get("vmp_url")
                vmp_regexp = site_arg.get("vmp_regexp")
        
        origin = "/".join(href.split("/")[0:3])

        if not script_url:
            headers = [
                f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                "sec-ch-ua-mobile: ?0",
                f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                "upgrade-insecure-requests: 1",
                f"user-agent: {user_agent}",
                "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-fetch-site: none",
                "sec-fetch-mode: navigate",
                "sec-fetch-user: ?1",
                "sec-fetch-dest: document",
                "accept-encoding: gzip, deflate, br, zstd",
                f"accept-language: {session.client_hints['accept-language']}",
                "priority: u=0, i"
            ]
            if script_regexp:
                headers = [
                    f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                    f"user-agent: {user_agent}",
                    f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                    "sec-ch-ua-mobile: ?0",
                    "accept: */*",
                    "sec-fetch-site: same-origin",
                    "sec-fetch-mode: no-cors",
                    "sec-fetch-dest: script",
                    f"referer: {href}",
                    "accept-encoding: gzip, deflate, br, zstd",
                    f"accept-language: {session.client_hints['accept-language']}",
                    "priority: u=1"
                ]
                resp = await session.get(href, headers=headers)
                script_url = re.findall(script_regexp, await resp.async_text())[1]
                  
        if not script_url.startswith('http'):
            script_url = origin + script_url
        
        try:
            headers = [
                f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                f"user-agent: {user_agent}",
                f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                "sec-ch-ua-mobile: ?0",
                "accept: */*",
                "sec-fetch-site: same-origin",
                "sec-fetch-mode: no-cors",
                "sec-fetch-dest: script",
                f"referer: {href}",
                "accept-encoding: gzip, deflate, br, zstd",
                f"accept-language: {session.client_hints['accept-language']}",
                "priority: u=1"
            ]
            resp = await session.get(script_url, headers=headers)
            if resp.status_code != 200:
                raise Warning(f"初始脚本状态码异常: {resp.status_code}")
            script = await resp.async_text()
            if script == "fail":
                raise Warning("初始脚本获取异常")
        except Warning as e:
            raise e
        except:
            raise Warning("初始脚本获取失败")
        
        if not vmp_url:
            if vmp_regexp:
                try:
                    vmp_url = re.search(vmp_regexp, script)[1]
                except:
                    raise Warning('vmp 地址获取失败')
        
        vmp_script = None
        if vmp_url:
            if not vmp_url.startswith("http"):
                vmp_url = origin + vmp_url
            try:
                vmp_resp = await session.get(vmp_url, headers=headers)
                if vmp_resp.status_code != 200:
                    raise Warning("vmp 脚本请求失败")
                
                vmp_script = await vmp_resp.async_text()
            except:
                raise Warning("vmp 获取失败")
        
        nocaptcha_resp = (await _session.post(
            f'http://{nocaptcha_host}/api/wanda/shape/v1', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json={
                'is_auth': auth,
                "branch": branch,
                "href": href,
                "script_url": script_url,
                "script_content": script,
                "vmp_url": vmp_url,
                "vmp_content": vmp_script,
                "user_agent": user_agent,
                **session.ipinfo,
                "fast": fast,
                "cookies": session.cookies,
            }
        )).json()
        if debug:
            logger.debug(nocaptcha_resp)
        if nocaptcha_resp["status"]:
            extra.update(nocaptcha_resp["extra"])
            shape_headers = nocaptcha_resp["data"]
            return session, shape_headers, extra
        else:
            raise Warning(f'计算失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')


def crack_shape_v2(
    user_token: str, href: str, pkey: Optional[str] = None, proxy: Optional[str] = None, request: Optional[Dict[str, str]] = None,
    script_url: Optional[str] = None, script_regexp: Optional[str] = None, vmp_url: Optional[str] = None, vmp_regexp: Optional[str] = None, 
    fast: bool = False, action: Optional[str] = None,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[Session] = None, cookies: Dict[str, str] = {},
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[Session, Union[Dict[str, str], Response], Dict[str, Any]]: 
    if not session:
        session = Session(
            user_agent=user_agent, 
            proxy=proxy, 
            ipinfo=ipinfo, 
            cookies=cookies, 
            timeout=timeout, 
            allow_redirects=allow_redirects, 
            verify=verify, 
            http_version=http_version
        )
        if not ipinfo:
            session.update_ipinfo()

    if not extra:
        extra.update(session.client_hints)
        
    user_agent = session.user_agent
    proxy = session.proxy
    
    nocaptcha_host = "api.nocaptcha.cn" if internal_host else "api.nocaptcha.io"

    origin = "/".join(href.split("/")[0:3])

    headers = [
        f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
        "sec-ch-ua-mobile: ?0",
        f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
        "upgrade-insecure-requests: 1",
        f"user-agent: {user_agent}",
        "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "sec-fetch-site: none",
        "sec-fetch-mode: navigate",
        "sec-fetch-user: ?1",
        "sec-fetch-dest: document",
        "accept-encoding: gzip, deflate, br, zstd",
        f"accept-language: {session.client_hints['accept-language']}",
        "priority: u=0, i"
    ]
    resp = session.get(href, headers=headers)
    html = resp.text
    
    if pkey:
        if not script_url:
            data = {
                "method": "read",
                "key": pkey.lower(),
            }
            site_arg = requests.post(
                f"http://{nocaptcha_host}/api/wanda/shape/p",
                json=data
            ).text
            
            if site_arg:
                site_arg = json.loads(site_arg)
                script_url = site_arg.get("script_url")
                vmp_url = site_arg.get("vmp_url")
                vmp_regexp = site_arg.get("vmp_regexp")
                if not request:
                    request = site_arg.get("request")
        
        if script_regexp:
            script_url = re.findall(script_regexp, html)[1]
                    
        if not script_url.startswith('http'):
            script_url = origin + script_url
        
        try:
            headers = [
                f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                f"user-agent: {user_agent}",
                f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                "sec-ch-ua-mobile: ?0",
                "accept: */*",
                "sec-fetch-site: same-origin",
                "sec-fetch-mode: no-cors",
                "sec-fetch-dest: script",
                f"referer: {href}",
                "accept-encoding: gzip, deflate, br, zstd",
                f"accept-language: {session.client_hints['accept-language']}",
                "priority: u=1"
            ]
            resp = session.get(script_url, headers=headers)
            if resp.status_code != 200:
                raise Warning(f"初始脚本状态码异常: {resp.status_code}")
            script = resp.text
            if script == "fail":
                raise Warning("初始脚本获取异常")
        except Warning as e:
            raise e
        except:
            raise Warning("初始脚本获取失败")
        
        if not vmp_url:
            if vmp_regexp:
                try:
                    vmp_url = re.search(vmp_regexp, script)[1]
                except:
                    raise Warning('vmp 地址获取失败')
        
        vmp_script = None
        if vmp_url:
            if not vmp_url.startswith("http"):
                vmp_url = origin + vmp_url
            try:
                vmp_resp = session.get(vmp_url, headers=headers)
                if vmp_resp.status_code != 200:
                    raise Warning("vmp 脚本请求失败")
                
                vmp_script = vmp_resp.text
            except:
                raise Warning("vmp 获取失败")
        
        nocaptcha_resp = requests.post(
            f'http://{nocaptcha_host}/api/wanda/shape/v2', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json={
                'is_auth': auth,
                "branch": branch,
                "href": href,
                "pkey": pkey,
                "request": request,
                "script_url": script_url,
                "script_content": script,
                "vmp_url": vmp_url,
                "vmp_content": vmp_script,
                "user_agent": user_agent,
                **session.ipinfo,
                "fast": fast,
                "cookies": session.cookies,
                "action": action,
            }
        ).json()
    
    else:
        if 'ISTL-REDIRECT-TO' in html:
            nocaptcha_resp = requests.post(
                f'http://{nocaptcha_host}/api/wanda/shape/v2', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    "branch": branch,
                    "href": href,
                    "html": html,
                    "user_agent": user_agent,
                    **session.ipinfo,
                    "fast": fast,
                    "cookies": session.cookies,
                }
            ).json()
        else:
            return session, resp, extra
        
    if debug:
        logger.debug(nocaptcha_resp)

    if nocaptcha_resp["status"]:
        extra.update(nocaptcha_resp["extra"])
        if isinstance(nocaptcha_resp["data"], list):
            shape_headers = nocaptcha_resp["data"][0]
        else:
            shape_headers = nocaptcha_resp["data"]['headers']
            
        return session, shape_headers, extra
    else:
        raise Warning(f'计算失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')


async def async_crack_shape_v2(
    user_token: str, href: str, pkey: Optional[str] = None, proxy: Optional[str] = None, request: Optional[Dict[str, str]] = None,
    script_url: Optional[str] = None, script_regexp: Optional[str] = None, vmp_url: Optional[str] = None, vmp_regexp: Optional[str] = None, 
    fast: bool = False, action: Optional[str] = None,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[AsyncSession] = None, cookies: Dict[str, str] = {},
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[AsyncSession, Union[Dict[str, str], Response], Dict[str, Any]]:    
    if not session:
        session = AsyncSession(
            user_agent=user_agent, 
            proxy=proxy, 
            ipinfo=ipinfo, 
            cookies=cookies, 
            timeout=timeout, 
            allow_redirects=allow_redirects, 
            verify=verify, 
            http_version=http_version
        )
        if not ipinfo:
            await session.update_ipinfo()

    if not extra:
        extra.update(session.client_hints)
        
    user_agent = session.user_agent
    proxy = session.proxy
    
    nocaptcha_host = "api.nocaptcha.cn" if internal_host else "api.nocaptcha.io"
    async with requests.AsyncSession() as _session:        
        origin = "/".join(href.split("/")[0:3])

        headers = [
            f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
            "sec-ch-ua-mobile: ?0",
            f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
            "upgrade-insecure-requests: 1",
            f"user-agent: {user_agent}",
            "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-site: none",
            "sec-fetch-mode: navigate",
            "sec-fetch-user: ?1",
            "sec-fetch-dest: document",
            "accept-encoding: gzip, deflate, br, zstd",
            f"accept-language: {session.client_hints['accept-language']}",
            "priority: u=0, i"
        ]
        resp = await session.get(href, headers=headers)
        html = await resp.async_text()
        
        if pkey:
            if not script_url:
                data = {
                    "method": "read",
                    "key": pkey.lower(),
                }
                site_arg = (await _session.post(
                    f"http://{nocaptcha_host}/api/wanda/shape/p",
                    json=data
                )).text
                
                if site_arg:
                    site_arg = json.loads(site_arg)
                    script_url = site_arg.get("script_url")
                    vmp_url = site_arg.get("vmp_url")
                    vmp_regexp = site_arg.get("vmp_regexp")
                    if not request:
                        request = site_arg.get("request")
            if script_regexp:
                script_url = re.findall(script_regexp, html)[1]
                
            if not script_url.startswith('http'):
                script_url = origin + script_url
            
            try:
                headers = [
                    f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                    f"user-agent: {user_agent}",
                    f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                    "sec-ch-ua-mobile: ?0",
                    "accept: */*",
                    "sec-fetch-site: same-origin",
                    "sec-fetch-mode: no-cors",
                    "sec-fetch-dest: script",
                    f"referer: {href}",
                    "accept-encoding: gzip, deflate, br, zstd",
                    f"accept-language: {session.client_hints['accept-language']}",
                    "priority: u=1"
                ]
                resp = await session.get(script_url, headers=headers)
                if resp.status_code != 200:
                    raise Warning(f"初始脚本状态码异常: {resp.status_code}")
                script = await resp.async_text()
                if script == "fail":
                    raise Warning("初始脚本获取异常")
            except Warning as e:
                raise e
            except:
                raise Warning("初始脚本获取失败")
            
            if not vmp_url:
                if vmp_regexp:
                    try:
                        vmp_url = re.search(vmp_regexp, script)[1]
                    except:
                        raise Warning('vmp 地址获取失败')
            
            vmp_script = None
            if vmp_url:
                if not vmp_url.startswith("http"):
                    vmp_url = origin + vmp_url
                try:
                    vmp_resp = await session.get(vmp_url, headers=headers)
                    if vmp_resp.status_code != 200:
                        raise Warning("vmp 脚本请求失败")
                    
                    vmp_script = await vmp_resp.async_text()
                except:
                    raise Warning("vmp 获取失败")
            
            nocaptcha_resp = (await _session.post(
                f'http://{nocaptcha_host}/api/wanda/shape/v2', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    "branch": branch,
                    "href": href,
                    "pkey": pkey,
                    "request": request,
                    "script_url": script_url,
                    "script_content": script,
                    "vmp_url": vmp_url,
                    "vmp_content": vmp_script,
                    "user_agent": user_agent,
                    **session.ipinfo,
                    "fast": fast,
                    "cookies": session.cookies,
                    "action": action,
                }
            )).json()
        else:
            if 'ISTL-REDIRECT-TO' in html:
                nocaptcha_resp = (await _session.post(
                    f'http://{nocaptcha_host}/api/wanda/shape/v2', headers={
                        'user-token': user_token,
                        **({ "Developer-Id": developer_id } if developer_id else {})
                    }, json={
                        'is_auth': auth,
                        "branch": branch,
                        "href": href,
                        "html": html,
                        "user_agent": user_agent,
                        **session.ipinfo,
                        "fast": fast,
                        "cookies": session.cookies,
                    }
                )).json()
            else:
                return session, resp, extra
        
        if debug:
            logger.debug(nocaptcha_resp)
        if nocaptcha_resp["status"]:
            extra.update(nocaptcha_resp["extra"])
            if isinstance(nocaptcha_resp["data"], list):
                shape_headers = nocaptcha_resp["data"][0]
            else:
                shape_headers = nocaptcha_resp["data"]['headers']
            return session, shape_headers, extra
        else:
            raise Warning(f'计算失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
