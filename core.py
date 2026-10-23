import os
import sys
import subprocess
import json
import traceback

# NullWriter class intercepts download logs when stdout/stderr streams are unavailable
class NullWriter:
    def write(self, text): pass
    def flush(self): pass
    def isatty(self): return False  # Fixes the 'progress' module validation crash

# Redirect system streams if stripped by PyInstaller inside the windowed .exe
if sys.stdout is None: sys.stdout = NullWriter()
if sys.stderr is None: sys.stderr = NullWriter()

from static_ffmpeg import run

def get_ffmpeg_paths(log_callback=None):
    """Automatically downloads fresh FFmpeg binaries on first run and returns paths."""
    try:
        ffmpeg_exe, ffprobe_exe = run.get_or_fetch_platform_executables_else_raise()
        return ffmpeg_exe, ffprobe_exe
    except Exception as e:
        if log_callback:
            error_details = traceback.format_exc()
            log_callback(f"Engine Initialization Failed:\n{error_details}")
        return None, None

def check_rotation(file_path, log_callback=None):
    _, FFPROBE_PATH = get_ffmpeg_paths(log_callback)
    if not FFPROBE_PATH or not os.path.exists(FFPROBE_PATH):
        return 0, "Error: ffprobe engine not ready!"

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
        
        # Check container format tags first
        rot = data.get("format", {}).get("tags", {}).get("rotate")
        if rot is not None: return abs(int(float(rot))), "OK"
        
        # Check video stream tags safely treating 'streams' as a list
        streams = data.get("streams", [])
        if streams and isinstance(streams, list):
            # Access the first stream item in the list safely
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

    FFMPEG_PATH, _ = get_ffmpeg_paths(log_callback)
    if not FFMPEG_PATH or not os.path.exists(FFMPEG_PATH):
        send_log("Error: ffmpeg engine not ready!")
        return

    try:
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
