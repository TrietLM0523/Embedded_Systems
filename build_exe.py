"""
Setup script để đóng gói Logic Analyzer thành executable
Sử dụng PyInstaller
"""

import PyInstaller.__main__
import os
import sys

def build_exe():
    """Build executable file"""
    
    script_name = "main_enhanced.py"
    
    # PyInstaller arguments
    args = [
        script_name,
        '--name=LogicAnalyzer',
        '--onefile',  # Pack all vào 1 file
        '--windowed',  # Không hiển thị console window
        '--icon=icon.ico',  # Icon (optional)
        '--add-data=.:.',
        '--collect-all=pyqtgraph',
        '--collect-all=PyQt5',
        '-y',  # Overwrite
    ]
    
    # Nếu trên Windows, thêm Windows-specific options
    if sys.platform == 'win32':
        args.extend([
            '--collect-all=serial',
            '--collect-all=colorama',
        ])
    
    print("Building Logic Analyzer executable...")
    print(f"Command: pyinstaller {' '.join(args)}")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✓ Build successful!")
        print("Executable tại: dist/LogicAnalyzer.exe")
    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()
