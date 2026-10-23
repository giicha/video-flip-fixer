import os
import zipfile
import urllib.request
import shutil

# 1. Берем точную прямую ссылку на стабильный ZIP-релиз с gyan.dev
url = 'https://gyan.dev'
zip_name = 'ffmpeg.zip'
target_bin_dir = 'bin'

try:
    print('Подключение к gyan.dev и скачивание FFmpeg (около 130 МБ)...')
    
    # Создаем запрос и добавляем заголовки, чтобы сайт думал, что качает обычный браузер Edge/Chrome
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    # Скачиваем файл потоком и сохраняем на диск
    with urllib.request.urlopen(req) as response, open(zip_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
        
    print('Скачивание завершено! Проверка и распаковка...')
    
    # Проверяем, что скачался именно архив, а не страница ошибки
    if not zipfile.is_zipfile(zip_name):
        raise zipfile.BadZipFile("Скачанный файл поврежден или заблокирован сервером (Cloudflare).")

    # Создаем чистую папку для распаковки
    extract_temp_dir = 'ffmpeg_temp'
    os.makedirs(target_bin_dir, exist_ok=True)

    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        zip_ref.extractall(extract_temp_dir)

    print('Поиск и извлечение ffmpeg.exe и ffprobe.exe...')
    # Пробегаемся по распакованным папкам, находим нужные бинарники и переносим их в нашу папку bin/
    for root, dirs, files in os.walk(extract_temp_dir):
        for file in files:
            if file.lower() in ["ffmpeg.exe", "ffprobe.exe"]:
                # Переносим файлы в итоговую папку bin рядом со скриптом
                shutil.move(os.path.join(root, file), os.path.join(target_bin_dir, file.lower()))

    # Чистим за собой мусор и временные папки
    if os.path.exists(zip_name): 
        os.remove(zip_name)
    if os.path.exists(extract_temp_dir): 
        shutil.rmtree(extract_temp_dir)
        
    print('Готово! Исполняемые файлы успешно сохранены в папку "bin".')

except Exception as e:
    print(f'\nПроизошла ошибка при обновлении: {e}')
    # Удаляем временные файлы в случае сбоя, чтобы не захламлять папку
    if os.path.exists(zip_name): os.remove(zip_name)
