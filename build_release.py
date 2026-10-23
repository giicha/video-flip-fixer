import os
import subprocess
import sys
import shutil
from static_ffmpeg import run

def build():
    print("=== Preparing cloud release build ===")
    
    try:
        ffmpeg_exe, ffprobe_exe = run.get_or_fetch_platform_executables_else_raise()
        static_ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        print(f"static-ffmpeg binaries deployed at: {static_ffmpeg_dir}")
    except Exception as e:
        print(f"static-ffmpeg initialization error: {e}")
        sys.exit(1)

    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=video-flip-fixer",
        f"--add-data={static_ffmpeg_dir};static_ffmpeg/bin",
        "main.py"
    ]

    print("\n=== Running PyInstaller ===")
    result = subprocess.run(cmd, text=True)
    
    if result.returncode == 0:
        print("\n=== BUILD COMPLETED SUCCESSFULLY! ===")
        exe_path = os.path.join("dist", "video-flip-fixer.exe")
        if os.path.exists(exe_path):
            print(f"Output file size: {os.path.getsize(exe_path) // (1024*1024)} MB")
    else:
        print("\nCompilation error occurred.")
        sys.exit(1)

if __name__ == "__main__":
    build()
