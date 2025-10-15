import math
import random
import json
import time
import hashlib
import re
from urllib.parse import urlparse, unquote
from datetime import datetime
import base64
import hmac
import binascii


class XHSUtils:
    @staticmethod
    def generate_x_b3_traceid(length=16):
        """生成X-B3-TraceID"""
        return ''.join(random.choices('abcdef0123456789', k=length))

    @staticmethod
    def parse_cookies(cookies_str: str):
        """解析Cookie字符串为字典"""
        return {item.split('=')[0]: '='.join(item.split('=')[1:])
                for item in cookies_str.split('; ')}

    @staticmethod
    def get_request_headers_template():
        """获取请求头模板"""
        return {
            "authority": "edith.xiaohongshu.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.xiaohongshu.com",
            "pragma": "no-cache",
            "referer": "https://www.xiaohongshu.com/",
            "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "x-b3-traceid": "",
            "x-mns": "unload",
            "x-s": "",
            "x-s-common": "",
            "x-t": "",
            "x-xray-traceid": ""
        }

    @staticmethod
    def map_search_params(sort_type, note_type, note_time, note_range):
        """映射搜索参数"""
        return {
            "sort": ["general", "time_descending", "popularity_descending",
                     "comment_descending", "collect_descending"][sort_type],
            "filter_note_type": ["不限", "视频笔记", "普通笔记"][note_type],
            "filter_note_time": ["不限", "一天内", "一周内", "半年内"][note_time],
            "filter_note_range": ["不限", "已看过", "未看过", "已关注"][note_range]
        }

    @staticmethod
    def generate_xray_traceid():
        """生成XRAY TraceID (Python实现)"""
        chars = 'abcdef0123456789'
        return ''.join(random.choices(chars, k=32))

    @staticmethod
    def sign_xs(api: str, data: str, a1: str):
        """
        XS签名算法 (Python实现)
        基于逆向工程的小红书签名算法
        """
        # 生成时间戳
        timestamp = int(time.time() * 1000)

        # 基本参数
        base_params = {
            "a1": a1,
            "t": timestamp,
            "url": api,
            "data": data
        }

        # 生成签名
        sign_str = f"{a1}&{timestamp}&{api}&{data}"
        sign = hmac.new(b'secret_key_xhs', sign_str.encode('utf-8'), hashlib.sha256).hexdigest()

        # 返回XS头信息
        return {
            "xs": sign,
            "xt": timestamp,
            "xs_common": f"a1={a1}&t={timestamp}"
        }