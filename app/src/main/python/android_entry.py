import asyncio
import builtins
import datetime
import json
import os
import shutil
import sys
import threading
import traceback

import freetype
from PIL import ImageFont

_thread = None
_stop_requested = False
_home = None
_original_stdout = sys.stdout
_original_stderr = sys.stderr
_original_open = builtins.open
_original_freetype_face = freetype.Face
_original_truetype = ImageFont.truetype
_runtime_config_path = None


def _stop_flag_path():
    return os.path.join(_home, "stop.flag") if _home else None


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class _LogWriter:
    def __init__(self, stream, log_path):
        self.stream = stream
        self.log_path = log_path

    def write(self, text):
        if not text:
            return
        try:
            self.stream.write(text)
            self.stream.flush()
        except Exception:
            pass
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(text)
                f.flush()
        except Exception:
            pass

    def flush(self):
        try:
            self.stream.flush()
        except Exception:
            pass


def _log(message):
    print(f"[{_now()}] {message}", flush=True)


def _write_status(state, message="", enabled_users=None):
    if not _home:
        return
    status_path = os.path.join(_home, "status.json")
    status = {}
    if os.path.exists(status_path):
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                status = json.load(f)
        except Exception:
            status = {}
    if state == "running" and not status.get("started_at"):
        status["started_at"] = _now()
    if state in {"stopped", "error"}:
        status["stopped_at"] = _now()
    status["state"] = state
    status["last_tick"] = _now()
    status["message"] = message
    if enabled_users is not None:
        status["enabled_users"] = enabled_users
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def _copy_if_missing(target_dir, name):
    target = os.path.join(target_dir, name)
    if os.path.exists(target):
        return
    for source_dir in [os.path.dirname(os.path.abspath(__file__)), *sys.path]:
        source = os.path.join(source_dir, name)
        if os.path.exists(source):
            with _original_open(source, "rb") as src, _original_open(target, "wb") as dst:
                dst.write(src.read())
            return


def _copy_file_contents(source, target):
    target_dir = os.path.dirname(target)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)
    with _original_open(source, "rb") as src, _original_open(target, "wb") as dst:
        dst.write(src.read())


def _patch_config_open(config_path):
    global _runtime_config_path
    _runtime_config_path = config_path

    def _open(file, *args, **kwargs):
        target = file
        if isinstance(file, os.PathLike):
            target = os.fspath(file)
        if isinstance(target, str) and target == "config.json":
            return _original_open(config_path, *args, **kwargs)
        return _original_open(file, *args, **kwargs)

    builtins.open = _open


def _patch_font_resolution():
    module_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(module_dir, "msyh.ttc")
    if not os.path.exists(font_path):
        return

    def _resolve_font_arg(value):
        if isinstance(value, os.PathLike):
            value = os.fspath(value)
        if value == "msyh.ttc":
            return font_path
        return value

    def _face(path, *args, **kwargs):
        return _original_freetype_face(_resolve_font_arg(path), *args, **kwargs)

    def _truetype(font, *args, **kwargs):
        return _original_truetype(_resolve_font_arg(font), *args, **kwargs)

    freetype.Face = _face
    ImageFont.truetype = _truetype


def _merge_missing(target, defaults):
    changed = False
    for key, value in defaults.items():
        if key not in target:
            target[key] = value
            changed = True
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            changed = _merge_missing(target[key], value) or changed
    return changed


def _ensure_config_defaults(home):
    config_path = os.path.join(home, "config.json")
    defaults = {
        "yuketang": {"users": [], "timeout": 30},
        "send": {"services": [], "threads": 5, "timeout": 30},
        "llm": {"models": [], "threads": 5, "timeout": 60},
        "util": {"threads": 10, "timeout": 30, "timezone": "Asia/Shanghai"},
    }
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            broken_path = os.path.join(home, f"config.invalid.{int(datetime.datetime.now().timestamp())}.json")
            _copy_file_contents(config_path, broken_path)
            config = {}
    changed = _merge_missing(config, defaults)
    if changed or not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            f.write("\n")


def _prepare_home(files_dir):
    global _home
    home = os.path.join(files_dir, "yuketang")
    os.makedirs(home, exist_ok=True)
    data_dir = os.path.join(home, "data")
    os.makedirs(data_dir, exist_ok=True)
    for name in ("config.json",):
        _copy_if_missing(home, name)
    _ensure_config_defaults(home)
    runtime_config = os.path.join(home, "config.runtime.json")
    _copy_file_contents(os.path.join(home, "config.json"), runtime_config)
    os.environ["YUKETANG_HOME"] = home
    os.environ["YUKETANG_DATA_DIR"] = data_dir
    _patch_config_open(runtime_config)
    _patch_font_resolution()
    os.chdir(home)
    _home = home
    stop_flag = _stop_flag_path()
    if stop_flag and os.path.exists(stop_flag):
        os.remove(stop_flag)
    log_path = os.path.join(home, "runner.log")
    sys.stdout = _LogWriter(_original_stdout, log_path)
    sys.stderr = _LogWriter(_original_stderr, log_path)
    return home


def _migrate_runtime_files(home, data_dir):
    os.makedirs(data_dir, exist_ok=True)


async def _run_forever():
    import yuketang as ykt_mod
    os.chdir(_home)

    data_dir = os.path.join(_home, "data")
    ykts = [
        ykt_mod.yuketang(user, idx)
        for idx, user in enumerate(ykt_mod.users)
        if user.get("enabled", False)
    ]
    if not ykts:
        _migrate_runtime_files(_home, data_dir)
        _write_status("stopped", "No enabled users", 0)
        _log("Runner did not start: no enabled users")
        _log("Runner 结束")
        return
    ykt_mod.exam_answer_cache = {ykt.idx: {} for ykt in ykts}
    _write_status("running", "Runner started", len(ykts))
    _log(f"Runner started with {len(ykts)} enabled user(s)")
    while not _stop_requested:
        _migrate_runtime_files(_home, data_dir)
        _write_status("running", "Checking users", len(ykts))
        await asyncio.gather(
            *(ykt_mod._handle_ykt_one(ykt) for ykt in ykts),
            return_exceptions=True,
        )
        _migrate_runtime_files(_home, data_dir)
        _write_status("running", "Sleeping", len(ykts))
        for _ in range(30):
            if _stop_requested:
                _migrate_runtime_files(_home, data_dir)
                _write_status("stopped", "Stop requested", len(ykts))
                _log("Runner 结束")
                return
            await asyncio.sleep(1)
    _migrate_runtime_files(_home, data_dir)
    _write_status("stopped", "Runner stopped", len(ykts))
    _log("Runner 结束")


def _runner(files_dir):
    try:
        _prepare_home(files_dir)
        asyncio.run(_run_forever())
    except Exception as exc:
        _write_status("error", str(exc))
        _log("Runner crashed")
        traceback.print_exc()


def start(files_dir):
    global _thread, _stop_requested
    if _thread and _thread.is_alive():
        _write_status("running", "Already running")
        return "already-running"
    _stop_requested = False
    _prepare_home(files_dir)
    _write_status("starting", "Starting runner")
    _thread = threading.Thread(target=_runner, args=(files_dir,), daemon=True)
    _thread.start()
    return "started"


def stop():
    global _stop_requested, _thread
    _stop_requested = True
    stop_flag = _stop_flag_path()
    if stop_flag:
        with open(stop_flag, "w", encoding="utf-8") as f:
            f.write(_now())
    _write_status("stopping", "Stop requested")
    return "stop-requested"
