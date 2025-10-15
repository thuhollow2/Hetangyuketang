import requests
import json
import os
import re
import shutil
import time
import freetype
import math
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
        problemType = {1:"单选题", 2:"多选题", 3:"投票题", 4:"填空题", 5:"主观题"}.get(problem_info['problemType'], "其它题型")
        text_result += f"PPT: 第{problem_info['index']}页 {problemType}\n问题: {body}\n"
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
    if not isinstance(im, Image.Image):
        raise TypeError("draw_cn_text_no_pillow 现在要求传入 PIL.Image 对象")

    face = freetype.Face(os.path.join(current_dir, "msyh.ttc"))
    w = im.width
    scale_ref = max(0.6, w / 1200.0)
    font_size = int(64 * scale_ref / k)
    face.set_pixel_sizes(0, font_size)

    size = face.size
    ascender  = (size.ascender  >> 6) if hasattr(size, "ascender")  else font_size
    descender = (size.descender >> 6) if hasattr(size, "descender") else 0

    # 渲染每个字的灰度位图
    pen_x = 0
    glyphs = []
    for ch in text:
        face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
        bmp = face.glyph.bitmap
        if bmp.width and bmp.rows:
            bm_img = Image.frombytes('L', (bmp.width, bmp.rows), bytes(bmp.buffer))
        else:
            bm_img = Image.new('L', (0, 0))
        glyphs.append({
            "image":   bm_img,
            "top":     face.glyph.bitmap_top,
            "left":    face.glyph.bitmap_left,
            "advance": face.glyph.advance.x >> 6
        })
        pen_x += glyphs[-1]["advance"]

    text_w = max(1, pen_x)
    text_h = ascender - descender
    if text_h <= 0:
        return im

    # 组装整行文字的遮罩
    mask = Image.new('L', (text_w, text_h), 0)
    pen_x = 0
    for g in glyphs:
        bm = g["image"]
        if bm.size == (0, 0):
            pen_x += g["advance"]
            continue
        x = pen_x + g["left"]
        y = ascender - g["top"]
        if x >= 0 and y >= 0:
            mask.paste(bm, (x, y))
        pen_x += g["advance"]

    # 计算放置位置
    pad   = int(8 * scale_ref)
    bgpad = int(6 * scale_ref)
    x1 = max(0, pad - bgpad)

    if vpos == 'top':
        cy = int(im.height * 0.25)
    elif vpos == 'middle':
        cy = im.height // 2
    else:
        cy = int(im.height * 0.75)
    y1 = max(0, cy - text_h // 2 - bgpad)

    # 叠加到原图
    box = (x1 + bgpad, y1 + bgpad, x1 + bgpad + text_w, y1 + bgpad + text_h)
    # 裁剪以防越界
    box = (min(box[0], im.width), min(box[1], im.height),
           min(box[2], im.width), min(box[3], im.height))
    if box[2] > box[0] and box[3] > box[1]:
        w_box, h_box = box[2] - box[0], box[3] - box[1]
        black = Image.new('RGB', (w_box, h_box), (0, 0, 0))
        mask_crop = mask.crop((0, 0, w_box, h_box))
        im.paste(black, box, mask_crop)
    return im

def concat_vertical_cv(folder, image_type, quality, questionList=[]):
    # 收集并排序文件(raw_数字.jpg)
    files = [f for f in os.listdir(folder)
             if f.lower().endswith('.jpg') and f.lower().startswith('raw_') and os.path.splitext(f)[0][4:].isdigit()]
    files.sort(key=lambda x: int(os.path.splitext(x)[0][4:]))
    files = [os.path.join(folder, f) for f in files]

    if not files:
        print(f'文件夹 {folder} 中没有任何图片文件')
        return

    if image_type == 3:
        if not questionList:
            return
        sel = []
        for p in files:
            stem = os.path.splitext(os.path.basename(p))[0][4:]
            if stem.isdigit() and int(stem) in questionList:
                sel.append(p)
        files = sel
        if not files:
            print("questionList 中的页码没有匹配到任何文件")
            return

    RESAMPLE = getattr(Image, "LANCZOS", getattr(Image, "BICUBIC", 3))

    if image_type in (0, 1):
        for p in files:
            stem = os.path.splitext(os.path.basename(p))[0][4:]
            try:
                with Image.open(p) as im_src:
                    im = im_src.convert("RGB")
                    # k 的策略与原逻辑一致
                    k = 2 if image_type in (0, 1, 2) else max(2, math.ceil(math.sqrt(len(questionList))))
                    new_w = max(1, int(im.width / k))
                    new_h = max(1, int(im.height / k))
                    im = im.resize((new_w, new_h), RESAMPLE)

                    if image_type == 1:
                        txt = f"第{stem}页"
                        im = draw_cn_text_no_pillow(im, txt, 'top', k)
                        im = draw_cn_text_no_pillow(im, txt, 'middle', k)
                        im = draw_cn_text_no_pillow(im, txt, 'bottom', k)

                    outname = f"resized_{stem}.jpg" if image_type == 0 else f"mark_{stem}.jpg"
                    im.save(os.path.join(folder, outname), "JPEG")
            except Exception as e:
                print(f"跳过无法处理: {p} ({e})")
        return

    if image_type == 2:
        MAX_JPEG_DIM = 65000  # 避免超过 JPEG 维度极限
        k = 2
        max_w = 0
        total_h = 0
        valid_files = []

        orig = []
        for p in files:
            try:
                with Image.open(p) as im_src:
                    w, h = im_src.size
                orig.append((p, w, h))
            except Exception as e:
                print(f"跳过无法读取: {p} ({e})")

        if not orig:
            return

        gap = 50
        n = len(orig)
        max_w_raw = max(w for _, w, _ in orig)
        sum_h_raw = sum(h for _, _, h in orig)
        need_k_h = math.ceil((sum_h_raw + gap * (n - 1)) / max(1, (MAX_JPEG_DIM - 1)))
        need_k_w = math.ceil(max_w_raw / max(1, (MAX_JPEG_DIM - 1)))
        k = max(2, need_k_h, need_k_w)

        for p, w, h in orig:
            new_w = max(1, int(w / k))
            new_h = max(1, int(h / k))
            max_w = max(max_w, new_w)
            total_h += new_h
            valid_files.append((p, new_w, new_h))

        if not valid_files:
            return

        canvas_w = max_w
        canvas_h = total_h + gap * (len(valid_files) - 1)
        if canvas_w > MAX_JPEG_DIM or canvas_h > MAX_JPEG_DIM:
            scale = max(
                math.ceil(canvas_w / (MAX_JPEG_DIM - 1)),
                math.ceil(canvas_h / (MAX_JPEG_DIM - 1))
            )
            k *= scale
            max_w = 0
            total_h = 0
            valid2 = []
            for p, w, h in orig:
                nw = max(1, int(w / k))
                nh = max(1, int(h / k))
                max_w = max(max_w, nw)
                total_h += nh
                valid2.append((p, nw, nh))
            valid_files = valid2
            canvas_w = max_w
            canvas_h = total_h + gap * (len(valid_files) - 1)

        out = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        y = 0
        for idx, (p, new_w, new_h) in enumerate(valid_files):
            stem = os.path.splitext(os.path.basename(p))[0][4:]
            try:
                with Image.open(p) as im_src:
                    im = im_src.convert("RGB").resize((new_w, new_h), RESAMPLE)
                txt = f"第{stem}页"
                im = draw_cn_text_no_pillow(im, txt, 'top', k)
                im = draw_cn_text_no_pillow(im, txt, 'middle', k)
                im = draw_cn_text_no_pillow(im, txt, 'bottom', k)

                row_canvas = Image.new("RGB", (canvas_w, im.height), (255, 255, 255))
                row_canvas.paste(im, ((canvas_w - im.width) // 2, 0))
                out.paste(row_canvas, (0, y))
                y += im.height
                if idx < len(valid_files) - 1:
                    y += gap
            except Exception as e:
                print(f"拼接失败,跳过: {p} ({e})")

        out_path = os.path.join(folder, "long.jpg")
        q = int(quality)

        try:
            out.save(out_path, "JPEG", quality=q, optimize=True)
        except Exception as e:
            print(f"保存长图失败(optimize=True),重试无优化: {e}")
            try:
                out.copy().save(out_path, "JPEG", quality=q)
            except Exception as e2:
                print(f"保存长图再次失败: {e2}")
                return
            
        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        while size_mb > 2 and q >= 5:
            q -= 4
            try:
                out.save(out_path, "JPEG", quality=q)
                size_mb = os.path.getsize(out_path) / (1024 * 1024)
            except Exception as e:
                print(f"降质重存失败: {e}")
                break
        if size_mb > 2 and q < 5:
            print("质量已降至最低,仍无法满足文件大小要求")
        return

    if image_type == 3:
        n = len(files)
        if n == 0:
            return

        k = max(2, math.ceil(math.sqrt(len(questionList))))
        cell_w, cell_h = 0, 0
        valid_files = []
        for p in files:
            try:
                with Image.open(p) as im_src:
                    w, h = im_src.size
                new_w = max(1, int(w / k))
                new_h = max(1, int(h / k))
                cell_w = max(cell_w, new_w)
                cell_h = max(cell_h, new_h)
                valid_files.append((p, new_w, new_h))
            except Exception as e:
                print(f"跳过无法读取: {p} ({e})")

        if not valid_files:
            return

        rows = math.ceil(math.sqrt(n) * 1.2)
        cols = math.ceil(n / rows)
        gap = 40
        canvas_w = cols * cell_w + (cols - 1) * gap

        full_rows = n // cols
        last_row_count = n % cols
        used_rows = full_rows + (1 if last_row_count else 0)
        if used_rows == 0:
            used_rows = 1
        canvas_h = used_rows * cell_h + (used_rows - 1) * gap

        canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

        for i, (p, new_w, new_h) in enumerate(valid_files):
            stem = os.path.splitext(os.path.basename(p))[0][4:]
            try:
                with Image.open(p) as im_src:
                    im = im_src.convert("RGB").resize((new_w, new_h), RESAMPLE)
                txt = f"第{stem}页"
                im = draw_cn_text_no_pillow(im, txt, 'top', k)
                im = draw_cn_text_no_pillow(im, txt, 'middle', k)
                im = draw_cn_text_no_pillow(im, txt, 'bottom', k)

                row = i // cols
                row_count = last_row_count if (row == full_rows and last_row_count) else cols
                y = row * (cell_h + gap)
                row_width = row_count * cell_w + (row_count - 1) * gap
                start_x = 0 if row_count == cols else (canvas_w - row_width) // 2

                col_in_row = i % cols if row_count == cols else i - full_rows * cols
                x = start_x + col_in_row * (cell_w + gap)

                x_im = x + (cell_w - im.width) // 2
                y_im = y + (cell_h - im.height) // 2
                canvas.paste(im, (x_im, y_im))
            except Exception as e:
                print(f"网格粘贴失败,跳过: {p} ({e})")

        canvas.save(os.path.join(folder, "grid.jpg"), "JPEG", quality=int(quality), optimize=True)
        return
