# -*- coding: utf-8 -*-
"""③ 步骤生成模块：关系类型 -> 5个具体可量化步骤（含插画场景描述）"""
import json
import os

from openai import OpenAI

BASE_URL = "https://api-inference.modelscope.cn/v1/"
LLM_MODEL = "Qwen/Qwen3.5-35B-A3B"


def _get_client():
    key = "ms-2d8fee51-97ee-4e44-8a87-a3d75928aa32"
    if not key:
        raise RuntimeError("未设置 MODELSCOPE_API_KEY")
    return OpenAI(base_url=BASE_URL, api_key=key)


def generate_steps(judgment: dict, object_desc: str, goal: str, n: int = 5) -> list:
    """返回长度=n 的列表，每项含 title / action / why / scene 四个字段"""
    client = _get_client()
    prompt = (
        f"物品：{object_desc}；目标：{goal}；判定结果：{json.dumps(judgment, ensure_ascii=False)}。\n"
        f"请基于该关系的成功路径，给出恰好{n}个实际、具体、可量化的行动步骤。\n"
        f"每个步骤含4个字段：title(4-8字)、action(怎么做，含数字/时间/频率)、"
        f"why(为什么有效)、scene(一句话可画成插画的画面)。\n"
        f"只输出JSON数组，不要多余内容："
        f"[{{\"title\":...,\"action\":...,\"why\":...,\"scene\":...}}, ...]"
    )
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system",
             "content": "你是生成可执行方案的行动规划师，步骤必须具体、可量化、不灌鸡汤。"},
            {"role": "user", "content": prompt},
        ],
    )
    text = resp.choices[0].message.content.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    steps = json.loads(text)
    return steps[:n]
