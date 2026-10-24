import os
import subprocess
import sys
import shutil
from static_ffmpeg import run

def build():
    print(f"=== Preparing fully offline release build for {sys.platform} ===")
    
    # 1. Поиск путей к ffmpeg
    try:
        ffmpeg_exe, ffprobe_exe = run.get_or_fetch_platform_executables_else_raise()
        static_ffmpeg_dir = os.path.abspath(os.path.dirname(ffmpeg_exe))
        print(f"Target static-ffmpeg binaries found at: {static_ffmpeg_dir}")
    except Exception as e:
        print(f"Error resolving static-ffmpeg paths: {e}")
        sys.exit(1)

    # 2. Очистка старых папок
    for folder in ["build", "dist", "bin"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    os.makedirs("bin", exist_ok=True)
    
    # Суффиксы файлов в зависимости от платформы
    exe_ext = ".exe" if sys.platform == "win32" else ""
    icon_ext = ".ico" if sys.platform == "win32" else ".icns"
    
    # 3. Копирование бинарников без жесткой привязки к .exe
    try:
        shutil.copy2(os.path.join(static_ffmpeg_dir, f"ffmpeg{exe_ext}"), os.path.join("bin", f"ffmpeg{exe_ext}"))
        shutil.copy2(os.path.join(static_ffmpeg_dir, f"ffprobe{exe_ext}"), os.path.join("bin", f"ffprobe{exe_ext}"))
        print("Successfully copied binaries into the local project bin/ folder.")
    except Exception as copy_err:
        print(f"Failed to copy binaries locally: {copy_err}")
        sys.exit(1)

    # 4. Имя выходного файла/папки
    release_tag = os.environ.get("GITHUB_REF_NAME", "")
    if release_tag and release_tag.startswith("v"):
        exe_name = f"video-flip-fixer-{release_tag}"
    else:
        exe_name = "video-flip-fixer"

    # 5. Настройка параметров PyInstaller
    icon_file = f"icon{icon_ext}"
    if not os.path.exists(icon_file):
        # Если .icns файла нет, временно игнорируем или используем дефолтный
        icon_arg = []
    else:
        icon_arg = [f"--icon={icon_file}"]

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={exe_name}",
        *icon_arg,
        "--add-data", f"icon.ico{os.path.pathsep}.",  # оставляем для совместимости ресурсов внутри UI
        "--add-data", f"bin{os.path.pathsep}bin",  
        "main.py"
    ]

    print("\n=== Running PyInstaller ===")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
    
    print(result.stdout)
    if result.returncode != 0:
        print("\n=== PYINSTALLER COMPILATION ERROR LOG ===")
        print(result.stderr)
        print("=========================================\n")
    
    if os.path.exists("bin"):
        shutil.rmtree("bin")
        
    if result.returncode == 0:
        print("\n=== BUILD COMPLETED SUCCESSFULLY! ===")
        # На macOS создается и исполняемый файл в dist/, и бандл .app
        if sys.platform == "darwin":
            # Архивируем .app в .zip, так как GitHub Releases не поддерживает загрузку папок напрямую
            app_path = os.path.join("dist", f"{exe_name}.app")
            zip_path = os.path.join("dist", f"{exe_name}-macOS.zip")
            if os.path.exists(app_path):
                print("Archiving .app bundle into zip for macOS release...")
                shutil.make_archive(zip_path.replace('.zip', ''), 'zip', root_dir="dist", base_dir=f"{exe_name}.app")
    else:
        print("\nCompilation error occurred.")
        sys.exit(1)

if __name__ == "__main__":
    build()
