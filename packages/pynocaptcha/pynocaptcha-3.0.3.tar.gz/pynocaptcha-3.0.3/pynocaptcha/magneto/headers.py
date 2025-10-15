# -*- coding: utf-8 -*-


import re
import sys


# TODO 补全
ACCEPT_LANGUAGE_MAP = {
    "jp": "ja-JP,ja;q=0.9",
    "us": "en-US,en;q=0.9",
    "tw": "zh-TW,zh;q=0.9",
    "hk": "zh-HK,zh;q=0.9",
    "it": "it-IT,it;q=0.9",
    "de": "de-DE,de;q=0.9",
    "es": "es-ES,es;q=0.9",
    "in": "en-IN,en;q=0.9",
    "cn": "zh-CN,zh;q=0.9",
    "fr": "fr-FR,fr;q=0.9",
    "tr": "tr-TR,tr;q=0.9",
    "ru": "ru-RU,uk;q=0.9",
    "gb": "en-GB,en;q=0.9",
    "ua": "uk-UA,uk;q=0.9",
    "ca": "en-US,en;q=0.9",
    "au": "en-AU,en;q=0.9"
}


def parse_sec_ch_ua(user_agent: str) -> str:
    """
    根据 user-agent 计算 sec-ch-ua 值
    :param user-agent:
    :return
    """
    version = int(re.search(r"(\d+)\.0\.0\.0", user_agent)[1])
    greasey_chars = [
        " ",
        "(",
        ":",
        "-",
        ".",
        "/",
        ")",
        ";",
        "=",
        "?",
        "_",
    ]
    greased_versions = ["8", "99", "24"]
    orders = [
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ][version % 6]
    brands = [
        {
            "brand": "".join([
                "Not",
                greasey_chars[version % 11],
                "A",
                greasey_chars[(version + 1) % 11],
                "Brand",
            ]),
            "version": greased_versions[version % 3],
        },
        { "brand": "Chromium", "version": str(version) },
        { "brand": "Google Chrome", "version": str(version) },
    ]
    _brands = [None, None, None]
    _brands[orders[0]] = brands[0]
    _brands[orders[1]] = brands[1]
    _brands[orders[2]] = brands[2]
    
    return ", ".join(map(lambda _: f'"{_["brand"]}";v="{_["version"]}"', _brands))
