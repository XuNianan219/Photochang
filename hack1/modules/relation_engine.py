# -*- coding: utf-8 -*-
"""② 关系判定模块：物品特征 + 目标 -> 8种关系之一（可混合型）+ 匹配度 + 理由"""
import json
import os

from openai import OpenAI

BASE_URL = "https://api-inference.modelscope.cn/v1/"
LLM_MODEL = "Qwen/Qwen3.5-35B-A3B"

SYSTEM = """你是「关系翻译机」的判定引擎。给你一件物品的描述 + 一个目标，判断两者之间的"关系类型"。
8种关系（可以是混合型）：
1.滋养型：被消耗→被补充→循环，路径=持续积累/瓶颈期补给
2.工具型：被使用→直接产生结果，路径=方法论/精准发力
3.桥梁型：连接两端/过渡，路径=分阶段推进
4.催化型：触发加速/不消耗，路径=抓住转折点/一次突破
5.镜像型：忠实映照状态，路径=自我认知/调整策略
6.锚定型：沉底稳住不动摇，路径=固定节奏/不漂移
7.障碍型：阻挡需克服，路径=识别/拆解障碍
8.远方型：看似无关、深层交汇，路径=跳出线性思维

只输出JSON，不要多余内容：
{"main":"滋养型","weights":[{"type":"滋养型","weight":0.7},{"type":"锚定型","weight":0.3}],"reason":"一句话理由"}"""


def _get_client():
    key = "ms-2d8fee51-97ee-4e44-8a87-a3d75928aa32"
    if not api_key:
        raise RuntimeError("未设置环境变量 MODELSCOPE_API_KEY，请先配置魔搭令牌")
    return OpenAI(base_url=BASE_URL, api_key=api_key)


def judge(object_desc: str, goal: str) -> dict:
    """返回 {"main", "weights", "reason"}"""
    client = _get_client()
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"物品：{object_desc}\n目标：{goal}"},
        ],
    )
    text = resp.choices[0].message.content.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)
