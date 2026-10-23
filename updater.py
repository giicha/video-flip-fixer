import os
import platform
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")

# Прямые ссылки на уже распакованные, готовые к работе файлы
# Используем официальные сборки проекта yt-dlp, которые всегда доступны
URLS = {
    "Windows": {
        "ffmpeg": "https://github.com",
        "ffprobe": "https://github.com"
    },
    "Linux": {
        "ffmpeg": "https://github.com",
        "ffprobe": "https://github.com" # Для простоты пока настроим Windows
    },
    "Darwin": { # macOS
        "ffmpeg": "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg",
        "ffprobe": "https://github.com"
    }
}

def get_os_type():
    return platform.system()

def download_single_file(url, target_name, progress_callback):
    """Скачивает один файл напрямую по ссылке."""
    target_path = os.path.join(BIN_DIR, target_name)
    log(f"Скачивание {target_name} напрямую с сервера...", progress_callback)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Скачиваем поток данных
    with requests.get(url, headers=headers, stream=True, allow_redirects=True, timeout=60) as r:
        r.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024): # Блоками по 1 МБ
                if chunk:
                    f.write(chunk)
    
    log(f"Успешно сохранен: {target_name}", progress_callback)

def download_ffmpeg(progress_callback=None):
    os_type = get_os_type()
    if os_type not in URLS:
        log(f"Ошибка: Операционная система {os_type} не поддерживается.", progress_callback)
        return False

    os.makedirs(BIN_DIR, exist_ok=True)
    files_to_download = URLS[os_type]

    try:
        log(f"Начало загрузки инструментов для {os_type}...", progress_callback)
        
        exe_ext = ".exe" if os_type == "Windows" else ""
        
        # Скачиваем ffmpeg
        download_single_file(files_to_download["ffmpeg"], f"ffmpeg{exe_ext}", progress_callback)
        # Скачиваем ffprobe
        download_single_file(files_to_download["ffprobe"], f"ffprobe{exe_ext}", progress_callback)

        # Выставляем права на запуск для Linux/Mac
        if os_type in ["Linux", "Darwin"]:
            for binary in ["ffmpeg", "ffprobe"]:
                bin_path = os.path.join(BIN_DIR, binary)
                if os.path.exists(bin_path):
                    os.chmod(bin_path, 0o755)

        log("FFmpeg и FFprobe успешно обновлены!", progress_callback)
        return True

    except Exception as e:
        log(f"Ошибка при обновлении: {e}", progress_callback)
        return False

def log(message, callback):
    print(message)
    if callback:
        callback(message)

if __name__ == "__main__":
    download_ffmpeg()
