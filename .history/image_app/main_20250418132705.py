from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import image_generator  # 导入我们之前创建的图像生成模块

app = FastAPI()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

class ImageRequest(BaseModel):
    prompt: str

@app.get("/")
async def read_index():
    """提供前端 HTML 文件"""
    return FileResponse('static/index.html')

@app.post("/generate-image/")
async def generate_image_endpoint(request: ImageRequest):
    """接收前端请求，调用图像生成逻辑"""
    image_path = image_generator.generate_image(request.prompt)
    # 在实际应用中，这里可能返回图像文件或图像 URL
