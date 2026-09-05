# -*- coding: utf-8 -*-
"""④ 配图 Prompt 构建模块：每个步骤 -> 一条统一水彩画风的文生图描述"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_style() -> dict:
    with open(DATA_DIR / "style_config.json", encoding="utf-8") as f:
        return json.load(f)


def build_prompts(steps: list, style: dict = None) -> list:
    style = style or load_style()
    return [
        f"{style['prefix']}，画面{i + 1}：{st['scene']}，{style['suffix']}"
        for i, st in enumerate(steps)
    ]
