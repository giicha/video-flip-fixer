import os
import platform
import zipfile
import shutil
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")

# План А: Прямая ссылка на CDN GitHub-релизов репозитория GyanD
GITHUB_URL = "https://github.com"

# План Б: Запасное распределенное API-зеркало ffbinaries (отдает файлы без архивации и проверок)
BACKUP_FFMPEG = "https://ffbinaries.com"
BACKUP_FFPROBE = "https://ffbinaries.com"

def get_local_ffmpeg_version():
    """Проверяет наличие файлов ffmpeg и ffprobe в папке bin."""
    ffmpeg_path = os.path.join(BIN_DIR, "ffmpeg.exe")
    ffprobe_path = os.path.join(BIN_DIR, "ffprobe.exe")
    
    if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
        if os.path.getsize(ffmpeg_path) > 10 * 1024 * 1024:
            return "Установлен"
    return None

def download_by_plan_b(send_log):
    """Резервный метод загрузки через независимое CDN-зеркало разработчиков."""
    send_log("Включение резервного плана Б (Альтернативное CDN-зеркало)...")
    exe_ext = ".exe"
    
    targets = {
        "ffmpeg": BACKUP_FFMPEG,
        "ffprobe": BACKUP_FFPROBE
    }

    for name, url in targets.items():
        archive_path = os.path.join(BIN_DIR, f"{name}_backup.zip")
        send_log(f"Скачивание компонента {name}...")
        
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=45)
        response.raise_for_status()
        
        with open(archive_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=512 * 1024):
                if chunk:
                    f.write(chunk)
                    
        if os.path.getsize(archive_path) < 2 * 1024 * 1024:
            return False

        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                filename = os.path.basename(member)
                if filename.lower() == f"{name}{exe_ext}":
                    with zip_ref.open(member) as source, open(os.path.join(BIN_DIR, filename.lower()), "wb") as target:
                        shutil.copyfileobj(source, target)
                        
        if os.path.exists(archive_path):
            os.remove(archive_path)
        send_log(f"Компонент {name} успешно настроен.")
    return True

def download_ffmpeg(progress_callback=None):
    """Скачивает и распаковывает стабильную сборку FFmpeg с защитой от сбоев редиректов."""
    def send_log(msg):
        if progress_callback:
            progress_callback(str(msg))

    if platform.system() != "Windows":
        send_log("Фоновое обновление пока реализовано только для Windows.")
        return False

    os.makedirs(BIN_DIR, exist_ok=True)
    archive_path = os.path.join(BIN_DIR, "ffmpeg_package.zip")
    extract_temp_dir = os.path.join(BIN_DIR, "temp_extracted")

    try:
        send_log("Подключение к серверам хранения репозитория...")
        
        # Создаем сессию, которая правильно обрабатывает куки и перенаправления CDN
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*'
        })
        
        # Принудительно разрешаем редиректы (allow_redirects=True)
        response = session.get(GITHUB_URL, stream=True, allow_redirects=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        # Если сервер сбросил контент или размер равен 0 — сразу уходим на План Б
        if total_size == 0:
            raise Exception("Сервер вернул пустой размер заголовка.")

        send_log(f"Загрузка пакета релизов ({total_size // (1024*1024)} МБ)...")
        with open(archive_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=512 * 1024): # Блоки по 512 КБ
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = int((downloaded / total_size) * 100)
                    if percent % 20 == 0: # Пишем лог каждые 20%
                        send_log(f"Прогресс: {percent}% ({downloaded // (1024*1024)} МБ)")

        # Если файл весит меньше 10 МБ, значит это была ошибка редиректа
        if os.path.getsize(archive_path) < 10 * 1024 * 1024:
            raise Exception("Скачанный архив поврежден или заблокирован сервером.")

        send_log("Распаковка и структурирование файлов...")
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_temp_dir)

        for root, dirs, files in os.walk(extract_temp_dir):
            for file in files:
                if file.lower() in ["ffmpeg.exe", "ffprobe.exe"]:
                    target_path = os.path.join(BIN_DIR, file.lower())
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    shutil.move(os.path.join(root, file), target_path)

        # Чистим кэш
        if os.path.exists(archive_path): os.remove(archive_path)
        if os.path.exists(extract_temp_dir): shutil.rmtree(extract_temp_dir)

        send_log("FFmpeg и FFprobe успешно установлены по основному плану!")
        return True

    except Exception as e:
        send_log(f"Основной сервер вернул ошибку: {str(e)}")
        # Очищаем битый файл перед планом Б
        if os.path.exists(archive_path): os.remove(archive_path)
        if os.path.exists(extract_temp_dir): shutil.rmtree(extract_temp_dir)
        
        # Запуск плана Б
        try:
            success = download_by_plan_b(send_log)
            if success:
                send_log("=== Библиотеки успешно развернуты через резервный сервер! ===")
                return True
            else:
                send_log("Ошибка: Резервное зеркало также недоступно.")
                return False
        except Exception as backup_error:
            send_log(f"Критическая ошибка развертывания: {str(backup_error)}")
            return False
