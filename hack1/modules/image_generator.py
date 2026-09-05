# -*- coding: utf-8 -*-
"""⑤ 配图生成模块：文生图（异步任务 + 轮询），支持多模型一键切换"""
import json
import os
import time
import requests
from io import BytesIO
from PIL import Image

SUBMIT_URL = "https://api-inference.modelscope.cn/v1/images/generations"
TASK_URL = "https://api-inference.modelscope.cn/v1/tasks"
IMAGE_MODEL = "Qwen/Qwen-Image"
# 需要强制异步头的模型（Qwen-Image 不在其中：它不需要，会自动返回异步任务）
NEED_ASYNC_HEADER = {"Kwai-Kolors/Kolors", "AI-ModelScope/FLUX.1-schnell"}
POLL_INTERVAL = 5
MAX_ATTEMPTS = 40
MAX_RETRY = 8
RETRY_WAIT = 10

def _headers():
    key = "ms-2d8fee51-97ee-4e44-8a87-a3d75928aa32"
    if not key:
        raise ValueError("API Key不能为空")
    h = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if IMAGE_MODEL in NEED_ASYNC_HEADER:
        h["X-ModelScope-Async-Mode"] = "true"
    return h

def _submit(prompt: str) -> str:
    for attempt in range(MAX_RETRY):
        resp = requests.post(
            SUBMIT_URL,
            headers=_headers(),
            data=json.dumps({"model": IMAGE_MODEL, "prompt": prompt}, ensure_ascii=False).encode(),
            timeout=60,
        )
        if resp.status_code == 429 or (resp.status_code == 400 and "40212" in resp.text):
            wait = RETRY_WAIT * (attempt + 1)
            print(f"    限流/排队限制({resp.status_code})，等 {wait}s 自动重试 ({attempt + 1}/{MAX_RETRY})", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            raise RuntimeError(f"提交任务失败 HTTP {resp.status_code}：{resp.text[:500]}")
        data = resp.json()
        task_id = data.get("task_id")
        if not task_id:
            raise RuntimeError(f"提交任务失败，响应：{data}")
        return task_id
    raise RuntimeError("重试 8 次仍受限，请等 10 分钟后再跑")

def _poll(task_id: str) -> str:
    headers = {**_headers(), "X-ModelScope-Task-Type": "image_generation"}
    for _ in range(MAX_ATTEMPTS):
        resp = requests.get(f"{TASK_URL}/{task_id}", headers=headers, timeout=60)
        if resp.status_code != 200:
            time.sleep(POLL_INTERVAL)
            continue
        data = resp.json()
        images = data.get("output_images")
        if images:
            return images[0]
        output = data.get("output", data)
        status = output.get("task_status") or data.get("task_status") or ""
        if status in ("SUCCEED", "SUCCEEDED", "FINISHED"):
            for key in ("results", "images", "generated_images"):
                if key in output and output[key]:
                    url = output[key][0].get("url")
                    if url:
                        return url
            raise RuntimeError(f"任务成功但没找到图片URL：{data}")
        if status in ("FAILED", "FAIL", "CANCELED"):
            raise RuntimeError(f"图片生成失败：{data}")
        time.sleep(POLL_INTERVAL)
    raise RuntimeError("图片生成超时")

def gen_one(prompt: str) -> str:
    """修改返回值：直接返回图片在线URL，不返回PIL对象，前端可以直接渲染"""
    print("    ⏳ 开始生成一张图...", flush=True)
    task_id = _submit(prompt)
    img_url = _poll(task_id)
    return img_url

def generate_all(prompts: list) -> list:
    """串行生成图片url列表"""
    return [gen_one(p) for p in prompts]
