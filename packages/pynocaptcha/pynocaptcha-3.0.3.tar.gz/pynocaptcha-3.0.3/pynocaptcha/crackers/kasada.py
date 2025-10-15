# -*- coding: UTF-8 -*-

import sys
import re
import base64
from curl_cffi import requests
from loguru import logger

from typing import Union, Tuple, Optional, Dict, Any

if sys.version_info >= (3, 8):  # pragma: no cover (py38+)
    from typing import Literal
else:  # pragma: no cover (py38+)
    from typing_extensions import Literal

from .base import BaseCracker
from ..magneto.session import AsyncSession, Session


class KasadaCdCracker(BaseCracker):
    cracker_name = "kasada"
    cracker_version = "cd"

    """
    kasada x-kpsdk-ct cracker
    :param href: 触发验证的页面地址
    调用示例:
    cracker = KasadaCdCracker(
        user_token="xxx",
        href="https://arcteryx.com/ca/en/shop/mens/beta-lt-jacket-7301",
        debug=True,
    )
    ret = cracker.crack()
    """

    # 必传参数
    must_check_params = ["href", "st"]
    option_params = {
        "ct": ""
    }


async def async_crack_kasada(
    user_token: str, href: str, proxy: Optional[str] = None, kpsdk_v: Optional[str] = None, fp_host: Optional[str] = None, iframe: bool = True, submit: bool = False,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[AsyncSession] = None, cookies: Dict[str, str] = {},
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[AsyncSession, Dict[str, Any], Dict[str, Any]]:
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

    headers = {
        'sec-ch-ua': session.client_hints['sec-ch-ua'],
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': session.client_hints['sec-ch-ua-platform'],
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'referer': href,
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': session.client_hints['accept-language'],
        'priority': 'u=0, i'
    }
    
    origin = "/".join(href.split("/")[0:3])
    _fp_protocol = href.split("://")[0]
    if not fp_host:
        fp_host = href.split("/")[2]
        
    if not kpsdk_v:
        if '?x-kpsdk-v=' in href:
            kpsdk_v = href.split("?x-kpsdk-v=")[1]
    
    if iframe:            
        headers["sec-fetch-dest"] = "iframe"
        headers["sec-fetch-site"] = "same-site"
        response = await session.get(f"{_fp_protocol}://{fp_host}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v={kpsdk_v}", headers=headers)
    else:
        response = await session.get(href, headers=headers)

    if response.status_code not in [429, 200]:
        raise Exception(f"fp status code: {response.status_code}")
    
    fp_html = await response.async_text()
    if '/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/ips.js' not in fp_html and 'KPSDK' in fp_html:
        kpsdk_args = {
            "href": href,
            "fp_host": fp_host,
            "fp_html": fp_html,
            "user_agent": user_agent,
            "cookies": session.cookies,
            "iframe": iframe,
        }
    else:            
        # KP_UIDz
        uidk = None
        for k, _ in response.cookies.items():
            if k.endswith('-ssn'):
                uidk = k.replace('-ssn', '')
        
        if not uidk:
            raise Warning("站点异常, 请联系管理员处理")

        ips_url = _fp_protocol + '://' + fp_host + re.search(r'src="(\/149e9513-01fa-4fb0-aad4-566afd725d1b\/2d206a39-8ed7-437e-a3be-862e0f06eea3\/ips\.js\?.*?)"', fp_html)[1].replace('amp;', '')
        
        headers = {
            'sec-ch-ua-platform': session.client_hints['sec-ch-ua-platform'],
            'user-agent': user_agent,
            'sec-ch-ua': session.client_hints['sec-ch-ua'],
            'sec-ch-ua-mobile': '?0',
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'referer': f"{_fp_protocol}://{fp_host}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v={kpsdk_v}",
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': session.client_hints['accept-language'],
            'priority': 'u=1'
        }
        ips_resp = await session.get(ips_url, headers=headers)
        kpsdk_args = {
            "href": href,
            "fp_host": fp_host,
            "fp_html": fp_html,
            "ips_script": await ips_resp.async_text(),
            "ips_headers": ips_resp.headers,
            "cookies": session.cookies,
            "user_agent": user_agent,
            "iframe": iframe,
        }
    
    kpsdk_args.update({
        **session.ipinfo,
        "submit": submit,
        "branch": branch,
        'is_auth': auth,
    })

    if submit:
        kpsdk_args['proxy'] = proxy
    
    nocaptcha_host = "api.nocaptcha.cn" if internal_host else "api.nocaptcha.io"
    async with requests.AsyncSession() as _session:
        nocaptcha_resp = (await _session.post(
            f'http://{nocaptcha_host}/api/wanda/kasada/ct', headers={
                'user-token': user_token,
                **({ "Developer-Id": developer_id } if developer_id else {})
            }, json=kpsdk_args
        )).json()
    
        if nocaptcha_resp["status"]:
            extra = nocaptcha_resp['extra']
            if not submit:
                extra = nocaptcha_resp['extra']
                post_data = base64.b64decode(nocaptcha_resp["data"]["post_data"].encode())
                headers = {
                    'content-length': str(len(post_data)),
                    'x-kpsdk-ct': nocaptcha_resp["data"]["headers"]['x-kpsdk-ct'],
                    'sec-ch-ua-platform': extra['sec-ch-ua-platform'],
                    'x-kpsdk-dt': nocaptcha_resp["data"]["headers"]['x-kpsdk-dt'],
                    'sec-ch-ua': extra['sec-ch-ua'],
                    'x-kpsdk-im': nocaptcha_resp["data"]["headers"]['x-kpsdk-im'],
                    'sec-ch-ua-mobile': '?0',
                    'x-kpsdk-v': nocaptcha_resp["data"]["headers"].get('x-kpsdk-v') or kpsdk_v,
                    'user-agent': extra['user-agent'],
                    'content-type': 'application/octet-stream',
                    'accept': '*/*',
                    'origin': origin,
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': f"{_fp_protocol}://{fp_host}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v={kpsdk_v}" if iframe else href,
                    'accept-encoding': 'gzip, deflate, br, zstd',
                    'accept-language': extra['accept-language'],
                    'priority': 'u=1, i',
                }

                response = await session.post(
                    f'{_fp_protocol}://{fp_host}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/tl',
                    headers=headers,
                    body=base64.b64decode(nocaptcha_resp["data"]["post_data"].encode()),
                )
                if 'reload' in await response.async_text():
                    kpsdk_ct = response.headers.get('x-kpsdk-ct')
                    kpsdk_st = int(response.headers.get('x-kpsdk-st'))
                    kpsdk_res = {
                        'x-kpsdk-ct': kpsdk_ct,
                        'x-kpsdk-st': kpsdk_st
                    }
                else:
                    raise Warning("验证失败")
            else:
                kpsdk_res = nocaptcha_resp['data']
            
            kpsdk_res.update({
                'x-kpsdk-v': kpsdk_v,
            })
            if debug:
                logger.debug(kpsdk_res)
            return session, kpsdk_res, extra
        else:
            raise Warning("计算失败")


def crack_kasada(
    user_token: str, href: str, proxy: Optional[str] = None, kpsdk_v: Optional[str] = None, fp_host: Optional[str] = None, iframe: bool = True, submit: bool = False,
    internal_host: bool = True, branch: Optional[str] = None,
    developer_id: Optional[str] = None, auth: bool = False,
    session: Optional[Session] = None, cookies: Dict[str, str] = {},
    timeout: int = 15, allow_redirects: bool = True, verify: bool = False, http_version: Optional[Literal["http1", "http2"]] = None,
    user_agent: Union[str, Tuple[int, Literal["windows", "macos"], Literal["chrome", "edge"]]] = None,
    ipinfo: Dict[str, str] = {}, extra: Dict[str, str] = {}, debug: bool = False
) -> Tuple[Session, Dict[str, Any], Dict[str, Any]]:
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
    
    headers = {
        'sec-ch-ua': session.client_hints['sec-ch-ua'],
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': session.client_hints['sec-ch-ua-platform'],
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'referer': href,
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': session.client_hints['accept-language'],
        'priority': 'u=0, i'
    }
    
    origin = "/".join(href.split("/")[0:3])
    _fp_protocol = href.split("://")[0]
    if not fp_host:
        fp_host = href.split("/")[2]
        
    if not kpsdk_v:
        if '?x-kpsdk-v=' in href:
            kpsdk_v = href.split("?x-kpsdk-v=")[1]
    
    if iframe:            
        headers["sec-fetch-dest"] = "iframe"
        headers["sec-fetch-site"] = "same-site"
        response = session.get(f"{_fp_protocol}://{fp_host}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v={kpsdk_v}", headers=headers)
    else:
        response = session.get(href, headers=headers)

    if response.status_code not in [429, 200]:
        raise Exception(f"fp status code: {response.status_code}")
    
    fp_html = response.text
    if '/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/ips.js' not in fp_html and 'KPSDK' in fp_html:
        kpsdk_args = {
            "href": href,
            "fp_host": fp_host,
            "fp_html": fp_html,
            "user_agent": user_agent,
            "cookies": session.cookies,
            "iframe": iframe,
        }
    else:            
        # KP_UIDz
        uidk = None
        for k, _ in response.cookies.items():
            if k.endswith('-ssn'):
                uidk = k.replace('-ssn', '')
        
        if not uidk:
            raise Warning("站点异常, 请联系管理员处理")

        ips_url = _fp_protocol + '://' + fp_host + re.search(r'src="(\/149e9513-01fa-4fb0-aad4-566afd725d1b\/2d206a39-8ed7-437e-a3be-862e0f06eea3\/ips\.js\?.*?)"', fp_html)[1].replace('amp;', '')
        
        headers = {
            'sec-ch-ua-platform': session.client_hints['sec-ch-ua-platform'],
            'user-agent': user_agent,
            'sec-ch-ua': session.client_hints['sec-ch-ua'],
            'sec-ch-ua-mobile': '?0',
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'referer': f"{_fp_protocol}://{fp_host}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v={kpsdk_v}",
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': session.client_hints['accept-language'],
            'priority': 'u=1'
        }
        ips_resp = session.get(ips_url, headers=headers)
        kpsdk_args = {
            "href": href,
            "fp_host": fp_host,
            "fp_html": fp_html,
            "ips_script": ips_resp.text,
            "ips_headers": ips_resp.headers,
            "cookies": session.cookies,
            "user_agent": user_agent,
            "iframe": iframe,
        }
    
    kpsdk_args.update({
        **session.ipinfo,
        "submit": submit,
        "branch": branch,
        'is_auth': auth,
    })

    if submit:
        kpsdk_args['proxy'] = proxy
    
    nocaptcha_host = "api.nocaptcha.cn" if internal_host else "api.nocaptcha.io"
    nocaptcha_resp = requests.post(
        f'http://{nocaptcha_host}/api/wanda/kasada/ct', headers={
            'user-token': user_token,
            **({ "Developer-Id": developer_id } if developer_id else {})
        }, json=kpsdk_args
    ).json()
    
    if nocaptcha_resp["status"]:
        if not submit:
            extra.update(nocaptcha_resp['extra'])
            post_data = base64.b64decode(nocaptcha_resp["data"]["post_data"].encode())
            headers = {
                'content-length': str(len(post_data)),
                'x-kpsdk-ct': nocaptcha_resp["data"]["headers"]['x-kpsdk-ct'],
                'sec-ch-ua-platform': extra['sec-ch-ua-platform'],
                'x-kpsdk-dt': nocaptcha_resp["data"]["headers"]['x-kpsdk-dt'],
                'sec-ch-ua': extra['sec-ch-ua'],
                'x-kpsdk-im': nocaptcha_resp["data"]["headers"]['x-kpsdk-im'],
                'sec-ch-ua-mobile': '?0',
                'x-kpsdk-v': nocaptcha_resp["data"]["headers"].get('x-kpsdk-v') or kpsdk_v,
                'user-agent': extra['user-agent'],
                'content-type': 'application/octet-stream',
                'accept': '*/*',
                'origin': origin,
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': f"{_fp_protocol}://{fp_host}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v={kpsdk_v}" if iframe else href,
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': extra['accept-language'],
                'priority': 'u=1, i',
            }

            response = session.post(
                f'{_fp_protocol}://{fp_host}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/tl',
                headers=headers,
                body=base64.b64decode(nocaptcha_resp["data"]["post_data"].encode()),
            )
            if 'reload' in response.text:
                kpsdk_ct = response.headers.get('x-kpsdk-ct')
                kpsdk_st = int(response.headers.get('x-kpsdk-st'))
                kpsdk_res = {
                    'x-kpsdk-ct': kpsdk_ct,
                    'x-kpsdk-st': kpsdk_st
                }
            else:
                raise Warning("验证失败")
        else:
            kpsdk_res = nocaptcha_resp['data']
        
        kpsdk_res.update({
            'x-kpsdk-v': kpsdk_v,
        })
        if debug:
            logger.debug(kpsdk_res)
        
        return session, kpsdk_res, extra
    else:
        raise Warning(f'计算失败, id: {nocaptcha_resp["id"]}, err: {nocaptcha_resp["msg"]}')
