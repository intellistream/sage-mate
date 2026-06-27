from __future__ import annotations

from pathlib import Path
import math
import textwrap

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1600
HEIGHT = 900
FPS = 12
DURATION = 84
OUT = Path.home() / "Downloads" / "faculty-twin-dual-profile-demo.mp4"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size, index=1 if bold else 0)
        except Exception:
            continue
    return ImageFont.load_default()


F_TITLE = font(54, True)
F_H1 = font(40, True)
F_H2 = font(27, True)
F_BODY = font(23)
F_SMALL = font(18)
F_TINY = font(15)
F_MONO = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 18)
F_MONO_CODE = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 14)


def ease(x: float) -> float:
    x = max(0, min(1, x))
    return x * x * (3 - 2 * x)


def draw_center(draw: ImageDraw.ImageDraw, text: str, y: int, fnt, fill=(28, 31, 38)) -> None:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    draw.text(((WIDTH - (bbox[2] - bbox[0])) / 2, y), text, font=fnt, fill=fill)


def wrap_by_width(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if draw.textlength(trial, font=fnt) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def text_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt,
    fill=(49, 54, 66),
    width: int = 700,
    line_gap: int = 8,
) -> int:
    x, y = xy
    for para in text.split("\n"):
        lines = wrap_by_width(draw, para, fnt, width) if para else [""]
        for line in lines:
            draw.text((x, y), line, font=fnt, fill=fill)
            y += fnt.size + line_gap
    return y


def pill(draw, xy, text, fill, outline=None, text_fill=(42, 47, 60), fnt=F_SMALL):
    x, y = xy
    pad_x, pad_y = 15, 8
    tw = int(draw.textlength(text, font=fnt))
    box = (x, y, x + tw + pad_x * 2, y + fnt.size + pad_y * 2)
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline)
    draw.text((x + pad_x, y + pad_y - 1), text, font=fnt, fill=text_fill)
    return box[2] + 10


def subtitle(draw, text: str) -> None:
    lines = textwrap.wrap(text, width=34)
    h = 34 * len(lines) + 26
    x0, y0, x1, y1 = 390, HEIGHT - h - 36, WIDTH - 390, HEIGHT - 36
    draw.rounded_rectangle((x0, y0, x1, y1), radius=16, fill=(20, 24, 34, 232))
    y = y0 + 15
    for line in lines:
        draw_center(draw, line, y, F_BODY, fill=(255, 255, 255))
        y += 34


def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), (247, 248, 251))
    draw = ImageDraw.Draw(img, "RGBA")
    return img, draw


def window(draw):
    draw.rounded_rectangle((78, 54, 1522, 846), radius=22, fill=(255, 255, 255), outline=(218, 221, 228))
    draw.rectangle((78, 92, 1522, 94), fill=(228, 230, 235))
    for i, c in enumerate([(255, 93, 88), (255, 190, 46), (40, 201, 64)]):
        draw.ellipse((100 + i * 30, 68, 118 + i * 30, 86), fill=c)
    draw.text((180, 64), "Sage Mate", font=F_SMALL, fill=(85, 90, 100))
    draw.rectangle((78, 94, 150, 846), fill=(250, 251, 253))
    draw.line((150, 94, 150, 846), fill=(228, 230, 235))
    for y, icon in [(132, "S"), (205, "+"), (272, "⌁"), (340, "□")]:
        draw.text((108, y), icon, font=F_H2, fill=(94, 99, 110))


def title_frame(text: str) -> Image.Image:
    img, draw = base()
    draw_center(draw, text, 392, F_TITLE)
    return img


def profile_scene(t: float) -> Image.Image:
    img, draw = base()
    window(draw)
    draw.text((190, 126), "Faculty Twin", font=F_H2, fill=(25, 28, 35))
    draw.text((190, 162), "一个系统，两种清晰工作模式", font=F_BODY, fill=(105, 110, 124))
    draw.rounded_rectangle((320, 250, 1280, 628), radius=20, fill=(255, 255, 255), outline=(225, 228, 235))
    draw.text((370, 300), "选择 Profile", font=F_H1, fill=(26, 31, 42))
    cards = [
        (370, 380, "教师分身", "教学、科研、知识库、问答与工作流"),
        (665, 380, "代码编程", "本地仓库、代码理解、propose-only 修改建议"),
    ]
    for idx, (x, y, head, body) in enumerate(cards):
        active = idx == (1 if t > 7 else 0)
        fill = (232, 239, 255) if active else (255, 255, 255)
        outline = (74, 126, 245) if active else (228, 230, 236)
        draw.rounded_rectangle((x, y, x + 250, y + 150), radius=12, fill=fill, outline=outline, width=2)
        draw.ellipse((x + 20, y + 27, x + 36, y + 43), outline=(74, 126, 245) if active else (135, 140, 150), width=3)
        if active:
            draw.ellipse((x + 25, y + 32, x + 31, y + 38), fill=(39, 112, 246))
        draw.text((x + 55, y + 24), head, font=F_H2, fill=(45, 50, 62))
        text_block(draw, (x + 55, y + 66), body, F_SMALL, fill=(100, 106, 122), width=170)
    subtitle(draw, "同一套自研智能底座，面向两类工作场景。")
    return img


def teacher_scene(t: float) -> Image.Image:
    img, draw = base()
    window(draw)
    draw.text((190, 122), "教师分身 Profile", font=F_H1, fill=(24, 28, 36))
    draw.text((190, 165), "张书豪 · 华中科技大学计算机学院教师", font=F_BODY, fill=(100, 106, 122))
    x = 260
    for label, color in [
        ("SAGE", (232, 240, 255)),
        ("NeuroMem", (232, 247, 242)),
        ("SageVDB / SageANNS", (255, 244, 225)),
        ("vLLM-HUST", (241, 235, 255)),
        ("NPU 推理服务", (235, 245, 255)),
    ]:
        x = pill(draw, (x, 218), label, color, outline=(224, 228, 236))
    draw.rounded_rectangle((250, 280, 960, 375), radius=18, fill=(241, 244, 250), outline=(225, 228, 236))
    text_block(draw, (278, 302), "请用两句话介绍这个数字分身系统的全自研能力栈，并点出 vLLM-HUST 和 NPU 推理服务。", F_BODY, width=650)
    if t > 16:
        draw.rounded_rectangle((250, 405, 1090, 550), radius=18, fill=(255, 255, 255), outline=(225, 228, 236))
        answer = "Faculty Twin 基于 SAGE、NeuroMem、SageVDB / SageANNS 构建记忆、检索、问答和工作流闭环。生成侧接入 vLLM-HUST，并通过 NPU 推理服务提供可部署、可观测的自研推理能力。"
        text_block(draw, (278, 430), answer, F_BODY, width=780)
    if t > 21:
        draw.rounded_rectangle((1120, 280, 1410, 550), radius=18, fill=(255, 255, 255), outline=(225, 228, 236))
        draw.text((1145, 305), "回答依据", font=F_H2, fill=(38, 42, 52))
        text_block(draw, (1145, 348), "• SAGE 能力栈说明\n• NeuroMem 记忆片段\n• 推理服务运行观测", F_SMALL, width=230)
        draw.line((1145, 450, 1385, 450), fill=(225, 228, 236))
        draw.text((1145, 470), "上下文观测", font=F_H2, fill=(38, 42, 52))
        text_block(draw, (1145, 510), "tokens 1.8k / 32k\n检索 4 条 · 记忆 3 条", F_SMALL, width=230)
    if t > 27:
        draw.rounded_rectangle((250, 595, 1410, 760), radius=18, fill=(255, 255, 255), outline=(225, 228, 236))
        draw.text((278, 620), "推理路径 / 工作流轨迹", font=F_H2, fill=(38, 42, 52))
        steps = ["路由", "记忆", "检索", "生成", "后处理"]
        for i, step in enumerate(steps):
            sx = 305 + i * 205
            draw.ellipse((sx, 682, sx + 28, 710), fill=(45, 111, 245))
            draw.text((sx + 42, 678), step, font=F_BODY, fill=(48, 53, 66))
            if i < len(steps) - 1:
                draw.line((sx + 122, 696, sx + 180, 696), fill=(160, 168, 185), width=3)
    sub = "教师分身 Profile"
    if t > 20:
        sub = "记忆、检索、问答与工作流协同运行"
    if t > 30:
        sub = "推理路径可观测：路由、记忆、检索、生成与后处理不再是黑盒"
    subtitle(draw, sub)
    return img


def code_scene(t: float) -> Image.Image:
    img, draw = base()
    window(draw)
    draw.text((190, 122), "代码编程 Profile", font=F_H1, fill=(24, 28, 36))
    draw.text((190, 165), "像 Codex 一样选择本地项目、理解代码、生成修改", font=F_BODY, fill=(100, 106, 122))
    draw.rounded_rectangle((220, 220, 620, 735), radius=18, fill=(255, 255, 255), outline=(225, 228, 236))
    draw.text((250, 250), "本地项目", font=F_H2, fill=(38, 42, 52))
    draw.rounded_rectangle((250, 305, 590, 365), radius=12, fill=(236, 243, 255), outline=(74, 126, 245), width=2)
    draw.text((270, 322), "~/tmp/faculty-twin-demo-project", font=F_SMALL, fill=(40, 49, 70))
    draw.text((250, 405), "src/cart.py", font=F_H2, fill=(38, 42, 52))
    code = [
        "def total_price(items, discount=0):",
        "    subtotal = sum(",
        "        item['price']",
        "        * item.get('quantity', 1)",
        "        for item in items",
        "    )",
        "    factor = 1 - discount / 100",
        "    return subtotal * factor",
    ]
    y = 452
    for i, line in enumerate(code, 1):
        draw.text((255, y), f"{i:>2}  {line}", font=F_MONO_CODE, fill=(50, 55, 68))
        y += 25
    draw.rounded_rectangle((660, 220, 1380, 735), radius=18, fill=(255, 255, 255), outline=(225, 228, 236))
    draw.text((690, 250), "任务", font=F_H2, fill=(38, 42, 52))
    text_block(draw, (690, 295), "请检查这个文件里有没有明显 bug，并生成最小 patch。", F_BODY, width=620)
    if t > 57:
        draw.text((690, 390), "Sage Mate propose-only 建议", font=F_H2, fill=(38, 42, 52))
        diff = [
            "--- a/src/cart.py",
            "+++ b/src/cart.py",
            "@@",
            "+    if discount < 0 or discount > 100:",
            "+        raise ValueError(",
            "+            'discount must be between 0 and 100'",
            "+        )",
            "     subtotal = sum(...)",
            "+    factor = 1 - discount / 100",
            "-    return subtotal - subtotal * discount / 100",
            "+    return subtotal * factor",
        ]
        y = 435
        for line in diff:
            color = (34, 126, 73) if line.startswith("+") else (55, 60, 72)
            draw.text((700, y), line, font=F_MONO_CODE, fill=color)
            y += 24
    if t > 69:
        draw.rounded_rectangle((690, 640, 1050, 700), radius=12, fill=(244, 247, 250), outline=(225, 228, 236))
        draw.text((712, 658), "$ pytest -q    3 passed", font=F_MONO, fill=(48, 53, 66))
        pill(draw, (1080, 646), "propose-only patch", (255, 244, 225), outline=(235, 220, 190), fnt=F_SMALL)
    sub = "代码编程 Profile"
    if t > 51:
        sub = "围绕本地项目上下文，先理解代码再生成建议"
    if t > 60:
        sub = "生成可审阅的 diff、风险说明和建议测试"
    if t > 70:
        sub = "从项目选择到 patch 建议，工作流全程可观测"
    subtitle(draw, sub)
    return img


def frame_at(t: float) -> Image.Image:
    if t < 3:
        return title_frame("Sage Mate：双 Profile 智能系统")
    if t < 12:
        return profile_scene(t)
    if t < 45:
        return teacher_scene(t)
    if t < 78:
        return code_scene(t)
    return title_frame("Sage Mate：教师分身与本地代码编程")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(
        OUT,
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=1,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    ) as writer:
        total = DURATION * FPS
        for idx in range(total):
            t = idx / FPS
            writer.append_data(np.asarray(frame_at(t)))
            if idx % (FPS * 10) == 0:
                print(f"rendered {math.floor(t)}s / {DURATION}s")
    print(OUT)


if __name__ == "__main__":
    main()
