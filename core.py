import os
import sys
import subprocess
import json

# Определение базовой директории для PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BIN_DIR = os.path.join(BASE_DIR, "bin")

# Адаптация расширений под ОС
EXE_EXT = ".exe" if sys.platform == "win32" else ""
FFMPEG_PATH = os.path.join(BIN_DIR, f"ffmpeg{EXE_EXT}")
FFPROBE_PATH = os.path.join(BIN_DIR, f"ffprobe{EXE_EXT}")

def check_rotation(file_path, log_callback=None):
    if not os.path.exists(FFPROBE_PATH):
        return 0, f"Error: Local bin/ffprobe{EXE_EXT} not found!"

    cmd = [
        FFPROBE_PATH, "-v", "error", "-select_streams", "v:0", 
        "-show_entries", "stream_tags=rotate:stream_side_data=rotation:format_tags=rotate", 
        "-of", "json", file_path
    ]
    try:
        # Убираем creationflags для macOS
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            errors='ignore', 
            timeout=15,
            **kwargs
        )
        if not result.stdout or not result.stdout.strip(): 
            return 0, "OK"
        data = json.loads(result.stdout)
        
        rot = data.get("format", {}).get("tags", {}).get("rotate")
        if rot is not None: return abs(int(float(rot))), "OK"
        
        streams = data.get("streams", [])
        if streams and isinstance(streams, list):
            first_stream = streams[0]
            r = first_stream.get("tags", {}).get("rotate")
            if r is not None: return abs(int(float(r))), "OK"
            
            for sd in first_stream.get("side_data_list", []):
                rotation = sd.get("rotation")
                if rotation is not None: return abs(int(float(rotation))), "OK"
    except Exception as e:
        return 0, f"ffprobe error: {str(e)}"
    return 0, "OK"

def process_video(file_path, mode="copy_near", output_folder=None, log_callback=None):
    def send_log(msg):
        if log_callback: log_callback(str(msg))

    if not os.path.exists(FFMPEG_PATH):
        send_log(f"Error: Local bin/ffmpeg{EXE_EXT} not found!")
        return

    try:
        send_log(f"Analyzing metadata for file: {os.path.basename(file_path)}")
        rotation, status_msg = check_rotation(file_path, log_callback)
        if status_msg != "OK":
            send_log(f"-> {status_msg}")
            return
        if rotation == 0:
            send_log(f"-> {os.path.basename(file_path)}: Rotation is already 0° (skipping).")
            return

        send_log(f"-> {os.path.basename(file_path)}: Found {rotation}° rotation. Resetting display matrix...")
        dir_name = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        name_without_ext, ext = os.path.splitext(base_name)

        if mode == "overwrite": 
            temp_output = os.path.join(dir_name, f"temp_fix_{base_name}")
        elif mode == "copy_near": 
            temp_output = os.path.join(dir_name, f"{name_without_ext}_fixed{ext}")
        elif mode == "copy_to_folder":
            os.makedirs(output_folder, exist_ok=True)
            temp_output = os.path.join(output_folder, base_name)
        else: 
            return

        cmd = [FFMPEG_PATH, "-y", "-display_rotation", "0", "-i", file_path, "-c", "copy", "-map_metadata", "0", temp_output]
        
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            errors='ignore',
            **kwargs
        )
        
        if result.returncode != 0:
            send_log(f"ffmpeg error: {result.stderr}")
            if os.path.exists(temp_output): 
                os.remove(temp_output)
            return

        if mode == "overwrite":
            os.remove(file_path)
            os.rename(temp_output, file_path)
            send_log(f"Successfully updated original file: {base_name}")
        else:
            send_log(f"Successfully saved fixed file: {os.path.basename(temp_output)}")
    except Exception as e:
        send_log(f"Failed: {str(e)}")
