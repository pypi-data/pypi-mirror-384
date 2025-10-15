import requests
import json
import random
import time
from .xhs_utils import XHSUtils

"""
from bruce_li_tc import XHSCrawler

# 初始化爬虫
crawler = XHSCrawler(cookies_str='你的cookie')

# 1. 单页搜索
success, msg, result = crawler.single_search_api("榴莲")
print(f"总共获取到 {len(result)} 条笔记")
print("result",result)


# 2. 多页搜索
all_notes = crawler.all_search_api("榴莲")
print(f"总共获取到 {len(all_notes)} 条笔记")
print("all_notes",all_notes)
"""

class XHSCrawler:
    def __init__(self, cookies_str: str):
        self.URL = "https://edith.xiaohongshu.com"
        self.cookies = XHSUtils.parse_cookies(cookies_str)
        self.a1 = self.cookies.get('a1', '')

    def _generate_headers(self, api: str, data: dict = None):
        """生成请求头"""
        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False) if data else ''

        # 获取XS加密头
        ret = XHSUtils.sign_xs(api, data_str, self.a1)

        # 生成其他头信息
        headers = XHSUtils.get_request_headers_template()
        headers.update({
            "x-s": ret['xs'],
            "x-t": str(ret['xt']),
            "x-s-common": ret['xs_common'],
            "x-b3-traceid": XHSUtils.generate_x_b3_traceid(),
            "x-xray-traceid": XHSUtils.generate_xray_traceid()
        })

        return headers, data_str

    def single_search_api(self, query: str, page: int = 1, sort_type: int = 0,
                     note_type: int = 0, note_time: int = 0,
                     note_range: int = 0, pos_distance: int = 0,
                     geo: dict = None, proxies: dict = None):
        """
        搜索小红书笔记
        :param query: 搜索关键词
        :param page: 页码(默认1)
        :param sort_type: 排序方式(0=综合,1=最新,2=点赞,3=评论,4=收藏)
        :param note_type: 笔记类型(0=不限,1=视频,2=图文)
        :param note_time: 时间范围(0=不限,1=1天,2=1周,3=半年)
        :param note_range: 范围(0=不限,1=看过,2=未看,3=关注)
        :param pos_distance: 位置距离(0=不限,1=同城,2=附近) 指定这个1或2必须要指定 geo
        :param geo: 地理位置信息（指定这个1或2必须要指定 geo）
        :param proxies: 代理设置
        :return: (success, message, response_data)
        """
        api = "/api/sns/web/v1/search/notes"

        # 映射参数
        params_map = XHSUtils.map_search_params(sort_type, note_type, note_time, note_range)

        # 处理位置筛选
        filter_pos_distance = "不限"
        if pos_distance == 1:
            filter_pos_distance = "同城"
        elif pos_distance == 2:
            filter_pos_distance = "附近"

        data = {
            "keyword": query,
            "page": page,
            "page_size": 20,
            "search_id": XHSUtils.generate_x_b3_traceid(21),
            "sort": params_map["sort"],
            "note_type": note_type,
            "ext_flags": [],
            "filters": [
                {"tags": [params_map["sort"]], "type": "sort_type"},
                {"tags": [params_map["filter_note_type"]], "type": "filter_note_type"},
                {"tags": [params_map["filter_note_time"]], "type": "filter_note_time"},
                {"tags": [params_map["filter_note_range"]], "type": "filter_note_range"},
                {"tags": [filter_pos_distance], "type": "filter_pos_distance"}
            ],
            "image_formats": ["jpg", "webp", "avif"]
        }

        # 添加地理位置信息
        if geo:
            data["geo"] = json.dumps(geo, separators=(',', ':'))

        try:
            headers, data_str = self._generate_headers(api, data)
            response = requests.post(
                url=self.URL + api,
                headers=headers,
                data=data_str.encode("utf-8"),
                cookies=self.cookies,
                proxies=proxies,
                timeout=30
            )
            res_json = response.json()
            return res_json.get("success", False), res_json.get("msg", ""), res_json
        except Exception as e:
            return False, str(e), None

    def all_search_api(self, query: str, max_notes: int = 500, **kwargs):
        """
        获取多页搜索结果
        :param query: 搜索关键词
        :param max_notes: 最大获取笔记数
        :return: 笔记列表
        """
        notes = []
        page = 1
        has_more = True

        try:
            while has_more and len(notes) < max_notes:
                success, msg, res = self.single_search_api(query, page=page, **kwargs)

                if not success:
                    raise Exception(f"搜索失败: {msg}")

                if "data" not in res or "items" not in res["data"]:
                    break

                items = res["data"]["items"]
                notes.extend(items)

                # 检查是否有更多结果
                has_more = res["data"].get("has_more", False)
                page += 1

                # 随机延迟避免被封
                time.sleep(random.uniform(1.5, 3.5))

                # 打印进度
                #print(f"已获取 {len(notes)}/{max_notes} 条笔记")

        except Exception as e:
            print(f"获取笔记时出错: {str(e)}")

        # 确保不超过最大数量
        if len(notes) > max_notes:
            notes = notes[:max_notes]

        return notes

