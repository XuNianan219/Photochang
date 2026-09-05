# -*- coding: utf-8 -*-
"""调试 FLUX.1-schnell：提交一张图，打印每次轮询的原始返回"""
import json
import os
import time
import requests

url = "https://api-inference.modelscope.cn/v1/images/generations"
task_url = "https://api-inference.modelscope.cn/v1/tasks"
key = os.environ["MODELSCOPE_API_KEY"]

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "X-ModelScope-Async-Mode": "true",   # 所有文生图都要这个头
}

# ① 提交
r = requests.post(url, headers=headers,
    data=json.dumps({"model": "Qwen/Qwen-Image",
                     "prompt": "一个古风英俊潇洒3D建模的男子"}, ensure_ascii=False).encode(),
    timeout=60)
print("提交 HTTP:", r.status_code, flush=True)
print("提交响应:", r.text[:500], flush=True)
if r.status_code != 200:
    raise SystemExit(1)
task_id = r.json().get("task_id")
print("task_id:", task_id, flush=True)

# ② 轮询：每次打印原始返回
poll_headers = {**headers, "X-ModelScope-Task-Type": "image_generation"}
for i in range(60):
    time.sleep(10)
    rr = requests.get(f"{task_url}/{task_id}", headers=poll_headers, timeout=60)
    print(f"--- 第{i + 1}次  HTTP {rr.status_code} ---", flush=True)
    print(rr.text[:800], flush=True)
    try:
        data = rr.json()
    except Exception:
        continue
    images = data.get("output_images")
    if images:
        print("✅ 找到图片URL:", images[0], flush=True)
        break
    output = data.get("output", data)
    status = output.get("task_status") or data.get("task_status") or ""
    if status in ("FAILED", "FAIL", "CANCELED"):
        print("❌ 任务失败", flush=True)
        break
print("结束", flush=True)
