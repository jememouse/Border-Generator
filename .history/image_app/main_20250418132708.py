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
    return {"image_path": image_path, "prompt": request.prompt}

if __name__ == "__main__":
    import uvicorn
    # 运行 FastAPI 应用，注意这里的路径是相对于 main.py 的
    # 在实际部署时，通常使用 Gunicorn 或其他 ASGI 服务器
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
