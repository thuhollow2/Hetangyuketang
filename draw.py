import io
import os
import re
import shutil
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont, ImageFile

current_dir = os.path.dirname(os.path.abspath(__file__))
home_dir = os.environ.get("YUKETANG_HOME", current_dir)
data_dir = os.path.join(home_dir, "data")
os.makedirs(data_dir, exist_ok=True)
file_dir = os.path.join(data_dir, "file")
os.makedirs(file_dir, exist_ok=True)
os.chdir(home_dir)

CANVAS_W, CANVAS_H = 1280, 960
TEXT_PADDING_Y = 24
LINE_SPACING = 10
FONT_SIZE = 48
FONT_PATH = "msyh.ttc"
MIN_FONT = 10
MIN_LINE_SPACING = 0
MIN_TEXT_PADDING_Y = 0
MIN_S = 0.03  # 全局缩放最小值
ImageFile.LOAD_TRUNCATED_IMAGES = True
RESAMPLE = Image.Resampling.BILINEAR
MAX_WORKERS = min(4, (os.cpu_count() or 4) * 2)
IMG_CACHE = os.path.join(file_dir, "_img_cache")

IMG_TAG_RE = re.compile(r'<\s*img\b[^>]*src=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)
_MEASURE_DRAW = ImageDraw.Draw(Image.new("RGB", (2, 2), "white"))

def clear_folder(folder_path):
    try:
        if os.path.isfile(folder_path) or os.path.islink(folder_path):
            os.unlink(folder_path)
        elif os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
    except Exception as e:
        print(f"删除 {folder_path} 时发生错误。原因: {e}")
    os.makedirs(folder_path)

clear_folder(IMG_CACHE)

def text_width(font, text):
    try:
        return font.getlength(text)
    except Exception:
        try:
            return _MEASURE_DRAW.textlength(text, font=font)
        except Exception:
            x0, _, x1, _ = _MEASURE_DRAW.textbbox((0, 0), text, font=font)
            return x1 - x0

def fetch_bytes(url, no):
    p = os.path.join(IMG_CACHE, f"{no}.jpg")
    if os.path.exists(p):
        with open(p, "rb") as f:
            return f.read()
    resp = requests.get(url, timeout=15, stream=True)
    resp.raise_for_status()
    data = resp.content
    with open(p, "wb") as f:
        f.write(data)
    return data

def prefetch_images(urls):
    pool, futs = {}, {}
    if not urls:
        return pool
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for idx, u in enumerate(urls):
            futs[ex.submit(fetch_bytes, u, idx + 1)] = u
        for fu in as_completed(futs):
            u = futs[fu]
            try:
                pool[u] = Image.open(io.BytesIO(fu.result())).convert("RGB")
            except Exception:
                pool[u] = Image.new("RGB", (1, 1), "white")
    return pool

def parse_items(str_list):
    items, buf = [], []
    for item in str_list:
        if not item:
            continue
        s = item.strip()
        if not s:
            continue
        m = IMG_TAG_RE.search(s)
        if m:
            if buf:
                items.append(("text", buf))
                buf = []
            items.append(("img", m.group(1)))
        else:
            buf.append(s)
    if buf:
        items.append(("text", buf))
    return items

def wrap_para_fast(text, font, max_w):
    if text == "":
        return [""]
    n = len(text)
    avg = max(1.0, float(text_width(font, text)) / n)
    approx = max(1, int(max_w / avg))
    out, i = [], 0
    while i < n:
        j = min(n, i + approx)
        while j < n and text_width(font, text[i:j + 1]) <= max_w:
            j += 1
        while j > i + 1 and text_width(font, text[i:j]) > max_w:
            j -= 1
        if j <= i:
            j = i + 1
        out.append(text[i:j])
        i = j
    return out

def wrap_text(paragraphs, font, width_1280):
    lines = []
    for p in paragraphs:
        lines.extend(wrap_para_fast(p, font, width_1280))
    return lines

def estimate_with_s(items, imgs, s):
    fs = max(MIN_FONT, int(round(FONT_SIZE * s)))
    ls = max(MIN_LINE_SPACING, int(round(LINE_SPACING * s)))
    py = max(MIN_TEXT_PADDING_Y, int(round(TEXT_PADDING_Y * s)))
    font = ImageFont.truetype(FONT_PATH, size=fs)

    content_w = CANVAS_W
    ascent, descent = font.getmetrics()
    line_h = ascent + descent

    total_h, pre = 0, []
    max_line_w = 0
    max_img_w = 0

    for typ, payload in items:
        if typ == "text":
            lines = wrap_text(payload, font, content_w)
            # 计算本文本块的最大行宽，用于确定整页实际占宽
            if lines:
                local_max = max(int(round(text_width(font, ln))) for ln in lines)
                if local_max > max_line_w:
                    max_line_w = local_max
            h = py * 2 + len(lines) * (line_h + ls)
            pre.append(("text", lines, py, ls))
            total_h += h
        else:
            url = payload
            img = imgs.get(url) or Image.new("RGB", (1, 1), "white")
            w0, h0 = img.size
            w_s = max(1, int(round(w0 * s)))
            h_s = max(1, int(round(h0 * s)))
            max_img_w = max(max_img_w, w_s)
            pre.append(("img", url, w_s, h_s))
            total_h += h_s

    used_w = max(1, min(CANVAS_W, max(max_line_w, max_img_w)))
    return font, total_h, pre, used_w

def max_scale_from_images(imgs):
    if not imgs:
        return 1.0
    max_w = max((im.size[0] for im in imgs.values()), default=1)
    return min(1.0, CANVAS_W / float(max_w or 1))

def find_best_s(items, imgs):
    s_hi = max_scale_from_images(imgs)  # 任何图片不会超宽
    s_lo = MIN_S

    pack_hi = estimate_with_s(items, imgs, s_hi)
    if pack_hi[1] <= CANVAS_H:
        return s_hi, pack_hi

    best_s, best_pack = s_lo, estimate_with_s(items, imgs, s_lo)
    for _ in range(28):
        mid = (s_lo + s_hi) / 2.0
        p = estimate_with_s(items, imgs, mid)
        if p[1] <= CANVAS_H:
            best_s, best_pack = mid, p
            s_lo = mid
        else:
            s_hi = mid
        if s_hi - s_lo < 1e-3:
            break
    return best_s, best_pack

def render_pre(pre, font, imgs, out_w):
    ascent, descent = font.getmetrics()
    line_h = ascent + descent

    total_h = 0
    for e in pre:
        if e[0] == "text":
            _, lines, py, ls = e
            total_h += py * 2 + len(lines) * (line_h + ls)
        else:
            _, _, _, h_s = e
            total_h += h_s

    img = Image.new("RGB", (out_w, max(1, total_h)), "white")
    draw = ImageDraw.Draw(img)
    y = 0

    for e in pre:
        if e[0] == "text":
            _, lines, py, ls = e
            # 文本从 x=0 左对齐绘制
            draw.multiline_text((0, y + py), "\n".join(lines), font=font, fill=(0, 0, 0), spacing=ls, align="left")
            y += py * 2 + len(lines) * (line_h + ls)
        else:
            _, url, w_s, h_s = e
            src = imgs.get(url) or Image.new("RGB", (1, 1), "white")
            resized = src.resize((w_s, h_s), RESAMPLE)
            x = 0  # 左对齐贴图
            if w_s > out_w:
                resized = resized.crop((0, 0, out_w, h_s))
            img.paste(resized, (x, y))
            y += h_s
    return img

def compose_from_strlist(str_list, out_path):
    items = parse_items(str_list)
    urls = [p for t, p in items if t == "img"]
    imgs = prefetch_images(urls)

    # 统一比例 s
    s, (font, _, pre, used_w) = find_best_s(items, imgs)

    # 裁掉右侧空白
    content = render_pre(pre, font, imgs, used_w)

    # 高度强制 960
    if content.height > CANVAS_H:
        k = CANVAS_H / float(content.height)
        new_w = max(1, int(round(content.width * k)))
        content = content.resize((new_w, CANVAS_H), RESAMPLE)

    if content.height < CANVAS_H:
        canvas = Image.new("RGB", (content.width, CANVAS_H), "white")
        canvas.paste(content, (0, 0))
    else:
        canvas = content

    canvas.save(out_path, "JPEG")
