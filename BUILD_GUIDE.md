# Hướng dẫn Đóng gói thành EXE

## 📦 Build Executable File cho Logic Analyzer

---

## Phương Pháp 1: Dùng PyInstaller (Khuyến nghị)

### 1.1 Cài đặt PyInstaller

```bash
pip install pyinstaller
```

### 1.2 Build đơn giản

```bash
pyinstaller main_enhanced.py --onefile --windowed --name=LogicAnalyzer
```

**Kết quả**: `dist/LogicAnalyzer.exe`

### 1.3 Build nâng cao (với tất cả tùy chọn)

```bash
pyinstaller main_enhanced.py ^
    --onefile ^
    --windowed ^
    --name=LogicAnalyzer ^
    --icon=icon.ico ^
    --add-data=".:." ^
    --collect-all=pyqtgraph ^
    --collect-all=PyQt5 ^
    --collect-all=serial ^
    --collect-all=colorama ^
    --hidden-import=pyqtgraph.core ^
    --hidden-import=pyqtgraph.graphicsItems ^
    --build-temp=build ^
    --distpath=dist ^
    --clean ^
    -y
```

### 1.4 Sử dụng Build Script

```bash
python build_exe.py
```

---

## Phương Pháp 2: Dùng Script Tự động

### 2.1 Tạo file `build_advanced.py`

```python
#!/usr/bin/env python
"""
Advanced build script với logging & verification
"""
import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

def clean_build_artifacts():
    """Xóa build artifacts cũ"""
    dirs = ['build', 'dist', '__pycache__']
    for d in dirs:
        if os.path.exists(d):
            print(f"Removing {d}...")
            shutil.rmtree(d)

def verify_dependencies():
    """Kiểm tra tất cả dependencies"""
    required = ['PyQt5', 'pyqtgraph', 'numpy', 'serial', 'colorama']
    
    print("Verifying dependencies...")
    try:
        import PyQt5
        import pyqtgraph
        import numpy
        import serial
        import colorama
        print("✓ All dependencies found")
        return True
    except ImportError as e:
        print(f"✗ Missing: {e}")
        return False

def build_exe():
    """Build executable"""
    
    print("\n" + "="*60)
    print("Logic Analyzer EXE Build")
    print("="*60)
    
    # Verify
    if not verify_dependencies():
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Clean
    clean_build_artifacts()
    
    # Build arguments
    args = [
        'main_enhanced.py',
        '--onefile',
        '--windowed',
        '--name=LogicAnalyzer',
        '--distpath=dist',
        '--buildpath=build',
        '--specpath=.',
        '--collect-all=pyqtgraph',
        '--collect-all=PyQt5',
        '--collect-all=serial',
        '--collect-all=colorama',
        '--hidden-import=pyqtgraph.graphicsItems',
        '--hidden-import=pyqtgraph.viewBox',
        '-y',
    ]
    
    # Nếu có icon
    if os.path.exists('icon.ico'):
        args.append('--icon=icon.ico')
    
    print(f"\nBuilding with command:")
    print(f"pyinstaller {' '.join(args)}\n")
    
    try:
        PyInstaller.__main__.run(args)
        
        # Verify output
        exe_path = Path('dist/LogicAnalyzer.exe')
        if exe_path.exists():
            exe_size = exe_path.stat().st_size / (1024**2)
            print("\n" + "="*60)
            print(f"✓ Build SUCCESSFUL!")
            print(f"  Executable: {exe_path}")
            print(f"  Size: {exe_size:.2f} MB")
            print("="*60)
            
            # Copy readme
            if os.path.exists('README.md'):
                shutil.copy('README.md', 'dist/README.md')
                print("✓ README.md copied")
            
            return True
        else:
            print("✗ Build failed - executable not found")
            return False
            
    except Exception as e:
        print(f"✗ Build error: {e}")
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
```

**Chạy**:
```bash
python build_advanced.py
```

### 2.2 Tạo file `build_portable.bat` (Windows)

```batch
@echo off
echo.
echo ============================================================
echo Logic Analyzer - Portable EXE Builder
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found!
    pause
    exit /b 1
)

REM Install/Upgrade PyInstaller
echo Installing PyInstaller...
pip install --upgrade pyinstaller

REM Clean old builds
echo.
echo Cleaning old builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build
echo.
echo Building executable...
pyinstaller main_enhanced.py ^
    --onefile ^
    --windowed ^
    --name=LogicAnalyzer ^
    --collect-all=pyqtgraph ^
    --collect-all=PyQt5 ^
    --collect-all=serial ^
    --clean ^
    -y

echo.
echo ============================================================
if exist "dist\LogicAnalyzer.exe" (
    echo Success! Executable created at: dist\LogicAnalyzer.exe
    echo.
    echo File size: 
    for %%A in (dist\LogicAnalyzer.exe) do echo %%~zA bytes
) else (
    echo Failed! Check output above for errors.
)
echo ============================================================
echo.
pause
```

**Chạy**: Double-click `build_portable.bat`

---

## Phương Pháp 3: Dùng cx_Freeze (Multi-platform)

### 3.1 Cài đặt

```bash
pip install cx_Freeze
```

### 3.2 Setup Script

Tạo `setup.py`:

```python
from cx_Freeze import setup, Executable

setup(
    name="LogicAnalyzer",
    version="1.0",
    description="Logic Analyzer GUI",
    executables=[Executable("main_enhanced.py")],
    options={
        "build_exe": {
            "packages": ["PyQt5", "pyqtgraph", "numpy", "serial"],
            "include_files": [],
            "bin_path_excludes": [],
        }
    }
)
```

### 3.3 Build

```bash
python setup.py build
```

---

## Phương Pháp 4: Dùng NSIS (Installer)

### 4.1 Tạo NSIS Script

```nsis
; Logic Analyzer Installer

!include "MUI2.nsh"

Name "Logic Analyzer"
OutFile "LogicAnalyzer_Installer.exe"
InstallDir "$PROGRAMFILES\LogicAnalyzer"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\LogicAnalyzer.exe"
  File "README.md"
  File "requirements.txt"
  
  CreateDirectory "$SMPROGRAMS\LogicAnalyzer"
  CreateShortCut "$SMPROGRAMS\LogicAnalyzer\LogicAnalyzer.lnk" "$INSTDIR\LogicAnalyzer.exe"
  CreateShortCut "$DESKTOP\LogicAnalyzer.lnk" "$INSTDIR\LogicAnalyzer.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\LogicAnalyzer.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\requirements.txt"
  RMDir "$INSTDIR"
  
  Delete "$SMPROGRAMS\LogicAnalyzer\LogicAnalyzer.lnk"
  RMDir "$SMPROGRAMS\LogicAnalyzer"
  Delete "$DESKTOP\LogicAnalyzer.lnk"
SectionEnd
```

**Build**:
```bash
makensis LogicAnalyzer.nsi
```

---

## Phương Pháp 5: GitHub Actions (CI/CD)

### 5.1 Tạo `.github/workflows/build.yml`

```yaml
name: Build LogicAnalyzer EXE

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build EXE
      run: |
        pyinstaller main_enhanced.py --onefile --windowed --name=LogicAnalyzer
    
    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: LogicAnalyzer.exe
        path: dist/LogicAnalyzer.exe
```

---

## Tối ưu Hóa Build

### Giảm Kích thước File

```bash
# Loại bỏ modules không cần thiết
pyinstaller main_enhanced.py \
    --onefile \
    --windowed \
    --exclude-module=matplotlib \
    --exclude-module=scipy \
    --exclude-module=pandas
```

### UPX Compression (không khuyến khích vì antivirus)

```bash
# Download UPX: https://upx.github.io/
pyinstaller main_enhanced.py \
    --onefile \
    --windowed \
    --upx-dir=<path-to-upx>
```

### Boot Mode

```bash
pyinstaller main_enhanced.py \
    --onefile \
    --windowed \
    --noconsole
```

---

## Troubleshooting Build

### Error: ModuleNotFoundError

```bash
# Cài missing module
pip install <module_name>

# Rebuild với --hidden-import
pyinstaller main_enhanced.py \
    --hidden-import=<module_name>
```

### Error: DLL Not Found

```bash
# Thêm vào build
--collect-all=<library>
```

### Slow Build

```bash
# Dùng UPX (tuy chậm hơn nhưng nhỏ hơn)
# hoặc tăng RAM & CPU
```

### Antivirus Warnings

```bash
# PyInstaller EXE thường bị flag bởi antivirus
# Solution: Submit EXE to VirusTotal for analysis
# hoặc dùng digital certificate (code signing)
```

### Runtime Error: No module named 'X'

```bash
# Thêm --hidden-import vào build command
# hoặc cài packages trực tiếp trong virtual env
```

---

## Testing EXE

### Chạy đơn giản

```bash
dist\LogicAnalyzer.exe
```

### Test Mock Mode

1. Click "Connect"
2. Check "Use Mock Device"
3. Click "Connect"
4. Click "Start Capture"
5. Verify biểu đồ hiển thị

### Test Serial Connection

1. Kết nối Pico qua USB
2. Click "Connect"
3. Chọn COM port đúng
4. Click "Connect"
5. Verify status = Connected
6. Click "Start Capture"

### Performance Test

1. Set "Sample Rate" = 1,000,000 Hz
2. Set "Channels" = 16
3. Start capture 10 giây
4. Monitor CPU/Memory trong Task Manager
5. Verify không crash

---

## Distribution

### Folder Structure

```
LogicAnalyzer_v1.0/
├── LogicAnalyzer.exe       (Main executable)
├── README.md               (User guide)
├── REQUIREMENTS.md         (Spec docs)
├── requirements.txt        (Dependencies - for reference)
└── Pico_Firmware/          (Example firmware)
    ├── micropython_example.py
    └── c_sdk_example.c
```

### Packaging

```bash
# Zip file
7z a LogicAnalyzer_v1.0.zip dist\LogicAnalyzer.exe README.md REQUIREMENTS.md

# Or create installer (NSIS)
makensis LogicAnalyzer.nsi
```

---

## Size Optimization Tips

| Approach | Size | Build Time |
|----------|------|-----------|
| Normal | ~200-300 MB | 2-3 min |
| --onefile | ~180-250 MB | 3-5 min |
| UPX | ~80-120 MB | 5-10 min |
| --onedir | ~300-400 MB | 1-2 min |

---

**Recommended**: Dùng **Phương Pháp 1 (PyInstaller)** cho đơn giản, hoặc **Phương Pháp 2 (Build Script)** để tự động hóa.
