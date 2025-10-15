# -*- coding: UTF-8 -*-

import sys
import re
from curl_cffi import requests
from loguru import logger

from typing import Optional, Literal, Union, Tuple, Dict, Any

if sys.version_info >= (3, 8):  # pragma: no cover (py38+)
    from typing import Literal
else:  # pragma: no cover (py38+)
    from typing_extensions import Literal

from .base import BaseCracker
from ..magneto.session import Session, AsyncSession

class AkamaiV2Cracker(BaseCracker):
    
    cracker_name = "akamai"
    cracker_version = "v2"    

    """
    akamai v2 cracker
    :param href: 触发验证的页面地址
    :param api: akamai 提交 sensor_data 的地址
    :param telemetry: 是否 headers 中的 telemetry 参数验证形式, 默认 false
    :param cookies: 请求 href 首页返回的 cookie _abck, bm_sz 值, 传了 api 参数必须传该值, 示例: { "value": "_abck=xxx; bm_sz=xxx", "uri": "https://example.com" }
    :param device: 请求流程使用的设备类型, 可选 pc/mobile, 默认 mobile
    调用示例:
    cracker = AkamaiV2Cracker(
        user_token="xxx",
        href="xxx",
        api="xxx",
        
        # debug=True,
        # proxy=proxy,
    )
    ret = cracker.crack()
    """
    
    # 必传参数
    must_check_params = ["href"]
    # 默认可选参数
    option_params = {
        "branch": "Master",
        "api": "",
        "telemetry": False,
        "uncheck": False,
        "sec_cpt_provider": None,
        "sec_cpt_script": None,
        "sec_cpt_key": None,
        "sec_cpt_challenge": {},
        "sec_cpt_host": None,
        "sec_cpt_html": None,
        "sec_cpt_duration": None,
        "sec_cpt_src": None,
        "sec_cpt_html": None,
        "proxy": None,
        "cookies": {},
        "country": None,
        "ip": None,
        "timezone": None,
        "geolocation": None,
        "user_agent": None,
        "timeout": 30
    }


async def async_crack_akamai_v3(
    user_token: str, requests_args: Dict[str, str], 
    other_requests: Optional[callable] = None, parse_index: Optional[str] = None, accept_language: Optional[str] = None,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[AsyncSession] = None, cookies: Dict[str, str] = {}, proxy: Optional[str] = None,
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {},
    debug: bool = False
) -> Tuple[AsyncSession, Dict[str, Any], Dict[str, Any]]:    
    href = requests_args["referer"]
    origin = "/".join(href.split("/")[0:3])
    
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
    
    headers = [
        f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
        'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 
        'upgrade-insecure-requests: 1', 
        "sec-ch-ua-mobile: ?0",
        f"user-agent: {user_agent}",
        f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
        "sec-fetch-site: none",
        "sec-fetch-mode: navigate",
        "sec-fetch-dest: document",
        'sec-fetch-user: ?1',
        "accept-encoding: gzip, deflate, br, zstd",
        f"accept-language: {session.client_hints['accept-language']}",
        "priority: u=0, i"
    ]
    
    response = await session.get(href, headers=headers)
    html = await response.async_text()
    async with requests.AsyncSession() as _session:
        nocaptcha_host = "api.nocaptcha.cn" if internal_host else "api.nocaptcha.io"
        if 'Challenge Validation' in html:
            if debug:
                logger.debug('触发 sec_cpt 验证')
            
            nocaptcha_resp = (await _session.post(
                f'http://{nocaptcha_host}/api/wanda/akamai/v2', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    'branch': branch,
                    'href': href,
                    'sec_cpt_html': html,
                    'cookies': session.cookies,
                    'user_agent': user_agent,
                    'proxy': session.proxy,
                    **session.ipinfo
                }
            )).json()
            
            if nocaptcha_resp["status"]:
                extra.update(nocaptcha_resp['extra'])
                session.cookies.update(nocaptcha_resp["data"])
                response = await session.get(href, headers=headers)
            else:
                raise Warning(f'akamai sec_cpt 验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
        
        html = await response.async_text()
        
        if 'Oops, Something Went Wrong.' in html:
            raise Warning('ip 被 ban, 切 ip 重试')

        elif "var chlgeId = ''" in html:
            if debug:
                logger.debug('触发 bm_sc 模式')
            
            bm_sc_src = re.search(r'src="(.*?)"', html)[1].replace('amp;', '')

            nocaptcha_resp = (await _session.post(
                f'http://{nocaptcha_host}/api/wanda/akamai/v2', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    'branch': branch,
                    'href': href,
                    'bm_sc_src': bm_sc_src,
                    'cookies': session.cookies,
                    'user_agent': user_agent,
                    'proxy': session.proxy,
                    **session.ipinfo
                }
            )).json()
            if debug:
                logger.debug(f"bm_sc 模式验证结果: {nocaptcha_resp}")
            if nocaptcha_resp["status"]:      
                extra.update(nocaptcha_resp['extra'])          
                session.cookies.update(nocaptcha_resp["data"])
                response = await session.get(href, headers=headers)
            else:
                raise Warning(f'akamai bm_sc 验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
        
        if parse_index:
            await parse_index(response, extra)
        
        html = await response.async_text()
        
    api = requests_args.get("api")
    if not api:
        try:
            apis = re.findall(r"type=\"text\/javascript\"[ ]{1,2}src\=\"((?:\/[A-Za-z0-9\-\_\+]*?)+)\"(?: defer){0,1}\>\<\/script\>", html)
            if not apis:
                apis = re.findall(r"nonce=\"[a-f0-9]{32}\"[ ]{1,2}src\=\"((?:\/[A-Za-z0-9\-\_\+]*?)+)\"(?: defer){0,1}\>\<\/script\>", html)
            if not apis:
                raise Warning('api 查找失败')
            api = apis[0]
            if not api.startswith("http"):
                api = requests_args.get("api_host", origin) + api
        except:
            raise Warning('api 查找失败')
        
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
        api_response = await session.get(api, headers=headers)
        if api_response.status_code != 200:
            raise Warning("脚本请求失败")

        requests_args['api'] = api
        requests_args["api_headers"] = api_response.headers
    
        iframe_src = requests_args.get("iframe_src")
        if iframe_src:
            nocaptcha_resp = (await _session.post(
                f'http://{nocaptcha_host}/api/wanda/akamai/v2', headers={
                    'user-token': user_token,
                    **({ "Developer-Id": developer_id } if developer_id else {})
                }, json={
                    'is_auth': auth,
                    'branch': branch,
                    'href': href,
                    'api': api,
                    'api_headers': api_response.headers,
                    'cookies': session.cookies,
                    'user_agent': user_agent,
                    'proxy': session.proxy,
                    **session.ipinfo
                }
            )).json()
            
            if nocaptcha_resp['status']:
                extra.update(nocaptcha_resp['extra'])
                session.cookies.update(nocaptcha_resp["data"])                        

                headers = [
                    f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                    "sec-ch-ua-mobile: ?0",
                    f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                    'upgrade-insecure-requests: 1',                 
                    f"user-agent: {user_agent}",
                    'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 
                    "sec-fetch-site: same-origin",
                    "sec-fetch-mode: navigate",
                    'sec-fetch-user: ?1',
                    "sec-fetch-dest: iframe",
                    f'referer: {href}',
                    "accept-encoding: gzip, deflate, br, zstd",
                    f"accept-language: {session.client_hints['accept-language']}",
                    "priority: u=0, i"
                ]
                response = await session.get(iframe_src, headers=headers)                    
                html = await response.async_text()
                
                origin = "/".join(iframe_src.split("/")[0:3])
                try:
                    apis = re.findall(r"type=\"text\/javascript\"[ ]{1,2}src\=\"((?:\/[A-Za-z0-9\-\_\+]*?)+)\"(?: defer){0,1}\>\<\/script\>", html)
                    if not apis:
                        apis = re.findall(r"nonce=\"[a-f0-9]{32}\"[ ]{1,2}src\=\"((?:\/[A-Za-z0-9\-\_\+]*?)+)\"(?: defer){0,1}\>\<\/script\>", html)
                    if not apis:
                        raise Warning('api 查找失败')
                    api = apis[0]
                    if not api.startswith("http"):
                        api = requests_args.get("api_host", origin) + api
                except:
                    raise Warning('api 查找失败')

                headers = [
                    f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                    f"user-agent: {user_agent}",
                    f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                    "sec-ch-ua-mobile: ?0",
                    "accept: */*",
                    "sec-fetch-site: same-origin",
                    "sec-fetch-mode: no-cors",
                    "sec-fetch-dest: script",
                    f"referer: {iframe_src}",
                    "accept-encoding: gzip, deflate, br, zstd",
                    f"accept-language: {session.client_hints['accept-language']}",
                    "priority: u=2"
                ]

                api_response = await session.get(api, headers=headers)
                if api_response.status_code != 200:
                    raise Warning(f"iframe api 脚本请求失败: {api_response.status_code}")

                requests_args["referer"] = iframe_src
                requests_args['api'] = api
                requests_args["api_headers"] = api_response.headers
                del requests_args["iframe_src"]
            else:
                raise Warning("akamai v2 验证失败")
        
        if other_requests:
            await other_requests(session, requests_args, extra)

        for k, v in requests_args.items():
            if isinstance(v, dict):
                for k1, v1 in v.items():
                    if callable(v1):
                        requests_args[k][k1] = v1(response)
        
        sub_domain = '.' + '.'.join(href.split('/')[2].split('.')[-2:])
        
        nocaptcha_resp = (await _session.post(
            f'http://{nocaptcha_host}/api/wanda/akamai/v3', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json={
                'is_auth': auth,
                'branch': branch,
                **requests_args,
                'cookies': [
                    {
                        'name': name,
                        'value': value,
                        'domain': sub_domain
                    } for name, value in session.cookies.items()
                ],
                'user_agent': user_agent,
                'proxy': session.proxy,
                **session.ipinfo
            }
        )).json()
        if debug:
            logger.debug(f"验证结果: {nocaptcha_resp}")
            
        if nocaptcha_resp["status"]:
            extra.update(nocaptcha_resp['extra'])
            session.cookies.update(nocaptcha_resp["data"]["cookies"])
            return session, nocaptcha_resp["data"].get("response", {}), extra
        else:
            raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')


def crack_akamai_v3(
    user_token: str, requests_args: Dict[str, str],
    other_requests: Optional[callable] = None, parse_index: Optional[callable] = None,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[Session] = None, cookies: Dict[str, str] = {}, proxy: Optional[str] = None,
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {},
    debug: bool = False
) -> Tuple[Session, Dict[str, Any], Dict[str, Any]]:
    href = requests_args["referer"]
    origin = "/".join(href.split("/")[0:3])
    
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
    
    headers = [
        f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
        'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 
        'upgrade-insecure-requests: 1', 
        "sec-ch-ua-mobile: ?0",
        f"user-agent: {user_agent}",
        f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
        "sec-fetch-site: none",
        "sec-fetch-mode: navigate",
        "sec-fetch-dest: document",
        'sec-fetch-user: ?1',
        "accept-encoding: gzip, deflate, br, zstd",
        f"accept-language: {session.client_hints['accept-language']}",
        "priority: u=0, i"
    ]
    
    response = session.get(href, headers=headers)

    nocaptcha_host = "api.nocaptcha.cn" if internal_host else "api.nocaptcha.io"
    if 'Challenge Validation' in response.text:
        if debug:
            logger.debug('触发 sec_cpt 验证')
        
        nocaptcha_resp = requests.post(
            f'http://{nocaptcha_host}/api/wanda/akamai/v2', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json={
                'is_auth': auth,
                'branch': branch,
                'href': href,
                'sec_cpt_html': response.text,
                'cookies': session.cookies,
                'user_agent': user_agent,
                'proxy': session.proxy,
                **session.ipinfo
            }
        ).json()
        if debug:
            logger.debug(nocaptcha_resp)
        
        if nocaptcha_resp["status"]:
            extra.update(nocaptcha_resp['extra'])
            session.cookies.update(nocaptcha_resp["data"])
            response = session.get(href, headers=headers)
        else:
            raise Warning(f'akamai sec_cpt 验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
    
    if 'Oops, Something Went Wrong.' in response.text:
        raise Warning('ip 被 ban, 切 ip 重试')

    elif "var chlgeId = ''" in response.text:
        if debug:
            logger.debug('触发 bm_sc 模式')
        
        bm_sc_src = re.search(r'src="(.*?)"', response.text)[1].replace('amp;', '')

        nocaptcha_resp = requests.post(
            f'http://{nocaptcha_host}/api/wanda/akamai/v2', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json={
                'is_auth': auth,
                'branch': branch,
                'href': href,
                'bm_sc_src': bm_sc_src,
                'cookies': session.cookies,
                'user_agent': user_agent,
                'proxy': session.proxy,
                **session.ipinfo
            }
        ).json()
        if debug:
            logger.debug(nocaptcha_resp)
            
        if nocaptcha_resp["status"]:                
            extra.update(nocaptcha_resp['extra'])
            session.cookies.update(nocaptcha_resp["data"])
            response = session.get(href, headers=headers)
        else:
            raise Warning(f'akamai bm_sc 验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
    
    if parse_index:
        parse_index(response, extra)
    
    html = response.text
    api = requests_args.get("api")
    if not api:
        try:
            apis = re.findall(r"type=\"text\/javascript\"[ ]{1,2}src\=\"((?:\/[A-Za-z0-9\-\_\+]*?)+)\"(?: defer){0,1}\>\<\/script\>", html)
            if not apis:
                apis = re.findall(r"nonce=\"[a-f0-9]{32}\"[ ]{1,2}src\=\"((?:\/[A-Za-z0-9\-\_\+]*?)+)\"(?: defer){0,1}\>\<\/script\>", html)
            if not apis:
                raise Warning('api 查找失败')
            api = apis[0]
            if not api.startswith("http"):
                api = requests_args.get("api_host", origin) + api
        except:
            raise Warning('api 查找失败')
    
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
    api_response = session.get(api, headers=headers)
    if api_response.status_code != 200:
        raise Warning("脚本请求失败")

    requests_args['api'] = api
    requests_args["api_headers"] = api_response.headers

    iframe_src = requests_args.get("iframe_src")
    if iframe_src:
        nocaptcha_resp = requests.post(
            f'http://{nocaptcha_host}/api/wanda/akamai/v2', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json={
                'is_auth': auth,
                'branch': branch,
                'href': href,
                'api': api,
                'api_headers': api_response.headers,
                'cookies': session.cookies,
                'user_agent': user_agent,
                'proxy': session.proxy,
                **session.ipinfo
            }
        ).json()
        if debug:
            logger.debug(nocaptcha_resp)
        
        if nocaptcha_resp['status']:
            extra.update(nocaptcha_resp['extra'])
            session.cookies.update(nocaptcha_resp["data"])                        

            headers = [
                f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                "sec-ch-ua-mobile: ?0",
                f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                'upgrade-insecure-requests: 1',                 
                f"user-agent: {user_agent}",
                'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 
                "sec-fetch-site: same-origin",
                "sec-fetch-mode: navigate",
                'sec-fetch-user: ?1',
                "sec-fetch-dest: iframe",
                f'referer: {href}',
                "accept-encoding: gzip, deflate, br, zstd",
                f"accept-language: {session.client_hints['accept-language']}",
                "priority: u=0, i"
            ]
            response = session.get(iframe_src, headers=headers)
            
            origin = "/".join(iframe_src.split("/")[0:3])
            html = response.text
            try:
                apis = re.findall(r"type=\"text\/javascript\"[ ]{1,2}src\=\"((?:\/[A-Za-z0-9\-\_\+]*?)+)\"(?: defer){0,1}\>\<\/script\>", html)
                if not apis:
                    apis = re.findall(r"nonce=\"[a-f0-9]{32}\"[ ]{1,2}src\=\"((?:\/[A-Za-z0-9\-\_\+]*?)+)\"(?: defer){0,1}\>\<\/script\>", html)
                if not apis:
                    raise Warning('api 查找失败')
                api = apis[0]
                if not api.startswith("http"):
                    api = requests_args.get("api_host", origin) + api
            except:
                raise Warning('api 查找失败')

            headers = [
                f"sec-ch-ua-platform: {session.client_hints['sec-ch-ua-platform']}",
                f"user-agent: {user_agent}",
                f"sec-ch-ua: {session.client_hints['sec-ch-ua']}",
                "sec-ch-ua-mobile: ?0",
                "accept: */*",
                "sec-fetch-site: same-origin",
                "sec-fetch-mode: no-cors",
                "sec-fetch-dest: script",
                f"referer: {iframe_src}",
                "accept-encoding: gzip, deflate, br, zstd",
                f"accept-language: {session.client_hints['accept-language']}",
                "priority: u=2"
            ]

            api_response = session.get(api, headers=headers)
            if api_response.status_code != 200:
                raise Warning(f"iframe api 脚本请求失败: {api_response.status_code}")

            requests_args["referer"] = iframe_src
            requests_args['api'] = api
            requests_args["api_headers"] = api_response.headers
            del requests_args["iframe_src"]
        else:
            raise Warning("akamai v2 验证失败")
    
    if other_requests:
        other_requests(session, requests_args, extra)

    for k, v in requests_args.items():
        if isinstance(v, dict):
            for k1, v1 in v.items():
                if callable(v1):
                    requests_args[k][k1] = v1(response)
    
    sub_domain = '.' + '.'.join(href.split('/')[2].split('.')[-2:])
    
    nocaptcha_resp = requests.post(
        f'http://{nocaptcha_host}/api/wanda/akamai/v3', headers={
            'user-token': user_token,
            **({ "Developer-Id": developer_id } if developer_id else {})
        }, json={
            'is_auth': auth,
            'branch': branch,
            **requests_args,
            'cookies': [
                {
                    'name': name,
                    'value': value,
                    'domain': sub_domain
                } for name, value in session.cookies.items()
            ],
            'user_agent': user_agent,
            'proxy': session.proxy,
            **session.ipinfo
        }
    ).json()
    if debug:
        logger.debug(nocaptcha_resp)
        
    if nocaptcha_resp["status"]:
        extra.update(nocaptcha_resp['extra'])
        session.cookies.update(nocaptcha_resp["data"]["cookies"])
        return session, nocaptcha_resp["data"].get("response", {}), extra
    else:
        raise Warning(f'验证失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
