from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import uuid

from vision_analyzer import analyse_image_plan
from image_generator import generate_all

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# 内存任务池（开发阶段）
task_store = {}

class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

async def background_work(task_id: str, img_bytes: bytes, goal_text: str):
    try:
        task_store[task_id]["status"] = TaskStatus.RUNNING
        # 1️⃣ 多模态分析图片，拿到步骤和绘图prompt
        vision_result = analyse_image_plan(img_bytes, goal_text)
        draw_prompt_list = [s["draw_prompt"] for s in vision_result["steps"]]
        desc_list = [s["desc"] for s in vision_result["steps"]]

        # 2️⃣ 串行生成每一张效果图URL
        loop = asyncio.get_event_loop()
        image_urls = await loop.run_in_executor(None, generate_all, draw_prompt_list)

        # 组装前端渲染数组
        step_list = []
        for desc, url in zip(desc_list, image_urls):
            step_list.append({"desc": desc, "image_url": url})

        task_store[task_id] = {
            "status": TaskStatus.SUCCESS,
            "success_probability": vision_result["success_probability"],
            "step_list": step_list
        }
    except Exception as e:
        task_store[task_id]["status"] = TaskStatus.FAILED
        task_store[task_id]["msg"] = str(e)

# 提交任务接口
@app.post("/api/submit")
async def submit_task(goal_text: str = Form(...), image: UploadFile = Form(...)):
    task_id = str(uuid.uuid4())
    img_bytes = await image.read()
    task_store[task_id] = {"status": TaskStatus.PENDING}
    # 后台异步运行，不会阻塞前端
    asyncio.create_task(background_work(task_id, img_bytes, goal_text))
    return {"task_id": task_id}

# 查询任务结果接口
@app.get("/api/result/{task_id}")
async def get_result(task_id: str):
    if task_id not in task_store:
        return {"status": "not_found"}
    return task_store[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000)
