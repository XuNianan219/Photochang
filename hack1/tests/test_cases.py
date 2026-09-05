# -*- coding: utf-8 -*-
"""30 组测试用例：10 物品 × 3 目标
用法：把 10 张物品照片放到 assets/examples/ 下，然后运行：python tests/test_cases.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules import vision_module, relation_engine, step_generator, prompt_builder

STYLE = prompt_builder.load_style()
EXAMPLES = Path(__file__).parent.parent / "examples"/"bottles.jpg"

GOALS = ["考上研究生", "去冰岛旅行", "成为作家"]

CASES = [
    {"object": "水瓶",   "file": "bottle.jpg",   "expect": ["滋养型"]},
    {"object": "笔",     "file": "pen.jpg",      "expect": ["工具型"]},
    {"object": "旧伞",   "file": "umbrella.jpg", "expect": ["远方型"]},
    {"object": "闹钟",   "file": "alarm.jpg",    "expect": ["催化型"]},
    {"object": "镜子",   "file": "mirror.jpg",   "expect": ["镜像型"]},
    {"object": "旧书",   "file": "book.jpg",     "expect": ["锚定型", "滋养型"]},
    {"object": "锁",     "file": "lock.jpg",     "expect": ["障碍型"]},
    {"object": "车票",   "file": "ticket.jpg",   "expect": ["桥梁型"]},
    {"object": "耳机",   "file": "earphone.jpg", "expect": ["工具型", "锚定型"]},
    {"object": "石头",   "file": "stone.jpg",    "expect": ["远方型", "锚定型"]},
]


def run_all():
    passed = 0
    total = len(CASES) * len(GOALS)
    for c in CASES:
        img_path = EXAMPLES / c["file"]
        for goal in GOALS:
            try:
                if not img_path.exists():
                    print(f"[SKIP] 缺少照片 {img_path}")
                    continue
                desc = vision_module.describe_object(str(img_path))
                jd = relation_engine.judge(desc, goal)
                ok = any(e in jd["main"] for e in c["expect"])
                steps = step_generator.generate_steps(jd, desc, goal)
                ok = ok and len(steps) == 5
                prompts = prompt_builder.build_prompts(steps, STYLE)
                ok = ok and all(("水彩" in p) for p in prompts)
                passed += ok
                print(f"[{'PASS' if ok else 'FAIL'}] {c['object']} + {goal} -> {jd['main']}")
            except Exception as e:
                print(f"[ERROR] {c['object']} + {goal}: {e}")
    print(f"\n{passed}/{total} 通过")


if __name__ == "__main__":
    run_all()
