# -*- coding: utf-8 -*-
"""魔搭多模态：接收图片+用户目标，生成结构化分步方案，支持励志激励方案 / 实物改造"""
import json
import os
import re
import base64
import requests

VISION_URL = "https://api-inference.modelscope.cn/v1/chat/completions"

def analyse_image_plan(image_bytes: bytes, user_goal: str):
    key = "ms-2d8fee51-97ee-4e44-8a87-a3d75928aa32"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    b64_img = base64.b64encode(image_bytes).decode("utf-8")

    system_prompt = f"""
你的任务：结合用户提供的实物图片 + 用户最终目标，设计一套可落地的分步执行方案。
规则：
1. 如果目标不是改造物体外观（例如考研、减肥、备考）：**不要修改物品本身，把这个物品作为精神激励/仪式道具**，设计完整行动计划。
2. 如果目标是手工DIY改造外观：输出实物改造步骤。
3. 输出严格是JSON，**禁止多余解释文字、markdown、代码块**。
字段定义：
success_probability：0~100的整数，代表这套方案实现目标的预估成功率
steps：数组，每一项包含
    desc：给人阅读的完整中文行动步骤
    draw_prompt：英文写实绘图提示词，用来生成这个步骤的效果图

示例参考（物品：一瓶水，目标：考上研究生）：
{{
  "success_probability": 76,
  "steps":[
    {{
      "desc":"把这瓶水当作每日打卡信物，每次完成一套真题，喝一口水作为奖励",
      "draw_prompt":"A student finishes mock exam, takes a sip from a water bottle as reward, warm study room, realistic photo"
    }},
    {{
      "desc":"在瓶身写下考研倒计时，每天学习前看一眼自我激励",
      "draw_prompt":"Handwritten exam countdown text on a plastic water bottle on a study desk, soft lighting, realistic"
    }},
    {{
      "desc":"坚持每日学习打卡，直到考研结束，完成最终目标",
      "draw_prompt":"Happy student celebrating passing postgraduate entrance exam with the water bottle on desk"
    }}
  ]
}}

用户目标：{user_goal}
严格只返回JSON，不要任何额外文字！
""".strip()

    payload = {
        "model": "Qwen/Qwen3.5-35B-A3B",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                ]
            }
        ],
        "stream": False
    }

    resp = requests.post(VISION_URL, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"视觉模型调用失败 {resp.status_code}: {resp.text}")

    raw_text = resp.json()["choices"][0]["message"]["content"]
    match = re.search(r"\{[\s\S]*\}", raw_text)
    if not match:
        raise RuntimeError(f"模型没有返回合法JSON：{raw_text}")
    json_str = match.group(0)
    result = json.loads(json_str)
    return result

