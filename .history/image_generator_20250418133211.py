# image_generator.py
# -*- coding: utf-8 -*-
"""
核心图像生成逻辑，使用 Pillow 库。
从原始脚本调整而来，用作一个模块。
"""

from PIL import Image, ImageDraw, ImageColor
import math
import logging # 使用 logging 记录服务器端信息，替代 print

# 配置基础日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 辅助函数 (大部分不变, 移除了输入函数) ---

def mm_to_pixels(mm, dpi):
    """将毫米转换为像素"""
    if mm is None: return 0
    try: return round(float(mm) / 25.4 * float(dpi))
    except ValueError: logging.error(f"无效的毫米值: '{mm}'"); return 0

def pt_to_pixels(pt, dpi):
    """将磅 (points) 转换为像素"""
    if pt is None: return 0
    try: return max(1, math.ceil(float(pt) / 72.0 * float(dpi))) # 至少为1像素
    except ValueError: logging.error(f"无效的磅值: '{pt}'"); return 1

# 移除了: get_float_input, get_int_input, get_color_input, get_numbered_choice_input

# --- 图案绘制函数 (不变) ---
def draw_diagonal_lines(draw_context, image_size, color1, color2, spacing_px, line_width_px):
    """绘制斜线图案"""
    width, height = image_size
    line_width_px = max(1, line_width_px) # 确保线宽至少为1
    spacing_px = max(line_width_px, spacing_px) # 确保间距不小于线宽
    if width <= 0 or height <= 0: return
    # 确保 color1 是有效的 RGBA 元组
    if color1 and isinstance(color1, tuple) and len(color1) == 4 and color1[3] > 0:
        for k in range(0 - height, width + height, spacing_px):
             draw_context.line([ (k-height, 0) , (width, width-k+height) ], fill=color1, width=line_width_px)
    # 注意：原始脚本的此函数似乎未使用 color2

def draw_checkerboard(draw_context, image_size, color1, color2, check_size_px):
    """绘制棋盘格图案"""
    width, height = image_size
    check_size_px = max(1, check_size_px) # 确保格子尺寸至少为1
    if width <= 0 or height <= 0: return
    for r in range(0, height, check_size_px):
        for c in range(0, width, check_size_px):
            row_idx = r // check_size_px
            col_idx = c // check_size_px
            # 交替使用 color1 和 color2
            current_color = color1 if (row_idx + col_idx) % 2 == 0 else color2
            # 确保颜色有效且透明度大于0才绘制
            if current_color and isinstance(current_color, tuple) and len(current_color) == 4 and current_color[3] > 0:
                c_end = min(c + check_size_px, width) # 防止超出图像边界
                r_end = min(r + check_size_px, height) # 防止超出图像边界
                draw_context.rectangle([(c, r), (c_end, r_end)], fill=current_color, outline=None)


# --- 核心图像生成函数 (修改后) ---
def create_bordered_image( # 轻微重命名，移除 'interactive'
    # 几何参数 (像素) - 由调用者 (FastAPI 端点) 计算传入
    outer_width_px: int, outer_height_px: int,
    inner_width_px: int, inner_height_px: int,
    inner_corner_radius_px: int,
    outer_shape_type: str, # 'rectangle' 或 'ellipse'
    inner_shape_type: str, # 'rectangle' 或 'ellipse'
    # 样式参数 - 特定于要生成的图像
    outer_border_type: str, outer_border_color1: tuple, outer_border_color2: tuple or None,
    outer_border_pattern_spacing_px: int, outer_stroke_color: tuple or None, outer_stroke_width_px: int,
    inner_fill_type: str, inner_fill_color1: tuple, inner_fill_color2: tuple or None,
    inner_fill_pattern_spacing_px: int, inner_stroke_color: tuple or None, inner_stroke_width_px: int,
    diagonal_line_width_px: int
) -> Image.Image | None: # 返回 PIL Image 对象或在失败时返回 None
    """
    根据提供的像素尺寸和样式参数生成带边框的图像。
    返回一个 PIL Image 对象，如果发生错误则返回 None。
    """
    canvas_width_px = outer_width_px
    canvas_height_px = outer_height_px
    logging.info(f"开始生成图像: 画布={canvas_width_px}x{canvas_height_px}px, 内框={inner_width_px}x{inner_height_px}px")

    # --- 参数验证 (从原始脚本复制并调整，使用 logging) ---
    if canvas_width_px <= 0 or canvas_height_px <= 0: logging.error("无效的画布尺寸。"); return None
    if inner_width_px < 0 or inner_height_px < 0: logging.error("内框尺寸不能为负数。"); return None
    # 通常内框不应大于外框，但暂时允许以支持特殊效果
    # if inner_width_px > canvas_width_px or inner_height_px > canvas_height_px: logging.warning("内框尺寸超出画布尺寸。");
    if inner_corner_radius_px < 0: inner_corner_radius_px = 0
    outer_stroke_width_px = max(1, outer_stroke_width_px) # 描边至少1像素
    inner_stroke_width_px = max(1, inner_stroke_width_px)
    diagonal_line_width_px = max(1, diagonal_line_width_px)

    # --- 计算坐标等 (从原始脚本复制并调整) ---
    # 将内框居中
    inner_x0 = round((canvas_width_px - inner_width_px) / 2.0)
    inner_y0 = round((canvas_height_px - inner_height_px) / 2.0)
    inner_x1 = inner_x0 + inner_width_px
    inner_y1 = inner_y0 + inner_height_px

    # 定义绘图用的边界框 (Pillow 通常使用 [x0, y0, x1, y1])
    outer_bbox = [0, 0, canvas_width_px, canvas_height_px]
    inner_bbox = [inner_x0, inner_y0, inner_x1, inner_y1]

    has_valid_inner_area = (inner_width_px > 0 and inner_height_px > 0) # 内框是否有有效面积
    border_width_x = (canvas_width_px - inner_width_px) / 2.0 # 边框 X 方向宽度
    border_width_y = (canvas_height_px - inner_height_px) / 2.0 # 边框 Y 方向宽度
    has_visible_border = border_width_x > 0 or border_width_y > 0 # 是否有可见边框

    # 如果内框是矩形且圆角半径过大，则调整半径
    if has_valid_inner_area and inner_shape_type == 'rectangle':
        max_radius_limit = min(inner_width_px / 2.0, inner_height_px / 2.0)
        inner_corner_radius_px = min(inner_corner_radius_px, max_radius_limit)
        inner_corner_radius_px = max(0, round(inner_corner_radius_px)) # 确保不为负
    elif not has_valid_inner_area: # 如果没有内框，圆角无意义
        inner_corner_radius_px = 0

    # --- 创建图像和遮罩 (Masks) (从原始脚本复制并调整) ---
    try:
        image = Image.new('RGBA', (canvas_width_px, canvas_height_px), (0, 0, 0, 0)) # 创建透明画布
        image_size = (canvas_width_px, canvas_height_px)
        draw = ImageDraw.Draw(image)

        # 创建边框遮罩 (外框形状挖掉内框形状的区域)
        border_mask = Image.new('L', image_size, 0) # 'L' 模式 (灰度), 黑色背景
        border_mask_draw = ImageDraw.Draw(border_mask)
        # 在遮罩上绘制白色外框形状
        if outer_shape_type == 'rectangle':
            border_mask_draw.rectangle(outer_bbox, fill=255) # 白色填充
        elif outer_shape_type == 'ellipse':
            border_mask_draw.ellipse(outer_bbox, fill=255)
        else: # 处理不支持的形状
            logging.warning(f"不支持的外框形状: {outer_shape_type}。默认使用矩形遮罩。")
            border_mask_draw.rectangle(outer_bbox, fill=255)

        # 如果有内框区域，在边框遮罩上挖掉内框形状 (填充为黑色)
        if has_valid_inner_area:
            if inner_shape_type == 'rectangle':
                if inner_corner_radius_px > 0: # 使用圆角矩形
                    border_mask_draw.rounded_rectangle(inner_bbox, radius=inner_corner_radius_px, fill=0) # 黑色填充 (挖洞)
                else: # 使用普通矩形
                    border_mask_draw.rectangle(inner_bbox, fill=0)
            elif inner_shape_type == 'ellipse':
                border_mask_draw.ellipse(inner_bbox, fill=0)
            else: # 处理不支持的形状
                logging.warning(f"不支持的内框形状: {inner_shape_type}。默认使用矩形挖洞。")
                border_mask_draw.rectangle(inner_bbox, fill=0)

        # 创建内框遮罩 (内框形状的区域)
        inner_mask = None
        if has_valid_inner_area:
            inner_mask = Image.new('L', image_size, 0) # 黑色背景
            inner_mask_draw = ImageDraw.Draw(inner_mask)
            # 在遮罩上绘制白色内框形状
            if inner_shape_type == 'rectangle':
                if inner_corner_radius_px > 0:
                    inner_mask_draw.rounded_rectangle(inner_bbox, radius=inner_corner_radius_px, fill=255) # 白色填充
                else:
                    inner_mask_draw.rectangle(inner_bbox, fill=255)
            elif inner_shape_type == 'ellipse':
                inner_mask_draw.ellipse(inner_bbox, fill=255)
            else: # 处理不支持的形状
                logging.warning(f"不支持的内框形状: {inner_shape_type}。默认使用矩形内框遮罩。")
                inner_mask_draw.rectangle(inner_bbox, fill=255)


        # --- 绘制边框填充 (使用边框遮罩) ---
        # 检查边框是否可见、颜色是否有效 (RGBA 且 alpha > 0)
        if has_visible_border and outer_border_color1 and isinstance(outer_border_color1, tuple) and len(outer_border_color1) == 4 and outer_border_color1[3] > 0:
            if outer_border_type == 'solid':
                # 创建纯色图层，并使用 border_mask 将其粘贴到主图像上
                border_layer = Image.new('RGBA', image_size, outer_border_color1)
                image.paste(border_layer, (0, 0), border_mask)
            elif outer_border_type in ['diagonal', 'checkerboard']:
                # 创建透明的图案图层
                border_pattern_layer = Image.new('RGBA', image_size, (0,0,0,0))
                border_pattern_draw = ImageDraw.Draw(border_pattern_layer)
                # 绘制图案
                if outer_border_type == 'diagonal':
                    space_px = max(1, outer_border_pattern_spacing_px)
                    line_px = max(1, diagonal_line_width_px)
                    # 确保 color2 也是有效的元组或 None
                    valid_color2 = outer_border_color2 if isinstance(outer_border_color2, tuple) and len(outer_border_color2) == 4 else None
                    draw_diagonal_lines(border_pattern_draw, image_size, outer_border_color1, valid_color2, space_px, line_px)
                elif outer_border_type == 'checkerboard':
                    check_px = max(1, outer_border_pattern_spacing_px)
                    valid_color2 = outer_border_color2 if isinstance(outer_border_color2, tuple) and len(outer_border_color2) == 4 else (0,0,0,0) # Provide default transparent if None
                    draw_checkerboard(border_pattern_draw, image_size, outer_border_color1, valid_color2, check_px)
                # 使用 border_mask 将图案图层粘贴到主图像上
                image.paste(border_pattern_layer, (0, 0), border_mask)
            else:
                logging.warning(f"不支持的边框填充类型: {outer_border_type}。边框未绘制。")

        # --- 绘制内框填充 (使用内框遮罩) ---
        # 检查内框是否存在、遮罩是否存在、颜色是否有效
        if has_valid_inner_area and inner_mask and inner_fill_color1 and isinstance(inner_fill_color1, tuple) and len(inner_fill_color1) == 4 and inner_fill_color1[3] > 0:
            if inner_fill_type == 'solid':
                inner_fill_layer = Image.new('RGBA', image_size, inner_fill_color1)
                image.paste(inner_fill_layer, (0, 0), inner_mask)
            elif inner_fill_type in ['diagonal', 'checkerboard']:
                inner_pattern_layer = Image.new('RGBA', image_size, (0,0,0,0))
                inner_pattern_draw = ImageDraw.Draw(inner_pattern_layer)
                if inner_fill_type == 'diagonal':
                    space_px = max(1, inner_fill_pattern_spacing_px)
                    line_px = max(1, diagonal_line_width_px)
                    valid_color2 = inner_fill_color2 if isinstance(inner_fill_color2, tuple) and len(inner_fill_color2) == 4 else None
                    draw_diagonal_lines(inner_pattern_draw, image_size, inner_fill_color1, valid_color2, space_px, line_px)
                elif inner_fill_type == 'checkerboard':
                    check_px = max(1, inner_fill_pattern_spacing_px)
                    valid_color2 = inner_fill_color2 if isinstance(inner_fill_color2, tuple) and len(inner_fill_color2) == 4 else (0,0,0,0)
                    draw_checkerboard(inner_pattern_draw, image_size, inner_fill_color1, valid_color2, check_px)
                image.paste(inner_pattern_layer, (0, 0), inner_mask)
            else:
                 logging.warning(f"不支持的内框填充类型: {inner_fill_type}。内框填充未绘制。")

        # --- 绘制内框描边 ---
        # 描边绘制在内框形状周围。Pillow 的 'width' 参数使线居中。
        # 原始脚本使用了一个稍微扩大边界框的方法，我们沿用此方法。
        if has_valid_inner_area and inner_stroke_color and isinstance(inner_stroke_color, tuple) and len(inner_stroke_color) == 4 and inner_stroke_color[3] > 0 and inner_stroke_width_px > 0:
            try:
                # 计算描边用的边界框 (比内框稍大)
                offset = inner_stroke_width_px / 2.0
                stroke_x0 = inner_x0 - offset
                stroke_y0 = inner_y0 - offset
                stroke_x1 = inner_x1 + offset
                stroke_y1 = inner_y1 + offset
                # 使用 [x0, y0, x1, y1] 格式
                stroke_bbox = [round(stroke_x0), round(stroke_y0), round(stroke_x1), round(stroke_y1)]

                # 确保描边边界框有效
                if stroke_bbox[0] < stroke_bbox[2] and stroke_bbox[1] < stroke_bbox[3]:
                    if inner_shape_type == 'rectangle':
                        stroke_radius = inner_corner_radius_px + offset # 相应调整圆角半径
                        stroke_radius = max(0, round(stroke_radius))
                        # 直接在主画布上绘制描边轮廓
                        draw.rounded_rectangle(stroke_bbox, radius=stroke_radius, outline=inner_stroke_color, width=inner_stroke_width_px)
                    elif inner_shape_type == 'ellipse':
                        draw.ellipse(stroke_bbox, outline=inner_stroke_color, width=inner_stroke_width_px)
            except Exception as e:
                logging.error(f"绘制内框描边失败: {e}")

        # --- 绘制外框描边 ---
        # 沿着画布边缘绘制。
        if outer_stroke_color and isinstance(outer_stroke_color, tuple) and len(outer_stroke_color) == 4 and outer_stroke_color[3] > 0 and outer_stroke_width_px > 0:
            try:
                # Pillow 的 width 参数会将线宽居中绘制在边界上。
                # 对于外边界 [0, 0, W, H]，直接绘制通常可以接受。
                outer_stroke_bbox = [0, 0, canvas_width_px, canvas_height_px]
                if outer_shape_type == 'rectangle':
                    draw.rectangle(outer_stroke_bbox, outline=outer_stroke_color, width=outer_stroke_width_px)
                elif outer_shape_type == 'ellipse':
                    # 椭圆描边可能需要稍微调整 box 以使其完全在画布内，但通常直接绘制也可以
                    draw.ellipse(outer_stroke_bbox, outline=outer_stroke_color, width=outer_stroke_width_px)
            except Exception as e:
                logging.error(f"绘制外框描边失败: {e}")

        logging.info("图像生成完成。")
        return image # 返回 PIL Image 对象

    except Exception as e:
        logging.exception(f"图像创建过程中发生错误: {e}") # 记录完整的 traceback
        return None

# --- 预定义的样式参数 (可以移到 main.py 或配置文件中) ---
# 这里保留作为参考，将在 main.py 中使用

STYLE1_PARAMS = {
    "outer_border_type": 'diagonal',                    # 外框填充: 斜线
    "outer_border_color1": (255, 0, 0, 255),            #   颜色1: 红
    "outer_border_color2": (0, 0, 0, 0),                #   颜色2: 透明
    "outer_border_pattern_spacing_mm": 1.5,             #   图案间距: 1.5mm
    "outer_stroke_color": (255, 0, 0, 255),             # 外框描边: 红
    "inner_fill_type": 'solid',                         # 内框填充: 纯色
    "inner_fill_color1": (0, 0, 0, 0),                  #   颜色1: 透明
    "inner_fill_color2": None,                          #   颜色2: 无
    "inner_fill_pattern_spacing_mm": 0,                 #   图案间距: 0
    "inner_stroke_color": (255, 0, 0, 255),             # 内框描边: 红
    "stroke_width_pt": 0.5,                             # 描边宽度 (通用): 0.5pt
    "diagonal_line_width_pt": 0.3                       # 斜线线宽: 0.3pt
}

STYLE2_PARAMS = {
    "outer_border_type": 'solid',                       # 外框填充: 纯色
    "outer_border_color1": (237, 237, 237, 255),        #   颜色1: 浅灰/白
    "outer_border_color2": None,                        #   颜色2: 无
    "outer_border_pattern_spacing_mm": 0,               #   图案间距: 0
    "outer_stroke_color": (0, 0, 0, 0),                 # 外框描边: 透明 (无)
    "inner_fill_type": 'solid',                         # 内框填充: 纯色
    "inner_fill_color1": (0, 0, 0, 0),                  #   颜色1: 透明
    "inner_fill_color2": None,                          #   颜色2: 无
    "inner_fill_pattern_spacing_mm": 0,                 #   图案间距: 0
    "inner_stroke_color": (0, 0, 0, 0),                 # 内框描边: 透明 (无)
    "stroke_width_pt": 0.5,                             # 描边宽度 (因颜色透明而无效)
    "diagonal_line_width_pt": 0.3                       # 斜线线宽 (因类型为 solid 而无效)
}