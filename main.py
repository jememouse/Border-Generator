# main.py
# -*- coding: utf-8 -*-
from fastapi import FastAPI, Form, HTTPException, Request # 从 FastAPI 导入所需组件
from fastapi.responses import StreamingResponse, HTMLResponse # 用于返回流式响应(图片)和HTML响应
from fastapi.staticfiles import StaticFiles # 用于提供静态文件服务
# from fastapi.templating import Jinja2Templates # 如果需要模板引擎则取消注释
from PIL import Image # 导入 Pillow 库
import io # 用于内存中的字节流操作
import logging

# 从我们重构的模块中导入函数和样式参数
from image_generator import (
    mm_to_pixels,
    pt_to_pixels,
    create_bordered_image,
    STYLE1_PARAMS,
    STYLE2_PARAMS
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建 FastAPI 应用实例
app = FastAPI(title="图像生成器 API", description="根据参数生成带边框的图像")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- 辅助函数：处理请求并生成图像 ---
def process_image_request(style_params: dict, dpi: int,
                          outer_width_mm: float, outer_height_mm: float, outer_shape_type: str,
                          inner_width_mm: float, inner_height_mm: float, inner_shape_type: str,
                          inner_corner_radius_mm: float):
    """
    处理通用的计算和调用图像生成器的逻辑。
    返回包含 PNG 图像数据的 BytesIO 流，或者抛出 HTTPException。
    """
    try:
        # --- 1. 计算像素值 ---
        logging.info("开始计算像素值...")
        outer_width_px = mm_to_pixels(outer_width_mm, dpi)
        outer_height_px = mm_to_pixels(outer_height_mm, dpi)
        inner_width_px = mm_to_pixels(inner_width_mm, dpi)
        inner_height_px = mm_to_pixels(inner_height_mm, dpi)
        # 仅当内框是矩形时计算圆角像素值
        inner_corner_radius_px = mm_to_pixels(inner_corner_radius_mm, dpi) if inner_shape_type == 'rectangle' else 0

        # 计算样式特定参数的像素值
        stroke_width_px = pt_to_pixels(style_params["stroke_width_pt"], dpi)
        diagonal_line_width_px = pt_to_pixels(style_params["diagonal_line_width_pt"], dpi)
        outer_border_pattern_spacing_px = mm_to_pixels(style_params["outer_border_pattern_spacing_mm"], dpi)
        inner_fill_pattern_spacing_px = mm_to_pixels(style_params["inner_fill_pattern_spacing_mm"], dpi)
        # 确保图案间距至少为1像素 (如果原始毫米值>0)
        if style_params["outer_border_pattern_spacing_mm"] > 0 and outer_border_pattern_spacing_px < 1:
             outer_border_pattern_spacing_px = 1
        if style_params["inner_fill_pattern_spacing_mm"] > 0 and inner_fill_pattern_spacing_px < 1:
             inner_fill_pattern_spacing_px = 1
        logging.info(f"计算得到的像素: 外框={outer_width_px}x{outer_height_px}, 内框={inner_width_px}x{inner_height_px}, 圆角={inner_corner_radius_px}, 描边={stroke_width_px}")

        # --- 2. 计算调整后的 DPI 以便精确保存 ---
        adjusted_dpi_w = (outer_width_px * 25.4 / outer_width_mm) if outer_width_mm > 0 else float(dpi)
        adjusted_dpi_h = (outer_height_px * 25.4 / outer_height_mm) if outer_height_mm > 0 else float(dpi)
        logging.info(f"输入 DPI: {dpi}, 调整后保存 DPI (宽, 高): ({adjusted_dpi_w:.2f}, {adjusted_dpi_h:.2f})")

        # --- 3. 调用核心图像生成函数 ---
        logging.info(f"调用 create_bordered_image, 外形='{outer_shape_type}', 内形='{inner_shape_type}'")
        image_obj = create_bordered_image(
            outer_width_px=outer_width_px, outer_height_px=outer_height_px,
            inner_width_px=inner_width_px, inner_height_px=inner_height_px,
            inner_corner_radius_px=inner_corner_radius_px,
            outer_shape_type=outer_shape_type, inner_shape_type=inner_shape_type,
            # 直接从选定的样式字典传递样式参数
            outer_border_type=style_params["outer_border_type"],
            outer_border_color1=style_params["outer_border_color1"],
            outer_border_color2=style_params["outer_border_color2"],
            outer_border_pattern_spacing_px=outer_border_pattern_spacing_px,
            outer_stroke_color=style_params["outer_stroke_color"],
            outer_stroke_width_px=stroke_width_px, # 使用计算得到的像素值
            inner_fill_type=style_params["inner_fill_type"],
            inner_fill_color1=style_params["inner_fill_color1"],
            inner_fill_color2=style_params["inner_fill_color2"],
            inner_fill_pattern_spacing_px=inner_fill_pattern_spacing_px,
            inner_stroke_color=style_params["inner_stroke_color"],
            inner_stroke_width_px=stroke_width_px, # 使用计算得到的像素值
            diagonal_line_width_px=diagonal_line_width_px # 使用计算得到的像素值
        )

        # 检查图像是否成功生成
        if not isinstance(image_obj, Image.Image):
            logging.error("核心函数 create_bordered_image 未返回有效的 Image 对象。")
            raise HTTPException(status_code=500, detail="图像生成失败 (内部错误)")

        # --- 4. 将图像保存到内存缓冲区 ---
        logging.info("将图像保存到内存缓冲区...")
        img_byte_arr = io.BytesIO() # 创建内存字节流对象
        # 使用调整后的 DPI 保存为 PNG 格式
        image_obj.save(img_byte_arr, format='PNG', dpi=(adjusted_dpi_w, adjusted_dpi_h))
        img_byte_arr.seek(0) # 将流的位置重置到开头，以便读取
        logging.info("图像已保存到内存。")
        return img_byte_arr

    except ValueError as ve: # 捕获像无效数字格式这样的特定错误
        logging.error(f"处理过程中发生值错误: {ve}")
        raise HTTPException(status_code=400, detail=f"输入参数无效: {ve}") # 返回 400 Bad Request
    except Exception as e:
        logging.exception(f"处理图像请求时发生意外错误: {e}") # 记录完整的错误堆栈
        raise HTTPException(status_code=500, detail=f"图像生成时发生意外错误: {str(e)}") # 返回 500 Internal Server Error

# --- API 端点 (Endpoints) ---

@app.get("/", response_class=HTMLResponse, summary="获取主页界面")
async def get_index_page(request: Request):
    """提供主要的 HTML 用户界面。"""
    logging.info("请求访问主页 /")
    try:
        # 直接读取并返回 static 目录下的 HTML 文件内容
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logging.error("无法找到 static/index.html 文件")
        raise HTTPException(status_code=500, detail="服务器内部错误: 无法加载界面文件。")

@app.post("/generate_image_style1/", response_class=StreamingResponse, summary="生成样式1的图像")
async def generate_image_style1(
    # 使用 Form(...) 从 HTML 表单接收数据
    dpi: int = Form(300, ge=72, le=1200, description="分辨率 (DPI)"),
    outer_width_mm: float = Form(60.0, gt=0, description="外框宽度 (mm)"),
    outer_height_mm: float = Form(92.0, gt=0, description="外框高度 (mm)"),
    outer_shape_type: str = Form('rectangle', description="外框形状 ('rectangle' 或 'ellipse')"),
    inner_width_mm: float = Form(54.0, ge=0, description="内框宽度 (mm)"),
    inner_height_mm: float = Form(86.0, ge=0, description="内框高度 (mm)"),
    inner_shape_type: str = Form('rectangle', description="内框形状 ('rectangle' 或 'ellipse')"),
    inner_corner_radius_mm: float = Form(3.18, ge=0, description="内框圆角半径 (mm, 仅矩形有效)")
):
    """根据传入的几何参数，使用预设的样式1生成图像。"""
    logging.info(f"收到生成样式1图像的请求, DPI={dpi}, 外框={outer_width_mm}x{outer_height_mm} ({outer_shape_type})")
    # 调用辅助函数处理请求
    img_buffer = process_image_request(
        STYLE1_PARAMS, dpi, outer_width_mm, outer_height_mm, outer_shape_type,
        inner_width_mm, inner_height_mm, inner_shape_type, inner_corner_radius_mm
    )
    # 返回包含图像数据的流式响应
    return StreamingResponse(img_buffer, media_type="image/png")

@app.post("/generate_image_style2/", response_class=StreamingResponse, summary="生成样式2的图像")
async def generate_image_style2(
    # 参数与样式1完全相同，因为几何形状是共享的
    dpi: int = Form(300, ge=72, le=1200, description="分辨率 (DPI)"),
    outer_width_mm: float = Form(60.0, gt=0, description="外框宽度 (mm)"),
    outer_height_mm: float = Form(92.0, gt=0, description="外框高度 (mm)"),
    outer_shape_type: str = Form('rectangle', description="外框形状 ('rectangle' 或 'ellipse')"),
    inner_width_mm: float = Form(54.0, ge=0, description="内框宽度 (mm)"),
    inner_height_mm: float = Form(86.0, ge=0, description="内框高度 (mm)"),
    inner_shape_type: str = Form('rectangle', description="内框形状 ('rectangle' 或 'ellipse')"),
    inner_corner_radius_mm: float = Form(3.18, ge=0, description="内框圆角半径 (mm, 仅矩形有效)")
):
    """根据传入的几何参数，使用预设的样式2生成图像。"""
    logging.info(f"收到生成样式2图像的请求, DPI={dpi}, 外框={outer_width_mm}x{outer_height_mm} ({outer_shape_type})")
    # 调用辅助函数处理请求
    img_buffer = process_image_request(
        STYLE2_PARAMS, dpi, outer_width_mm, outer_height_mm, outer_shape_type,
        inner_width_mm, inner_height_mm, inner_shape_type, inner_corner_radius_mm
    )
    # 返回包含图像数据的流式响应
    return StreamingResponse(img_buffer, media_type="image/png")

# --- 可选：添加一个简单的健康检查端点 ---
@app.get("/health", summary="服务健康检查")
async def health_check():
    """检查服务是否正常运行。"""
    logging.debug("健康检查 /health")
    return {"status": "ok", "message": "服务运行正常"}