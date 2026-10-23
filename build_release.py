import os
import subprocess
import sys
import shutil
from static_ffmpeg import run

def build():
    print("=== Подготовка к облачной сборке релиза ===")
    
    # 1. Принудительно вызываем скачивание ffmpeg/ffprobe внутри окружения GitHub
    try:
        ffmpeg_exe, ffprobe_exe = run.get_or_fetch_platform_executables_else_raise()
        static_ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        print(f"Бинарники static-ffmpeg развернуты в: {static_ffmpeg_dir}")
    except Exception as e:
        print(f"Ошибка инициализации static-ffmpeg: {e}")
        sys.exit(1)

    # 2. Очистка прошлых папок
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # 3. Команда PyInstaller для создания ОДНОГО монолитного .exe (--onefile)
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",                    # Собираем всё в ОДИН исполняемый файл
        "--windowed",                   # Отключаем консоль при запуске GUI
        "--name=video-flip-fixer",  # Имя готового файла
        f"--add-data={static_ffmpeg_dir};static_ffmpeg/bin",
        "main.py"
    ]

    print("\n=== Запуск сборки через PyInstaller ===")
    result = subprocess.run(cmd, text=True)
    
    if result.returncode == 0:
        print("\n=== СБОРКА УСПЕШНО ЗАВЕРШЕНА! ===")
        exe_path = os.path.join("dist", "video-flip-fixer.exe")
        if os.path.exists(exe_path):
            print(f"Размер готового файла: {os.path.getsize(exe_path) // (1024*1024)} МБ")
    else:
        print("\nОшибка компиляции проекта.")
        sys.exit(1)

if __name__ == "__main__":
    build()
