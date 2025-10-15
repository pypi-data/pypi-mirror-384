# -*- coding: UTF-8 -*-

import sys

from typing import Optional, Literal, Union, Tuple, Dict, List, Any

if sys.version_info >= (3, 8):  # pragma: no cover (py38+)
    from typing import Literal
else:  # pragma: no cover (py38+)
    from typing_extensions import Literal

from loguru import logger
from curl_cffi import requests

from .base import BaseCracker
from ..magneto.session import AsyncSession, Session
from ..magneto.response import Response


class PerimeterxCracker(BaseCracker):
    
    cracker_name = "perimeterx"
    cracker_version = "universal"    

    """
    perimeterx cracker
    :param tag: px 版本号
    :param href: 触发 perimeterx 验证的页面地址
    :param captcha: 按压验证码参数, 示例: {
        appId: 'PXaOtQIWNf',
        jsClientSrc: '/aOtQIWNf/init.js',
        firstPartyEnabled: true,
        uuid: '013b4cad-ece3-11ee-a877-09542f9a30cf',
        hostUrl: '/aOtQIWNf/xhr',
        blockScript: '/aOtQIWNf/captcha/captcha.js?a=c&u=013b4cad-ece3-11ee-a877-09542f9a30cf&v=&m=0',
        altBlockScript: 'https://captcha.px-cloud.net/PXaOtQIWNf/captcha.js?a=c&u=013b4cad-ece3-11ee-a877-09542f9a30cf&v=&m=0',
        customLogo: 'https://chegg-mobile-promotions.cheggcdn.com/px/Chegg-logo-79X22.png'
    }
    :param user_agent: 请求流程使用 ua, 请使用 chrome 的 ua
    :param headers: 触发验证必须的 headers, 默认 {} 
    :param cookies: 触发验证必须的 cookies, 默认 {}
    :param timeout: 最大破解超时时间
    调用示例:
    cracker = CloudFlareCracker(
        href=href,
        user_token="xxx",
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["href"]
    # 默认可选参数
    option_params = {
        "branch": "Master",
        "tag": None,
        "app_id": None,
        "uuid": None,
        "vid": None,
        "modal": False,
        "press": False,
        "captcha": None,
        "captcha_html": None,
        "user_agent": None,
        "did": None,
        "proxy": None,
        "country": None,
        "ip": None,
        "timezone": None,
        "geolocation": None,
        "headers": {},
        "cookies": {},
        "actions": 1,
        "timeout": 30
    }


async def async_crack_perimeterx(
    user_token: str, href: str, app_id: str, press: bool = False, modal: bool = False, pow: bool = False,
    parse_index: Optional[callable] = None, verifiers: List[callable] = [], max_retry_times: int = 2,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[AsyncSession] = None, cookies: Dict[str, str] = {}, proxy: Optional[str] = None,
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[AsyncSession, Response, Dict[str, str]]:   
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
        
        retry_times = 0
        while resp.status_code == 403 and retry_times < max_retry_times:
            if debug:
                logger.debug("触发按压模式")
                
            nocaptcha_resp = (await _session.post(
                f'http://{nocaptcha_host}/api/wanda/perimeterx/universal', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    "branch": branch,
                    "href": href,
                    "app_id": app_id,
                    "captcha_html": await resp.async_text(),
                    "cookies": session.cookies,
                    "user_agent": user_agent,
                    "proxy": proxy,
                    **session.ipinfo,
                },
                timeout=120
            )).json()
            if debug:
                logger.debug(nocaptcha_resp)

            if nocaptcha_resp["status"]:
                extra.update(nocaptcha_resp["extra"])
                session.cookies.update(nocaptcha_resp["data"]['cookies'])
                if parse_index:
                    resp = await session.get(href, headers=headers)
                    retry_times += 1
                else:
                    break
            else:
                raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
        
        if retry_times == 0:
            nocaptcha_resp = (await _session.post(
                f'http://{nocaptcha_host}/api/wanda/perimeterx/universal', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    "branch": branch,
                    "href": href,
                    "app_id": app_id,
                    "press": press,
                    "modal": modal,
                    "pow": pow,
                    "cookies": session.cookies,
                    "user_agent": user_agent,
                    "proxy": proxy,
                    **session.ipinfo,
                },
                timeout=120
            )).json()
            if debug:
                logger.debug(nocaptcha_resp)

            if nocaptcha_resp["status"]:
                extra.update(nocaptcha_resp["extra"])
                session.cookies.update(nocaptcha_resp["data"]['cookies'])
            else:
                raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')

        if parse_index:
            await parse_index(resp, extra)
        
        for verifier in verifiers:            
            resp = await verifier(session, extra)
                
            retry_times = 0
            while resp.status_code == 403 and retry_times < max_retry_times:
                did = extra.get("did")
                _branch = extra.get("branch")
                if _branch:
                    branch = _branch
                    
                captcha_args = {}
                try:
                    captcha_args["captcha"] = await resp.async_json()
                except:
                    captcha_args["captcha_html"] = await resp.async_text()
                
                nocaptcha_resp = (await _session.post(
                    f'http://{nocaptcha_host}/api/wanda/perimeterx/universal', headers={
                        'user-token': user_token,
                        **({ "Developer-Id": developer_id } if developer_id else {})
                    }, json={
                        'is_auth': auth,
                        "branch": branch,
                        "href": href,
                        "app_id": app_id,
                        **captcha_args,
                        "did": did,
                        "cookies": session.cookies,
                        "user_agent": user_agent,
                        "proxy": proxy,
                        **session.ipinfo,
                    },
                    timeout=120
                )).json()
                if debug:
                    logger.debug(f'验证结果: {nocaptcha_resp}')
                
                if nocaptcha_resp["status"]:
                    extra.update(nocaptcha_resp["extra"])
                    session.cookies.update(nocaptcha_resp['data']['cookies'])
                    resp = await verifier(session, extra)
                else:
                    raise Warning(f'验证失败, id: {resp["id"]}, err: {resp["msg"]}')
                
                retry_times += 1

        return session, resp, extra


def crack_perimeterx(
    user_token: str, href: str, app_id: str, press: bool = False, modal: bool = False, pow: bool = False, 
    parse_index: Optional[callable] = None, verifiers: List[callable] = [], max_retry_times: int = 2,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[AsyncSession] = None, cookies: Dict[str, str] = {}, proxy: Optional[str] = None,
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[Session, Response, Dict[str, str]]:   
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
    
    retry_times = 0
    while resp.status_code == 403 and retry_times < max_retry_times:
        if debug:
            logger.debug("触发按压模式")
            
        nocaptcha_resp = requests.post(
            f'http://{nocaptcha_host}/api/wanda/perimeterx/universal', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json={
                'is_auth': auth,
                "branch": branch,
                "href": href,
                "app_id": app_id,
                "captcha_html": resp.text,
                "cookies": session.cookies,
                "user_agent": user_agent,
                "proxy": proxy,
                **session.ipinfo,
            },
            timeout=120
        ).json()
        if debug:
            logger.debug(nocaptcha_resp)

        if nocaptcha_resp["status"]:
            extra.update(nocaptcha_resp["extra"])
            session.cookies.update(nocaptcha_resp["data"]['cookies'])
            if parse_index:
                resp = session.get(href, headers=headers)
                retry_times += 1
            else:
                break
        else:
            raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
    
    if retry_times == 0:
        nocaptcha_resp = requests.post(
            f'http://{nocaptcha_host}/api/wanda/perimeterx/universal', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json={
                'is_auth': auth,
                "branch": branch,
                "href": href,
                "app_id": app_id,
                "press": press,
                "modal": modal,
                "pow": pow,
                "cookies": session.cookies,
                "user_agent": user_agent,
                "proxy": proxy,
                **session.ipinfo,
            },
            timeout=120
        ).json()
        if debug:
            logger.debug(nocaptcha_resp)

        if nocaptcha_resp["status"]:
            extra.update(nocaptcha_resp["extra"])
            session.cookies.update(nocaptcha_resp["data"]['cookies'])
        else:
            raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')

    if parse_index:
        parse_index(resp, extra)
    
    for verifier in verifiers:            
        resp = verifier(session, extra)
            
        retry_times = 0
        while resp.status_code == 403 and retry_times < max_retry_times:
            did = extra.get("did")
            _branch = extra.get("branch")
            if _branch:
                branch = _branch
                    
            captcha_args = {}
            try:
                captcha_args["captcha"] = resp.json()
            except:
                captcha_args["captcha_html"] = resp.text
            
            nocaptcha_resp = requests.post(
                f'http://{nocaptcha_host}/api/wanda/perimeterx/universal', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    "branch": branch,
                    "href": href,
                    "app_id": app_id,
                    **captcha_args,
                    "did": did,
                    "cookies": session.cookies,
                    "user_agent": user_agent,
                    "proxy": proxy,
                    **session.ipinfo,
                },
                timeout=120
            ).json()
            if debug:
                logger.debug(nocaptcha_resp)
            
            if nocaptcha_resp['status']:
                session.cookies.update(nocaptcha_resp['data']['cookies'])
                resp = verifier(session, extra)
            else:
                raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
            
            retry_times += 1

    return session, resp, extra
