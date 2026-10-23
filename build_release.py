import os
import subprocess
import sys
import shutil

def build():
    print("=== Preparing lightweight cloud release build ===")
    
    # Clean up output directories from previous builds
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # Compile the standalone GUI executable without bundling heavy ffmpeg binaries
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=video-flip-fixer",
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
