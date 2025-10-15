from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
import requests
from .factory import model_factory
from .base_search import BaseAIModel
from typing import TypedDict, List, Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum


class MessageType(TypedDict,total=False):
    """定义消息类型"""
    role: str                 #大模型的角色
    content: str              #大模型输出的内容

class SearchResultItemType(TypedDict,total=False):
    """定义搜索结果项的类型 - 包含所有可能字段"""
    message:MessageType       #大模型结果
    index:int                 #大模型的结果序号，在多候选中使用

class SearchUsageType(TypedDict,total=False):
    """定义搜索结果项的类型 - 包含所有可能字段"""
    prompt_tokens: int        #用户输入信息，消耗的token数量
    completion_tokens: int    #大模型输出信息，消耗的token数量
    total_tokens: int         #用户输入+大模型输出，总的token数量

class SearchResponseType(TypedDict,total=False):
    """定义完整响应类型 - 包含所有可能字段"""
    code: int                 # 错误码：0表示成功，非0表示错误
    message: str              # 错误码的描述信息
    sid: Optional[str]        # 本次请求的唯一id
    choices: List[SearchResultItemType] #大模型结果的数组
    usage: SearchUsageType    #本次请求消耗的token数量

class SparkAIModel(Enum):
    """星火大模型请求域/模型枚举

    Attributes:
        指定访问的模型版本:
        4.0Ultra指向4.0 Ultra版本
        generalv3.5指向Max版本
        max-32k指向Max-32K版本
        generalv3指向Pro版本
        pro-128k指向Pro-128K版本
        lite指向Lite版本
    """
    Model_4_Ultra="4.0Ultra"
    Model_Max="generalv3.5" #现阶段使用，精确，但有使用额度
    Model_Max_32K="max-32k"
    Model_Pro="generalv3"
    Model_Pro_128K="pro-128k"
    Model_Lite="lite"   #免费使用，不精确

# 使用装饰器注册星火模型
@model_factory.register("spark")
class XingHuoAISearch(BaseAIModel):
    """星火大模型"""
    def __init__(self,
                 api_password: str,
                 sparkai_app_id: str,
                 sparkai_api_key: str,
                 sparkai_api_secret: str,
                 sparkai_domain:str ="lite",
                 base_url: str = "https://spark-api-open.xf-yun.com/v1/",
                 sparkai_url: str = "wss://spark-api.xf-yun.com/v1.1/chat"):

        self.api_password = api_password
        self.sparkai_app_id = sparkai_app_id
        self.sparkai_api_key = sparkai_api_key
        self.sparkai_api_secret = sparkai_api_secret
        self.sparkai_domain = sparkai_domain
        self.base_url = base_url
        self.sparkai_url = sparkai_url


    def search(self, keyword: str, **kwargs)->List[str]:
        new_data=self.http_serice_extract_contents(keyword)
        return new_data

    def set_config(self, **kwargs):
        """设置配置"""
        config_keys = ['api_password', 'sparkai_app_id', 'sparkai_api_key',
                       'sparkai_api_secret', 'sparkai_domain', 'base_url', 'sparkai_url']

        for key in config_keys:
            if key in kwargs:
                setattr(self, key, kwargs[key])

    def http_serice(self,keyword)-> Union[SearchResponseType, str]:
        url = self.base_url+"chat/completions"
        data = {
            "model": self.sparkai_domain,  # 指定请求的模型
            "messages": [
                {
                    "role": "user",
                    "content": keyword
                }
            ]
        }
        header = {
            "Authorization": "Bearer "+self.api_password  # 注意此处把“123456”替换为自己的APIPassword
        }
        response = requests.post(url, headers=header, json=data)
        return response.json()

    def http_serice_extract_contents(self,keyword:str)-> List[str]:
        """
        过滤后的数据
        :return:
        """
        yuan_data=self.http_serice(keyword)
        new_data=[]
        if yuan_data.get("choices") and len(yuan_data.get("choices"))>0:
            for i in yuan_data.get("choices"):
                if i.get("message") and i.get("message").get("content"):
                    new_data.append(i.get("message").get("content"))
        return new_data

    def websoket_service(self,keyword):
        spark = ChatSparkLLM(
            spark_api_url=self.sparkai_url,
            spark_app_id=self.sparkai_app_id,
            spark_api_key=self.sparkai_api_key,
            spark_api_secret=self.sparkai_api_secret,
            spark_llm_domain=self.sparkai_domain,
            streaming=False,
        )
        messages = [ChatMessage(
            role="user",
            content=keyword
        )]
        handler = ChunkPrintHandler()
        a = spark.generate([messages], callbacks=[handler])
        print(a)