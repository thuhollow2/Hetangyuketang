import requests
import json
import os
import re
import shutil
import time
import cv2
import freetype
import math
import numpy as np
import qrcode
from pyzbar.pyzbar import decode
from PIL import Image
from datetime import datetime, timedelta
from pytz import timezone
from concurrent.futures import ThreadPoolExecutor

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

timeout = config['util']['timeout']
threads = config['util']['threads']
tz = timezone(config['util']['timezone'])

def download_qrcode(url):
    try:
        res=requests.get(url, timeout=timeout)
    except Exception as e:
        print(f"下载登录二维码时发生错误: {e}")
        return
    with open("qrcode.jpg","wb") as f:
        f.write(res.content)
    print("登录二维码已保存为qrcode.jpg")
    barcode_url = ''
    barcodes = decode(Image.open("qrcode.jpg"))
    for barcode in barcodes:
        barcode_url = barcode.data.decode("utf-8")
    qr = qrcode.QRCode()
    qr.add_data(barcode_url)
    qr.print_ascii(invert=True)

def cookie_date(response):
    set_cookie_str = response.headers.get('Set-Cookie', '')
    expires_regex = re.compile(r'expires=([^;]+)')
    expires_matches = expires_regex.findall(set_cookie_str)
    expires_datetimes = [int(datetime.strptime(date_str, '%a, %d-%b-%Y %H:%M:%S GMT').replace(tzinfo=timezone('UTC')).timestamp() * 1000) for date_str in expires_matches]
    nearest_expires = min(expires_datetimes, default=None)
    return nearest_expires

def clear_folder(folder_path):
    try:
        if os.path.isfile(folder_path) or os.path.islink(folder_path):
            os.unlink(folder_path)
        elif os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
    except Exception as e:
        print(f'删除 {folder_path} 时发生错误。原因: {e}')
    os.makedirs(folder_path)

def download_image(item, folder, retry_delay=5, backoff=1.5, max_delay=60):
    if not item.get('cover'):
        return
    url = item['cover']
    file_path = os.path.join(folder, f"raw_{item['index']}.jpg")
    delay = max(1, int(retry_delay))

    while True:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200 and response.content:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return
            else:
                print(f"下载图片 {item.get('index')} 失败: HTTP {response.status_code}, {len(response.content) if response.content else 0} bytes")
        except Exception as e:
            print(f"下载图片 {item.get('index')} 时发生错误: {e}")

        # 失败后等待再试
        time.sleep(delay)
        delay = min(int(delay * backoff), max_delay)

def download_images_to_folder(slides, folder):
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for item in slides:
            executor.submit(download_image, item, folder)

def images_to_pdf(folder, output_path):
    if not os.path.exists(folder):
        print(f'文件夹 {folder} 不存在')
        return
    
    image_files = [f for f in os.listdir(folder)
                   if f.lower().endswith('.jpg') and f.lower().startswith('raw_') and os.path.splitext(f)[0][4:].isdigit()]
    image_files.sort(key=lambda x: int(os.path.splitext(x)[0][4:]))
    image_files = [os.path.join(folder, f) for f in image_files]

    images = [Image.open(f).convert('RGB') for f in image_files]
    if images:
        images[0].save(output_path, save_all=True, append_images=images[1:])
        print(f'PDF文件已生成: {output_path}')
    else:
        print("没有找到任何图片文件")

def convert_date(timestamp_ms):
    timestamp_s = timestamp_ms / 1000
    dt = datetime.fromtimestamp(timestamp_s, tz=timezone('UTC')).astimezone(tz)
    formatted_date = dt.strftime('%Y年%m月%d日%H时%M分%S秒')
    return formatted_date

def check_time(target_time_str, minutes):
    target_time = tz.localize(datetime.strptime(target_time_str, "%Y年%m月%d日%H时%M分%S秒"))
    target_time_minus = target_time - timedelta(minutes=minutes)
    current_time = datetime.now(tz)
    return current_time < target_time_minus

def check_time2(time_dict):
    today = str(datetime.now(tz).weekday() + 1)
    if today not in time_dict:
        return True
    time = time_dict[today]
    given_time = datetime.strptime(time, "%H:%M").time()
    current_time = datetime.now(tz).time()
    return current_time >= given_time

def format_json_to_text(json_data, list_data):
    index_data = []
    if not json_data:
        return "问题列表: 无"
    text_result = "问题列表:\n"
    for index, problem_info in json_data.items():
        if index in list_data:
            index_data.append(problem_info['index'])
        text_result += "-"*20 + "\n"
        body = problem_info.get('body', '未知问题')
        text_result += f"PPT: 第{problem_info['index']}页\n问题: {body}\n"
        if 'options' in problem_info:
            for option in problem_info['options']:
                text_result += f"- {option['key']}: {option['value']}\n"
        text_result += f"答案: 暂无, 待生成\n"
    text_result += "已解锁问题:\n"
    if not index_data:
        text_result += "无\n"
    else:
        for item in index_data:
            text_result += f"- PPT第{item}页\n"
    return text_result

async def recv_json(websocket):
    server_response = await websocket.recv()
    # print(f"Received from server: {server_response}")
    info=json.loads(server_response)
    return info

def draw_cn_text_no_pillow(im, text, vpos, k):
    face = freetype.Face(os.path.join(current_dir, "msyh.ttc"))
    w = im.shape[1]
    scale_ref = max(0.6, w / 1200.0)
    font_size = int(64 * scale_ref / k)
    face.set_pixel_sizes(0, font_size)

    size = face.size
    ascender = (size.ascender >> 6) if hasattr(size, "ascender") else font_size
    descender = (size.descender >> 6) if hasattr(size, "descender") else 0

    pen_x = 0
    glyphs = []
    for ch in text:
        face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
        bmp = face.glyph.bitmap
        buf = (np.array(bmp.buffer, dtype=np.uint8).reshape(bmp.rows, bmp.width)
               if bmp.width and bmp.rows else np.zeros((0,0), np.uint8))
        glyphs.append({
            "bitmap": buf,
            "top": face.glyph.bitmap_top,
            "left": face.glyph.bitmap_left,
            "advance": face.glyph.advance.x >> 6
        })
        pen_x += glyphs[-1]["advance"]

    text_w = max(1, pen_x)
    text_h = ascender - descender
    if text_h <= 0:
        return im

    mask = np.zeros((text_h, text_w), dtype=np.uint8)
    pen_x = 0
    for g in glyphs:
        bm = g["bitmap"]
        if bm.size == 0:
            pen_x += g["advance"]
            continue
        x = pen_x + g["left"]
        y = ascender - g["top"]
        x_end = x + bm.shape[1]
        y_end = y + bm.shape[0]
        if x < 0 or y < 0:
            pen_x += g["advance"]
            continue
        if x_end > mask.shape[1] or y_end > mask.shape[0]:
            bm = bm[:max(0, mask.shape[0]-y), :max(0, mask.shape[1]-x)]
            y_end = min(y_end, mask.shape[0])
            x_end = min(x_end, mask.shape[1])
        if bm.size > 0:
            region = mask[y:y_end, x:x_end]
            region[:] = np.maximum(region, bm[:region.shape[0], :region.shape[1]])
        pen_x += g["advance"]

    pad = int(8 * scale_ref)
    bg_pad = int(6 * scale_ref)
    x1 = pad - bg_pad

    if vpos == 'top':
        cy = int(im.shape[0] * 0.25)
    elif vpos == 'middle':
        cy = im.shape[0] // 2
    else:  # bottom
        cy = int(im.shape[0] * 0.75)
    y1 = cy - text_h // 2 - bg_pad

    if y1 < 0:
        y1 = 0
    x2 = x1 + text_w + bg_pad * 2
    y2 = y1 + text_h + bg_pad * 2
    x2 = min(x2, im.shape[1])
    y2 = min(y2, im.shape[0])
    if x1 < 0 or y1 >= im.shape[0]:
        return im

    text_roi = im[y1+bg_pad:y1+bg_pad+text_h, x1+bg_pad:x1+bg_pad+text_w]
    if (text_roi.shape[0] == mask.shape[0]) and (text_roi.shape[1] == mask.shape[1]):
        m = mask.astype(np.float32)/255.0
        color = np.array([0, 0, 0], dtype=np.float32)  # 黑色 (B,G,R)
        for c in range(3):
            text_roi[..., c] = (m * color[c] + (1 - m) * text_roi[..., c]).astype(np.uint8)
    return im

def concat_vertical_cv(folder, image_type, quality, questionList=[]):
    files = [f for f in os.listdir(folder)
                   if f.lower().endswith('.jpg') and f.lower().startswith('raw_') and os.path.splitext(f)[0][4:].isdigit()]
    files.sort(key=lambda x: int(os.path.splitext(x)[0][4:]))
    files = [os.path.join(folder, f) for f in files]

    if not files:
        print(f'文件夹 {folder} 中没有任何图片文件'); return

    imgs = []

    widths, heights = [], []
    for p in files:
        stem = os.path.splitext(os.path.basename(p))[0][4:]
        if image_type == 3:
            if stem.isdigit() and int(stem) not in questionList:
                continue

        im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if im is None:
            print(f"跳过无法读取: {p}")
            continue
        
        # 统一为BGR三通道
        if im.ndim == 2:
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        elif im.shape[2] == 4:
            b, g, r, a = cv2.split(im)
            alpha = (a.astype(np.float32) / 255.0)[..., None]
            bg = np.full_like(im[..., :3], (255, 255, 255), dtype=np.uint8)
            rgb = cv2.merge([b, g, r]).astype(np.float32)
            im = (alpha * rgb + (1.0 - alpha) * bg.astype(np.float32)).astype(np.uint8)

        if image_type == 3:
            k = max(2, math.ceil(math.sqrt(len(questionList))))
        else:
            k = 2
        new_w = max(1, int(im.shape[1] / k))
        new_h = max(1, int(im.shape[0] / k))
        im = cv2.resize(im, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        if image_type in (1, 2, 3):
            txt = f"第{stem}页"
            im = draw_cn_text_no_pillow(im, txt, 'top', k)
            im = draw_cn_text_no_pillow(im, txt, 'middle', k)
            im = draw_cn_text_no_pillow(im, txt, 'bottom', k)

        imgs.append(im)
        if image_type == 0:
            cv2.imwrite(os.path.join(folder, f"resized_{stem}.jpg"), im)
        elif image_type == 1:
            cv2.imwrite(os.path.join(folder, f"mark_{stem}.jpg"), im)
        heights.append(im.shape[0])
        widths.append(im.shape[1])

    if not imgs:
        print("没有可拼接的图片")
        return

    if image_type == 2:
        max_w = max(widths)

        padded = []
        for im in imgs:
            h, w = im.shape[:2]
            canvas = np.full((h, max_w, 3), (255,255,255), dtype=np.uint8)
            x = (max_w - w) // 2
            canvas[:, x:x+w] = im
            padded.append(canvas)
        imgs = padded
        heights = [im.shape[0] for im in imgs]

        gap = 200
        total_h = sum(im.shape[0] for im in imgs) + gap * (len(imgs) - 1)
        out = np.full((total_h, max_w, 3), (255,255,255), dtype=np.uint8)

        y = 0
        for idx, im in enumerate(imgs):
            h = im.shape[0]
            out[y:y+h, :max_w] = im
            y += h
            if idx < len(imgs) - 1:
                y += gap

        cv2.imwrite(os.path.join(folder, "long.jpg"), out, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        size_bytes = os.path.getsize(os.path.join(folder, "long.jpg")) / (1024 * 1024)
        if quality < 5:
            print("质量已降至最低，仍无法满足文件大小要求")
            return
        if size_bytes > 2:
            return concat_vertical_cv(folder, image_type, quality=quality-4)
    elif image_type == 3:
        if not questionList:
            print("请提供 questionList 参数")
            return
        n = len(imgs)

        rows = math.ceil(math.sqrt(n)*1.2)
        cols = math.ceil(n / rows)

        # 统一 cell 尺寸
        cell_w = max(im.shape[1] for im in imgs)
        cell_h = max(im.shape[0] for im in imgs)
        gap = 40

        # 计算满列宽度
        canvas_w = cols * cell_w + (cols - 1) * gap

        full_rows = n // cols
        last_row_count = n % cols
        used_rows = full_rows + (1 if last_row_count else 0)
        if used_rows == 0:
            used_rows = 1

        canvas_h = used_rows * cell_h + (used_rows - 1) * gap
        canvas = np.full((canvas_h, canvas_w, 3), (255, 255, 255), dtype=np.uint8)

        for i, im in enumerate(imgs):
            row = i // cols
            if row == full_rows and last_row_count:
                row_count = last_row_count
            else:
                row_count = cols

            # 行起始 y
            y = row * (cell_h + gap)

            # 行宽
            row_width = row_count * cell_w + (row_count - 1) * gap
            start_x = 0 if row_count == cols else (canvas_w - row_width) // 2  # 居中最后一行

            col_in_row = i % cols if row_count == cols else i - full_rows * cols
            x = start_x + col_in_row * (cell_w + gap)

            ih, iw = im.shape[:2]
            x_im = x + (cell_w - iw) // 2
            y_im = y + (cell_h - ih) // 2
            canvas[y_im:y_im+ih, x_im:x_im+iw] = im

        cv2.imwrite(os.path.join(folder, "grid.jpg"), canvas, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return
