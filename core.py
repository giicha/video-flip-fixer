import os
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")
FFMPEG_PATH = os.path.join(BIN_DIR, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(BIN_DIR, "ffprobe.exe")

def check_rotation(file_path):
    if not os.path.exists(FFPROBE_PATH):
        return 0, "Ошибка: ffprobe.exe не найден!"

    cmd = [
        FFPROBE_PATH, "-v", "error", "-select_streams", "v:0", 
        "-show_entries", "stream_tags=rotate:stream_side_data=rotation:format_tags=rotate", 
        "-of", "json", file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore', creationflags=subprocess.CREATE_NO_WINDOW)
        if not result.stdout or not result.stdout.strip(): return 0, "Ок"
        data = json.loads(result.stdout)
        
        # Проверяем тег контейнера
        rot = data.get("format", {}).get("tags", {}).get("rotate")
        if rot is not None: return abs(int(float(rot))), "Ок"
        
        # Проверяем теги самого видеопотока
        streams = data.get("streams", [])
        if streams:
            r = streams[0].get("tags", {}).get("rotate")
            if r is not None: return abs(int(float(r))), "Ок"
            for sd in streams[0].get("side_data_list", []):
                rotation = sd.get("rotation")
                if rotation is not None: return abs(int(float(rotation))), "Ок"
    except Exception as e:
        return 0, f"Ошибка: {str(e)}"
    return 0, "Ок"

def process_video(file_path, mode="copy_near", output_folder=None, log_callback=None):
    def send_log(msg):
        if log_callback: log_callback(str(msg))

    if not os.path.exists(FFMPEG_PATH):
        send_log("Ошибка: Нужен FFmpeg. Нажмите синюю кнопку 'Обновить FFmpeg' справа внизу!")
        return

    try:
        rotation, status_msg = check_rotation(file_path)
        if status_msg != "Ок":
            send_log(f"-> {status_msg}")
            return
        if rotation == 0:
            send_log(f"-> {os.path.basename(file_path)}: Поворот уже 0° (исправление не требуется).")
            return

        send_log(f"-> {os.path.basename(file_path)}: Полный сброс всех скрытых матриц...")
        dir_name = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        name_without_ext, ext = os.path.splitext(base_name)

        if mode == "overwrite": temp_output = os.path.join(dir_name, f"temp_fix_{base_name}")
        elif mode == "copy_near": temp_output = os.path.join(dir_name, f"{name_without_ext}_fixed{ext}")
        elif mode == "copy_to_folder":
            os.makedirs(output_folder, exist_ok=True)
            temp_output = os.path.join(output_folder, base_name)
        else: return

        # Сбрасывает display_rotation на 0 и в контейнере, и во всех внутренних стримах
        cmd = [FFMPEG_PATH, "-y", "-display_rotation", "0", "-i", file_path, "-c", "copy", "-map_metadata", "0", temp_output]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore', creationflags=subprocess.CREATE_NO_WINDOW)
        
        if result.returncode != 0:
            send_log(f"Ошибка: {result.stderr}")
            if os.path.exists(temp_output): os.remove(temp_output)
            return

        if mode == "overwrite":
            os.remove(file_path)
            os.rename(temp_output, file_path)
            send_log(f"Успешно исправлен оригинал: {base_name}")
        else:
            send_log(f"Успешно сохранен исправленный файл: {os.path.basename(temp_output)}")
    except Exception as e:
        send_log(f"Сбой: {str(e)}")
