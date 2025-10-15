import requests
import json
from typing import TypedDict, List, Optional, Dict, Any, Union
from openai import OpenAI
from .factory import model_factory
from .base_search import BaseAIModel
from dataclasses import dataclass,field




class SearchResultItemType(TypedDict,total=False):
    """定义搜索结果项的类型 - 包含所有可能字段"""
    id: int                         # 引用编号1、2、3
    url: str                        # 网页地址
    title: str                      # 网页标题
    date: Optional[str]             # 网页日期
    content: str                    # 网页内容，显示2000字以内的相关信息原文片段
    icon: Optional[str]             # 网站图标地址
    web_anchor: str                 # 网站锚文本或网站标题
    type: str                       # 检索资源类型。返回值：web:网页,video:视频内容,image：图片
    website: str                    # 站点名称
    video: Optional[Any]            # 视频详情
    image: Optional[Any]            # 图片详情
    is_aladdin: bool                # 是否为阿拉丁内容
    aladdin: Optional[Any]          # 阿拉丁详细内容
    snippet: str                    # 摘要片段
    web_extensions: Optional[Dict]  # 网页相关图片
    rerank_score: float             # 原文片段相关性评分（仅type值为web、video时存在），取值范围0～1
    authority_score: float          # 网页权威性评分（仅type值为web时存在），取值范围0～1

class SearchResponseType(TypedDict,total=False):
    """定义完整响应类型 - 包含所有可能字段"""
    request_id: str                         # 请求ID
    references: List[SearchResultItemType]  # 模型回答详情列表
    # 其他可能出现的字段
    error_code: Optional[str]  # 错误代码
    error_msg: Optional[str]   # 错误信息
    # 可能还有其他未知字段，total=False允许其他字段存在


# 使用装饰器注册百度模型
@model_factory.register("baidu")
class BaiDuAISearch(BaseAIModel):
    """百度AI搜索"""
    def __init__(self,api_key: str, base_url: str = "https://qianfan.baidubce.com"):
        self.API_Key = api_key
        self.BaseUrl=base_url

    def search(self,keyword: str,**kwargs)->List[str]:
        new_data = self.baidu_search_extract_contents(keyword)
        return new_data

    def set_config(self, **kwargs):
        """设置配置"""
        if 'api_key' in kwargs:
            self.API_Key = kwargs['api_key']
        if 'base_url' in kwargs:
            self.BaseUrl = kwargs['base_url']

    def ai_search_generate(self,keyword: str):
        """
        智能搜索生成
        能力描述
        概述：可根据用户输入query搜索全网实时信息后，并进行智能总结回答。
        :param keyword:输入关键字
        :return:
        """
        url = self.BaseUrl+"/v2/ai_search/chat/completions"
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.API_Key
        }
        payload=json.dumps({
            "messages": [
                {
                    "content": keyword,
                    "role": "user"
                }
            ],
            "search_source": "baidu_search_v1",
            "resource_type_filter": [
                {"type": "image", "top_k": 4},
                {"type": "video", "top_k": 4},
                {"type": "web", "top_k": 4}
            ],
            "search_recency_filter": "year",
            "stream": False,
            "model": "ernie-3.5-8k",
            "enable_deep_search": False,
            "enable_followup_query": False,
            "temperature": 0.11,
            "top_p": 0.55,
            "search_mode": "auto",
            "enable_reasoning": True
        })
        try:
            res=requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))
            return res.json()
        except Exception as e:
            print(e)

    def ai_search_extract_contents(self,keyword:str):
        pass

    def baidu_search(self,keyword:str)-> Union[SearchResponseType, str]:
        """
        百度搜索
        能力描述
        概述： 可根据用户输入query，搜索全网实时信息，并返回摘要、网址等信息。
        计费：每日免费额度为100次，支持按量后付费（为不影响使用体验，可先去开通后付费），
        默认优先抵扣免费资源，且每个账号每天最多使用100,000次。
        :param keyword: 输入关键字
        :return:
        """
        url = self.BaseUrl+"/v2/ai_search/web_search"
        payload = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": keyword
                }
            ],
            "edition": "standard",
            "search_source": "baidu_search_v2",
            "search_recency_filter": "week"
        }, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+self.API_Key
        }
        try:
            response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))
            return response.json()
        except Exception as e:
            print(e)

    def baidu_search_extract_contents(self,keyword:str)-> List[str]:
        """
        百度搜索过滤后的数据
        :param keyword:
        :return:
        """
        yuan_data=self.baidu_search(keyword)
        new_data=[]
        if yuan_data.get("references") and len(yuan_data.get("references"))>0:
            for i in yuan_data["references"]:
                new_data.append(i["content"].strip())
        return new_data

    def open_ai_sdk_search(self,keyword:str):
        """
        OpenAI SDK调用智能搜索生成
        智能搜索生成V2版本使用与 OpenAI 兼容的 API 格式，通过修改配置，您可以使用 OpenAI SDK 来访问智能搜索生成。
        :param keyword:
        :return:
        """
        try:
            client = OpenAI(api_key=self.API_Key,  # 千帆AppBuilder平台的ApiKey
                            base_url="https://qianfan.baidubce.com/v2/ai_search")  # 智能搜索生成V2版本接口
            response = client.chat.completions.create(
                model="deepseek-r1",
                messages=[
                    {"role": "user", "content": keyword}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(e)
