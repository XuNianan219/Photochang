# -*- coding: utf-8 -*-
"""文生图模型体检：依次测 3 个模型，看哪个能出图"""
import json
import requests

url = "https://api-inference.modelscope.cn/v1/images/generations"
# 直接赋值密钥，不再使用 os.environ（修复KeyError报错）
api_key = "ms-2d8fee51-97ee-4e44-8a87-a3d75928aa32"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
# deepseek视觉模型不支持文生图接口，这里只保留Qwen绘图模型
models = [
    "Qwen/Qwen-Image",
    "deepseek-ai/DeepSeek-V4-Flash-Vision-Exp"
]
for m in models:
    print("=" * 40)
    print(f"测试模型：{m}")
    try:
        r = requests.post(
            url,
            headers=headers,
            data=json.dumps({"model": m, "prompt": "一只淡雅水彩风格的小猫，柔和暖色调，大留白"},
                            ensure_ascii=False).encode(),
            timeout=120,
        )
        print(f"HTTP 状态码：{r.status_code}")
        print("返回内容（前 600 字）：")
        print(r.text[:600])
    except Exception as e:
        print(f"异常：{type(e).__name__}: {e}")
    print()
