import sys, os
base_path = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(base_path, "modules"))
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import vision_module
import image_generator

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/multi-steps")
async def run_workflow(goal: str = Form(...), files: list[UploadFile] = File(...)):
    image = files[0]
    img_bytes = await image.read()
    step_result = vision_module.analyse_image_plan(img_bytes, goal)
    steps = step_result["steps"]

    output_steps = []
    for idx, s in enumerate(steps):
        output_steps.append({
            "title": s.get("title", f"阶段{idx+1}"),
            "action": s.get("action", s.get("desc","")),
            "scene_cn": s.get("scene_cn", ""),
            "scene_en": s.get("scene_en", s.get("draw_prompt",""))
        })

    return {
        "object_desc": step_result.get("object_desc", ""),
        "steps": output_steps
    }

class GenImageReq(BaseModel):
    prompt: str

@app.post("/api/generate-image")
async def gen_image(req: GenImageReq):
    try:
        urls = image_generator.generate_all([req.prompt])
        url = urls[0]
        return {"image_url": url}
    except RuntimeError:
        return {"image_url": ""}

app.mount("/", StaticFiles(directory="public", html=True))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000)
