import os
import sys
import subprocess
import json

# Smart path resolution for PyInstaller sandbox vs local VS Code script execution
if getattr(sys, 'frozen', False):
    # Inside compiled .exe: files are extracted to sys._MEIPASS
    BASE_DIR = sys._MEIPASS
else:
    # Local script execution in VS Code
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BIN_DIR = os.path.join(BASE_DIR, "bin")
FFMPEG_PATH = os.path.join(BIN_DIR, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(BIN_DIR, "ffprobe.exe")

def check_rotation(file_path, log_callback=None):
    if not os.path.exists(FFPROBE_PATH):
        return 0, "Error: Local bin/ffprobe.exe not found!"

    cmd = [
        FFPROBE_PATH, "-v", "error", "-select_streams", "v:0", 
        "-show_entries", "stream_tags=rotate:stream_side_data=rotation:format_tags=rotate", 
        "-of", "json", file_path
    ]
    try:
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            errors='ignore', 
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=15
        )
        if not result.stdout or not result.stdout.strip(): 
            return 0, "OK"
        data = json.loads(result.stdout)
        
        # Check container format tags
        rot = data.get("format", {}).get("tags", {}).get("rotate")
        if rot is not None: return abs(int(float(rot))), "OK"
        
        # Check video stream tags safely
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
        send_log("Error: Local bin/ffmpeg.exe not found!")
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
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            errors='ignore', 
            creationflags=subprocess.CREATE_NO_WINDOW
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
