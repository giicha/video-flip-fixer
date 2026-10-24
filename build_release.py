import os
import subprocess
import sys
import shutil
from static_ffmpeg import run

def build():
    print("=== Preparing fully offline release build with local bin/ folder ===")
    
    # 1. Fetch paths inside GitHub Actions environment to locate binaries
    try:
        ffmpeg_exe, ffprobe_exe = run.get_or_fetch_platform_executables_else_raise()
        static_ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        print(f"Target static-ffmpeg binaries found at: {static_ffmpeg_dir}")
    except Exception as e:
        print(f"Error resolving static-ffmpeg paths: {e}")
        sys.exit(1)

    # 2. Clean up previous build directories
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # 3. Dynamically determine the executable name based on GitHub Release Tag
    release_tag = os.environ.get("GITHUB_REF_NAME", "")
    if release_tag and release_tag.startswith("v"):
        exe_name = f"video-flip-fixer-{release_tag}"
    else:
        exe_name = "video-flip-fixer"

    print(f"Target executable filename configured as: {exe_name}.exe")

    # 4. Compile standalone .exe with custom icon and explicit multiple data mappings
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={exe_name}",
        f"--icon=icon.ico",
        "--add-data", f"icon.ico{os.path.pathsep}.",  # First explicit mapping for app icon asset
        "--add-data", f"{static_ffmpeg_dir}{os.path.pathsep}bin",  # Second explicit mapping for video utilities
        "main.py"
    ]

    print("\n=== Running PyInstaller ===")
    result = subprocess.run(cmd, text=True)
    
    if result.returncode == 0:
        print("\n=== BUILD COMPLETED SUCCESSFULLY! ===")
        exe_path = os.path.join("dist", f"{exe_name}.exe")
        if os.path.exists(exe_path):
            print(f"Output standalone file size: {os.path.getsize(exe_path) // (1024*1024)} MB")
    else:
        print("\nCompilation error occurred.")
        sys.exit(1)

if __name__ == "__main__":
    build()
