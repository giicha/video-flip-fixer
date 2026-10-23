import os
import subprocess
import json
import shutil

# Ожидаем, что ffmpeg и ffprobe лежат в папке 'bin' рядом со скриптом
BIN_DIR = os.path.join(os.path.dirname(__file__), "bin")
FFMPEG_PATH = os.path.join(BIN_DIR, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(BIN_DIR, "ffprobe.exe")

def check_rotation(file_path):
    """
    Проверяет флаг поворота видео с помощью ffprobe.
    Возвращает угол поворота (int) или 0, если поворота нет/не найден.
    """
    if not os.path.exists(FFPROBE_PATH):
        print(f"Ошибка: Не найден ffprobe.exe в {BIN_DIR}")
        return 0

    # Команда для ffprobe, которая вытаскивает данные о повороте в формате JSON
    cmd = [
        FFPROBE_PATH, "-v", "error", 
        "-select_streams", "v:0", 
        "-show_entries", "stream_tags=rotate:stream_side_data=rotation", 
        "-of", "json", file_path
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
        
        # ffprobe может отдавать поворот в разных полях в зависимости от версии и формата
        streams = data.get("streams", [])
        if streams:
            stream = streams[0]
            # Вариант 1: ищем в старых тегах (tags: rotate)
            rotate = stream.get("tags", {}).get("rotate")
            if rotate is not None:
                return abs(int(float(rotate)))
            
            # Вариант 2: ищем в новых side_data (rotation)
            side_data_list = stream.get("side_data_list", [])
            for side_data in side_data_list:
                rotation = side_data.get("rotation")
                if rotation is not None:
                    return abs(int(float(rotation)))
                    
    except Exception as e:
        print(f"Ошибка при анализе файла {file_path}: {e}")
        
    return 0

def process_video(file_path, mode="copy_near", output_folder=None):
    """
    Обрабатывает видео в зависимости от выбранного режима.
    mode может быть:
      - 'overwrite' (заменить оригинал)
      - 'copy_near' (создать копию рядом с суффиксом _fixed)
      - 'copy_to_folder' (сохранить в указанную папку)
    """
    if not os.path.exists(FFMPEG_PATH):
        print("Ошибка: Не найден ffmpeg.exe!")
        return

    # 1. Проверяем флаг поворота
    rotation = check_rotation(file_path)
    if rotation == 0:
        print(f"-> {os.path.basename(file_path)}: Поворот 0° или не требуется изменений. Пропускаем.")
        return

    print(f"-> {os.path.basename(file_path)}: Обнаружен поворот {rotation}°. Начинаем сброс...")

    # Разбираем путь к файлу
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    name_without_ext, ext = os.path.splitext(base_name)

    # 2. Определяем, куда положить временный или итоговый файл
    if mode == "overwrite":
        # ffmpeg не может писать в тот же файл, что читает, поэтому делаем временный файл
        temp_output = os.path.join(dir_name, f"temp_{base_name}")
    elif mode == "copy_near":
        temp_output = os.path.join(dir_name, f"{name_without_ext}_fixed{ext}")
    elif mode == "copy_to_folder":
        if not output_folder:
            print("Ошибка: Не указана папка для сохранения!")
            return
        os.makedirs(output_folder, exist_ok=True)
        temp_output = os.path.join(output_folder, base_name)
    else:
        print("Неизвестный режим работы.")
        return

    # 3. Запускаем ffmpeg для сброса метаданных поворота без перекодирования
    cmd = [
        FFMPEG_PATH, "-y", "-display_rotation", "0", 
        "-i", file_path, "-c", "copy", temp_output
    ]
    
    try:
        # Запуск процесса в фоновом режиме (скрываем консольное окно ffmpeg)
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # 4. Если режим "заменить оригинал", подменяем файлы
        if mode == "overwrite":
            os.remove(file_path)             # Удаляем оригинал
            os.rename(temp_output, file_path) # Переименовываем временный файл в имя оригинала
            print(f"Успешно: Файл {base_name} перезаписан.")
        else:
            print(f"Успешно: Исправленный файл сохранен в {temp_output}")
            
    except subprocess.CalledProcessError as e:
        print(f"Ошибка ffmpeg при обработке {base_name}: {e}")
        if os.path.exists(temp_output) and mode == "overwrite":
            os.remove(temp_output)

# --- Блок для ручного теста ---
if __name__ == "__main__":
    print("Код готов к работе. Для теста нужно положить ffmpeg.exe и ffprobe.exe в папку 'bin'.")
    # Сюда позже можно вписать тестовый вызов функции, например:
    # process_video("C:/my_video.mp4", mode="copy_near")
