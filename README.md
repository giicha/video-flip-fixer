# Video flip fixer

A lightweight, high-performance, and fully standalone desktop application built with Python 3 and PyQt6. This tool performs cross-platform, **lossless (no re-encoding)** resetting of video orientation metadata matrices (such as the Apple iPhone `-display_rotation` flag) in just a fraction of a second.

It uses an advanced **Web Deployment / Bundled Hybrid Architecture** powered by `static-ffmpeg` to achieve complete autonomy and offline capability without requiring any pre-installed global system dependencies.

---

## Key Features

- ** 100% Lossless & Instant:** Resets hidden rotation metadata flags (0°) while perfectly copying original video and audio streams (`-c copy`). Processing a 500MB file takes less than 0.5 seconds.
- ** Zero-Dependency Executable:** Bundles full-production `ffmpeg` and `ffprobe` binaries internally within a single, portable Windows `.exe` application via cloud automation.
- ** Robust Offline Capability:** Once compiled or deployed, the application operates in a completely isolated air-gapped environment. It never makes stealthy update checks or network calls during runtime.
- ** Professional Camera Support:** Enhanced block-by-block streaming metadata parser securely resolves complex or non-standard index definitions (`moov` / `tkhd` atoms) found at the very end of heavy cinema files (Sony, RED, ARRI, iPhone 15 Pro+ ProRES).
- ** Automated CI/CD Releases:** Fully integrated with GitHub Actions. Pushing a version tag automatically compiles, signs, and attaches the release asset to your repository.

---

## Project Structure

Before initializing repository packaging, verify that your local workspace strictly matches the following layout:

```text
video-flip-fixer/
├── .github/
│   └── workflows/
│       └── release.yml      # GitHub Actions CI/CD workflow script
├── .gitignore               # Strict build cache exclusion patterns
├── core.py                  # Isolated video metadata processing engine
├── main.py                  # PyQt6 responsive Drag & Drop GUI interface
├── build_release.py         # PyInstaller local/cloud build coordinator
└── README.md                # Project documentation
```

---

## Core Component Architectures

### 1. Graphical Interface (`main.py`)
Implements an asynchronous PyQt6 thread workflow (`QThread`). Heavy operations (file IO execution, metadata extraction, structural cloning) are completely decoupled from the main thread, keeping the GUI smoothly responsive and preventing accidental OS freezes during batch operations.

### 2. Video Processing Engine (`core.py`)
Bypasses restrictive wrapper abstractions by executing clean, low-level `subprocess` operations with `CREATE_NO_WINDOW` flags to suppress console popups. It dynamically maps execution directories using `sys._MEIPASS` when frozen inside a virtual boot sandbox environment.

### 3. Cloud Packaging Specification (`build_release.py`)
Automates the local discovery of absolute module environment paths on virtual hosts. It structures the output parameters of PyInstaller using the `--add-data` protocol, mapping compiled binary payloads directly into an internal standalone application subfolder named `bin/`.

---

## Local Development & Setup

To run the project locally from source using Visual Studio Code, follow these environment installation steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd video-flip-fixer
   ```

2. **Install Python environment dependencies:**
   ```bash
   pip install PyQt6 requests static-ffmpeg pyinstaller
   ```

3. **Verify engine integrity:**
   Run the main entry script directly from your terminal:
   ```bash
   python main.py
   ```
   *Note: On your first local launch, `static-ffmpeg` will securely stream verified, official production binaries into your Python site-packages environment layout.*

---

## CI/CD Deployment via GitHub Actions

The compilation process is fully handled in the cloud using Microsoft Windows Runners. You never need to manually pack your files or risk local character mapping (`CP1252` vs `UTF-8`) compilation crashes.

To release a new version with an automated version-tagged executable (e.g., `video-flip-fixer-v1.0.0.exe`):

1. **Commit and push your clean workspace changes:**
   ```bash
   git add .
   git commit -m "Release stable production core build"
   git push origin main
   ```

2. **Create and publish a version tag:**
   ```bash
   git tag -a v1.0.0 -m "Version 1.0.0 Release"
   git push origin v1.0.0
   ```

3. **Monitor Cloud Pipeline:**
   Navigate to the **Actions** tab on your GitHub repository page. The automated runner will spin up a fresh Windows environment, resolve execution configurations, compile the single binary payload via PyInstaller, and attach the portable application to a freshly minted **GitHub Release** page automatically.

---

## Technical Specifications

- **UI Framework:** PyQt6 (Qt 6.x)
- **Binary Stream Core:** FFmpeg / FFprobe (Full Essentials Build Layer)
- **Compilation Engine:** PyInstaller 6.x+ (Configured with custom system stream interceptors to block windowed environment crashes)
- **Target OS Deployment:** Windows 10 / 11 (Architecture target x64)
- **Metadata Target:** `tkhd` atom display transformation matrix coordinates (Resetting translation maps to uniform identity grids)
