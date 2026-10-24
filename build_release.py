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
        static_ffmpeg_dir = os.path.abspath(os.path.dirname(ffmpeg_exe))
        print(f"Target static-ffmpeg binaries found at: {static_ffmpeg_dir}")
    except Exception as e:
        print(f"Error resolving static-ffmpeg paths: {e}")
        sys.exit(1)

    # 2. Clean up previous build directories and local temporary bins
    for folder in ["build", "dist", "bin"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # 3. Create a clean local 'bin' directory and copy the binaries directly into it
    os.makedirs("bin", exist_ok=True)
    try:
        shutil.copy2(os.path.join(static_ffmpeg_dir, "ffmpeg.exe"), os.path.join("bin", "ffmpeg.exe"))
        shutil.copy2(os.path.join(static_ffmpeg_dir, "ffprobe.exe"), os.path.join("bin", "ffprobe.exe"))
        print("Successfully copied binaries into the local project bin/ folder.")
    except Exception as copy_err:
        print(f"Failed to copy binaries locally: {copy_err}")
        sys.exit(1)

    # 4. Dynamically determine the executable name based on GitHub Release Tag
    release_tag = os.environ.get("GITHUB_REF_NAME", "")
    if release_tag and release_tag.startswith("v"):
        exe_name = f"video-flip-fixer-{release_tag}"
    else:
        exe_name = "video-flip-fixer"

    print(f"Target executable filename configured as: {exe_name}.exe")

    # 5. Compile standalone .exe mapping our safe clean local folders
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={exe_name}",
        f"--icon=icon.ico",
        "--add-data", f"icon.ico{os.path.pathsep}.",  
        "--add-data", f"bin{os.path.pathsep}bin",  
        "main.py"
    ]

    print("\n=== Running PyInstaller ===")
    # Capture stderr to show the exact reason for the compilation crash
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
    
    print(result.stdout)
    if result.returncode != 0:
        print("\n=== PYINSTALLER COMPILATION ERROR LOG ===")
        print(result.stderr)
        print("=========================================\n")
    
    # 6. Post-build cleanup of the temporary local bin folder
    if os.path.exists("bin"):
        shutil.rmtree("bin")
        
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
