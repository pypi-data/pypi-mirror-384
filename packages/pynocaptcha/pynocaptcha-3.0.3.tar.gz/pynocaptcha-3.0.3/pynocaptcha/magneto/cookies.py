# -*- coding: utf-8 -*-


from http.cookies import SimpleCookie


class Cookie(dict):
    
    def to_str(self):
        """
        转成 headers 中的 cookie 字符串
        """
        cookie = SimpleCookie()
        for key, value in self.items():
            cookie[key] = value
        
        return cookie.output(header='', sep=';').strip().replace('="', '=').replace('"; ', '; ').strip('"')
