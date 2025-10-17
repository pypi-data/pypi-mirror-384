import turtle
import random
import time
import math
import tkinter as tk
from importlib.resources import files
from pathlib import Path

# ---------------------------
# 高亮色彩库
# ---------------------------
_ALL_VIBRANT_COLORS = [
    "#FF0000", "#FF4500", "#FF8C00", "#FFD700", "#ADFF2F", "#00FF7F",
    "#00FA9A", "#00FFFF", "#1E90FF", "#7B68EE", "#9932CC", "#FF69B4",
    "#FF1493", "#FF00FF", "#FF7F50", "#FFA500", "#40E0D0", "#7FFF00",
    "#FF5733", "#FFC300", "#DAF7A6", "#C70039", "#900C3F", "#581845"
]

# ---------------------------
# 资源文件获取函数
# ---------------------------


def get_resource_path(filename: str) -> str:
    """返回包内资源的绝对路径"""
    return str(files("XMWAI.assets").joinpath(filename))

# ---------------------------
# 特效函数
# ---------------------------


def _effect_stars(screen):
    """炫彩星星闪烁"""
    t = turtle.Turtle(visible=False)
    t.speed(0)
    t.hideturtle()
    screen.tracer(False)

    stars = [(random.randint(-250, 250), random.randint(-180, 200),
              random.randint(10, 30)) for _ in range(30)]

    for _ in range(12):  # 闪烁次数
        t.clear()
        for x, y, size in stars:
            t.penup()
            t.goto(x, y)
            t.pendown()
            t.color(random.choice(_ALL_VIBRANT_COLORS))
            t.begin_fill()
            for _ in range(5):
                t.forward(size)
                t.right(144)
            t.end_fill()
        screen.update()
        time.sleep(0.07)

    t.clear()
    screen.update()


def _effect_like(screen, img_path=None, flash_times=1, flash_interval=0.2):
    """点赞动画"""
    screen.tracer(False)
    canvas = screen.getcanvas()
    img_path = img_path or get_resource_path("like.png")

    tk_img = tk.PhotoImage(file=img_path)
    screen._tk_img_ref = tk_img  # 保持引用

    w = screen.window_width()
    h = screen.window_height()
    img_id = canvas.create_image(w//4, h//4, image=tk_img)

    for _ in range(flash_times * 2):
        canvas.itemconfigure(img_id, state='normal')
        screen.update()
        time.sleep(flash_interval)
        canvas.itemconfigure(img_id, state='hidden')
        screen.update()
        time.sleep(flash_interval)

    canvas.delete(img_id)
    screen.update()


def _effect_fireworks(screen):
    """极速瞬爆烟花"""
    t = turtle.Turtle(visible=False)
    t.speed(0)
    t.hideturtle()
    screen.tracer(False)

    fireworks = []
    for _ in range(random.randint(3, 6)):
        start_x = random.randint(-300, 300)
        peak_y = random.randint(150, 280)
        fireworks.append({
            "x": start_x,
            "y": peak_y,
            "particles": [
                (random.uniform(0, 360), random.uniform(
                    80, 220), random.choice(_ALL_VIBRANT_COLORS))
                for _ in range(random.randint(100, 180))
            ],
            "color": random.choice(["white", "gold", "yellow"])
        })

    for y in range(-250, 0, 80):
        t.clear()
        for fw in fireworks:
            t.penup()
            t.goto(fw["x"], y)
            t.dot(8, "white")
        screen.update()
        time.sleep(0.01)

    steps = 12
    for step in range(1, steps + 1):
        t.clear()
        scale = step / steps
        fade = 1 - scale * 0.7
        for fw in fireworks:
            for angle, dist, color in fw["particles"]:
                r, g, b = screen.cv.winfo_rgb(color)
                r, g, b = int((r / 256) * fade), int((g / 256)
                                                     * fade), int((b / 256) * fade)
                fade_color = f"#{r:02x}{g:02x}{b:02x}"
                x = fw["x"] + math.cos(math.radians(angle)) * \
                    (dist * scale ** 1.5)
                y = fw["y"] + math.sin(math.radians(angle)) * \
                    (dist * scale ** 1.5)
                t.penup()
                t.goto(x, y)
                if random.random() > 0.1:
                    t.dot(max(2, 10 - step * 0.3), fade_color)
            if step < 4:
                t.penup()
                t.goto(fw["x"], fw["y"])
                t.dot(40 - step * 4, fw["color"])
        screen.update()
        time.sleep(0.03)

    for i in range(3):
        t.clear()
        for fw in fireworks:
            t.penup()
            t.goto(fw["x"], fw["y"])
            if i % 2 == 0:
                t.dot(25, "white")
            else:
                t.dot(18, "gold")
        screen.update()
        time.sleep(0.05)

    t.clear()
    screen.update()


def _effect_heart(screen):
    """快速跳动的爱心效果"""
    t = turtle.Turtle(visible=False)
    t.speed(0)
    screen.tracer(False)
    t.color("red", "red")

    for s in [0.5, 0.7, 0.9, 1.1, 0.9, 1.1, 0.9, 0.7, 0.5]:
        t.clear()
        t.begin_fill()
        t.setheading(140)
        t.forward(120 * s)
        t.circle(-60 * s, 200)
        t.left(120)
        t.circle(-60 * s, 200)
        t.forward(120 * s)
        t.end_fill()
        screen.update()
        time.sleep(0.05)

    t.clear()
    t.penup()
    t.goto(0, -100)
    t.pendown()
    t.color("black")
    t.write("点赞!", align="center", font=("Arial", 24, "bold"))
    screen.update()
    time.sleep(0.5)
    t.clear()
    screen.update()


# ---------------------------
# 统一接口
# ---------------------------
def effects(screen, effect_name: str):
    if effect_name == "stars":
        _effect_stars(screen)
    elif effect_name == "like":
        _effect_like(screen)
    elif effect_name == "fireworks":
        _effect_fireworks(screen)
    elif effect_name == "heart":
        _effect_heart(screen)
    else:
        print(f"未知特效: {effect_name}")
