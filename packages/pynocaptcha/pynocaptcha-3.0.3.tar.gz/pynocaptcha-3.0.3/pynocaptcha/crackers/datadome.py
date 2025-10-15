# -*- coding: UTF-8 -*-

import re
import sys

from typing import Optional, List, Dict, Any, Tuple, Union

if sys.version_info >= (3, 8):  # pragma: no cover (py38+)
    from typing import Literal
else:  # pragma: no cover (py38+)
    from typing_extensions import Literal

import json
from loguru import logger
from curl_cffi import requests

from ..magneto.session import Session, AsyncSession
from ..magneto.response import Response


def crack_datadome(
    user_token: str, href: str, interstitial: bool = False,
    js_url: Optional[str] = None, js_key: Optional[str] = None, 
    parse_index: Optional[callable] = None, verifiers: List[callable] = [], max_retry_times: int = 2, 
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[Session] = None, cookies: Dict[str, str] = {}, proxy: Optional[str] = None,
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[Session, Response, Dict[str, Any]]:    
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

    if interstitial:
        html = parse_index is None

        nocaptcha_resp = requests.post(
            f'http://{nocaptcha_host}/api/wanda/datadome/universal', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json={
                'is_auth': auth,
                "branch": branch,
                "href": href,
                "interstitial": interstitial,
                "html": html,
                "user_agent": user_agent,
                "proxy": proxy,
                **session.ipinfo,
            }
        ).json()
        if debug:
            logger.debug(nocaptcha_resp)

        if nocaptcha_resp["status"]:
            extra = nocaptcha_resp["extra"]
            session.cookies.update(nocaptcha_resp["data"])
        else:
            raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
    else:
        headers = {
            'sec-ch-ua': session.client_hints['sec-ch-ua'], 
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 
            'upgrade-insecure-requests': '1', 
            'sec-ch-ua-mobile': '?0', 
            'user-agent': user_agent, 
            'sec-ch-ua-platform': session.client_hints['sec-ch-ua-platform'],
            'Sec-Fetch-Site': 'none', 
            'Sec-Fetch-Mode': 'navigate', 
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': session.client_hints['accept-language'], 
            'priority': 'u=0, i'
        }

        resp = session.get(href, headers=headers)
        html = resp.text
        
        retry_times = 0
        while resp.status_code in [403, 405] and retry_times < max_retry_times:
            try:
                dd_match = re.search(r'var dd=(\{.*?\})', html)
                captcha = json.loads(dd_match[1].replace("'", '"'))
                if captcha.get("t") == "bv":
                    raise Warning("代理被封锁, 请切换代理重试")
            except:
                raise Warning(f"验证异常: {resp.status_code} {html}")

            if debug:
                logger.debug(f'触发验证码: {html}')
            
            datadome = resp.cookies.get('datadome')

            nocaptcha_resp = requests.post(
                f'http://{nocaptcha_host}/api/wanda/datadome/universal', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    "branch": branch,
                    "href": href,
                    "captcha_html": html,
                    "cookies": {
                        'datadome': datadome
                    },
                    "html": html,
                    "user_agent": user_agent,
                    "proxy": proxy,
                    **session.ipinfo,
                }
            ).json()
            if debug:
                logger.debug(nocaptcha_resp)
            
            if nocaptcha_resp["status"]:
                extra = nocaptcha_resp["extra"]
                session.cookies.update(nocaptcha_resp["data"])
                if parse_index:
                    resp = session.get(href, headers=headers)
                    retry_times += 1
                else:
                    break            
            else:
                raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
            
        if retry_times == 0 and js_url and js_key:
            datadome = session.cookies.get('datadome')
            _cookies = None
            if datadome:
                _cookies = {
                    "datadome": datadome
                }
            
            nocaptcha_resp = requests.post(
                f'http://{nocaptcha_host}/api/wanda/datadome/universal', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    "branch": branch,
                    "href": href,
                    "js_url": js_url,
                    "js_key": js_key,
                    "cookies": _cookies,
                    "user_agent": user_agent,
                    "proxy": proxy,
                    **session.ipinfo,
                }
            ).json()
            if debug:
                logger.debug(nocaptcha_resp)
                
            if nocaptcha_resp["status"]:
                extra.update(nocaptcha_resp['extra'])
                session.cookies.update(nocaptcha_resp['data'])
            else:
                raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
    
    if parse_index:
        if interstitial:
            parse_index(extra["html"])
        else:
            parse_index(resp, extra)
    
    for verifier in verifiers:
        
        retry_times = 0
        
        resp = verifier(session, extra)

        while resp.status_code in [403, 405] and retry_times < max_retry_times:
            did = extra.get("did")
            
            datadome = session.cookies["datadome"]
            
            captcha_args = {}
            try:
                captcha_url = resp.json()["url"]
                if 't=bv' in captcha_url:
                    raise Warning("代理被封锁, 请切换代理重试")
                captcha_args["captcha_url"] = captcha_url
            except Warning as e:
                raise e
            except:
                captcha_html = resp.text
                try:
                    dd_match = re.search(r'var dd=(\{.*?\})', captcha_html)
                    captcha = json.loads(dd_match[1].replace("'", '"'))
                    if captcha.get("t") == "bv":
                        raise Warning("代理被封锁, 请切换代理重试")
                except:
                    raise Warning("验证异常: " + captcha_html)
                
                captcha_args["captcha_html"] = captcha_html
            
            if debug:
                logger.debug(f'触发验证码: {captcha_args}')
                
            nocaptcha_resp = requests.post(
                f'http://{nocaptcha_host}/api/wanda/datadome/universal', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    "branch": branch,
                    "href": href,
                    **captcha_args,
                    "did": did,
                    "cookies": {
                        "datadome": datadome
                    },
                    "user_agent": user_agent,
                    "proxy": proxy,
                    **session.ipinfo,
                }
            ).json()
            if debug:
                logger.debug(nocaptcha_resp)
                
            if nocaptcha_resp["status"]:
                session.cookies.update(nocaptcha_resp['data'])
                resp = verifier(session, extra)
            else:
                raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
            
            retry_times += 1

    return session, resp, extra


async def async_crack_datadome(
    user_token: str, href: str, interstitial: bool = False,
    js_url: Optional[str] = None, js_key: Optional[str] = None, 
    parse_index: Optional[callable] = None, verifiers: List[callable] = [], max_retry_times: int = 2, 
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[AsyncSession] = None, cookies: Dict[str, str] = {}, proxy: Optional[str] = None,
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[AsyncSession, Response, Dict[str, Any]]:    
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
        resp = None
        if interstitial:
            html = parse_index is None

            nocaptcha_resp = (await _session.post(
                f'http://{nocaptcha_host}/api/wanda/datadome/universal', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    "branch": branch,
                    "href": href,
                    "interstitial": interstitial,
                    "html": html,
                    "user_agent": user_agent,
                    "proxy": proxy,
                    **session.ipinfo,
                }
            )).json()
            if debug:
                logger.debug(nocaptcha_resp)

            if nocaptcha_resp["status"]:
                extra = nocaptcha_resp["extra"]
                session.cookies.update(nocaptcha_resp["data"])
            else:
                raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
        else:
            headers = {
                'sec-ch-ua': session.client_hints['sec-ch-ua'], 
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 
                'upgrade-insecure-requests': '1', 
                'sec-ch-ua-mobile': '?0', 
                'user-agent': user_agent, 
                'sec-ch-ua-platform': session.client_hints['sec-ch-ua-platform'],
                'Sec-Fetch-Site': 'none', 
                'Sec-Fetch-Mode': 'navigate', 
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': session.client_hints['accept-language'], 
                'priority': 'u=0, i'
            }

            resp = await session.get(href, headers=headers)
            html = await resp.async_text()
            
            retry_times = 0
            while resp.status_code in [403, 405] and retry_times < max_retry_times:
                try:
                    dd_match = re.search(r'var dd=(\{.*?\})', html)
                    captcha = json.loads(dd_match[1].replace("'", '"'))
                    if captcha.get("t") == "bv":
                        raise Warning("代理被封锁, 请切换代理重试")
                except:
                    raise Warning(f"验证异常: {resp.status_code} {html}")

                if debug:
                    logger.debug(f'触发验证码: {html}')
                
                datadome = resp.cookies.get('datadome')

                nocaptcha_resp = (await _session.post(
                    f'http://{nocaptcha_host}/api/wanda/datadome/universal', headers={
                        'user-token': user_token,
                        **({ "Developer-Id": developer_id } if developer_id else {})
                    }, json={
                        'is_auth': auth,
                        "branch": branch,
                        "href": href,
                        "captcha_html": html,
                        "cookies": {
                            'datadome': datadome
                        },
                        "html": html,
                        "user_agent": user_agent,
                        "proxy": proxy,
                        **session.ipinfo,
                    }
                )).json()
                if debug:
                    logger.debug(nocaptcha_resp)
                
                if nocaptcha_resp["status"]:
                    extra = nocaptcha_resp["extra"]
                    session.cookies.update(nocaptcha_resp["data"])
                    if parse_index:
                        resp = await session.get(href, headers=headers)
                        retry_times += 1
                    else:
                        break            
                else:
                    raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
                
            if retry_times == 0 and js_url and js_key:
                datadome = session.cookies.get('datadome')
                _cookies = None
                if datadome:
                    _cookies = {
                        "datadome": datadome
                    }
                
                nocaptcha_resp = (await _session.post(
                    f'http://{nocaptcha_host}/api/wanda/datadome/universal', headers={
                        'user-token': user_token,
                        **({ "Developer-Id": developer_id } if developer_id else {})
                    }, json={
                        'is_auth': auth,
                        "branch": branch,
                        "href": href,
                        "js_url": js_url,
                        "js_key": js_key,
                        "cookies": _cookies,
                        "user_agent": user_agent,
                        "proxy": proxy,
                        **session.ipinfo,
                    }
                )).json()
                if debug:
                    logger.debug(nocaptcha_resp)
                    
                if nocaptcha_resp["status"]:
                    extra.update(nocaptcha_resp['extra'])
                    session.cookies.update(nocaptcha_resp['data'])
                else:
                    raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
        
        if parse_index:
            if interstitial:
                parse_index(extra)
            else:
                await parse_index(resp, extra)
        
        for verifier in verifiers:
            
            retry_times = 0
            
            resp = await verifier(session, extra)

            while resp.status_code in [403, 405] and retry_times < max_retry_times:
                did = extra.get("did")
                
                datadome = session.cookies["datadome"]
                
                captcha_args = {}
                try:
                    captcha_url = (await resp.async_json())["url"]
                    if 't=bv' in captcha_url:
                        raise Warning("代理被封锁, 请切换代理重试")
                    captcha_args["captcha_url"] = captcha_url
                except Warning as e:
                    raise e
                except:
                    captcha_html = await resp.async_text()
                    try:
                        dd_match = re.search(r'var dd=(\{.*?\})', captcha_html)
                        captcha = json.loads(dd_match[1].replace("'", '"'))
                        if captcha.get("t") == "bv":
                            raise Warning("代理被封锁, 请切换代理重试")
                    except:
                        raise Warning("验证异常: " + captcha_html)
                    
                    captcha_args["captcha_html"] = captcha_html
                
                if debug:
                    logger.debug(f'触发验证码: {captcha_args}')
                    
                nocaptcha_resp = (await _session.post(
                    f'http://{nocaptcha_host}/api/wanda/datadome/universal', headers={
                        'user-token': user_token,
                        **({ "Developer-Id": developer_id } if developer_id else {})
                    }, json={
                        'is_auth': auth,
                        "branch": branch,
                        "href": href,
                        **captcha_args,
                        "did": did,
                        "cookies": {
                            "datadome": datadome
                        },
                        "user_agent": user_agent,
                        "proxy": proxy,
                        **session.ipinfo,
                    }
                )).json()
                if debug:
                    logger.debug(nocaptcha_resp)
                    
                if nocaptcha_resp["status"]:
                    session.cookies.update(nocaptcha_resp['data'])
                    resp = await verifier(session, extra)
                else:
                    raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
                
                retry_times += 1

        return session, resp, extra
