"""
Quick Start Guide - Setup & Test Logic Analyzer

Chạy script này để setup environment & test ứng dụng
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def check_python():
    """Check Python version"""
    print_header("CHECKING PYTHON")
    
    version = sys.version_info
    print(f"Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required!")
        return False
    
    print("✓ Python version OK")
    return True

def check_venv():
    """Check if virtual environment is active"""
    print_header("CHECKING VIRTUAL ENVIRONMENT")
    
    if hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    ):
        print(f"✓ Virtual environment active: {sys.prefix}")
        return True
    else:
        print("⚠ No virtual environment detected")
        print("Recommendation: Create with 'python -m venv la_env'")
        return True  # Not fatal

def install_requirements():
    """Install required packages"""
    print_header("INSTALLING DEPENDENCIES")
    
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    print(f"Installing from {req_file}...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=False
        )
        print("✓ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def verify_imports():
    """Verify all required imports"""
    print_header("VERIFYING IMPORTS")
    
    modules = {
        "PyQt5": "GUI Framework",
        "pyqtgraph": "Plotting Library",
        "numpy": "Numerical Computing",
        "serial": "Serial Communication",
        "colorama": "Terminal Colors",
    }
    
    all_ok = True
    for module, desc in modules.items():
        try:
            __import__(module)
            print(f"✓ {module:15} - {desc}")
        except ImportError as e:
            print(f"❌ {module:15} - {desc} (NOT FOUND)")
            all_ok = False
    
    return all_ok

def check_project_structure():
    """Check project structure"""
    print_header("CHECKING PROJECT STRUCTURE")
    
    required_files = [
        "main_enhanced.py",
        "la_core_enhanced.py",
        "serial_interface.py",
        "protocol_decoder.py",
        "requirements.txt",
    ]
    
    all_ok = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            size = path.stat().st_size / 1024
            print(f"✓ {file:30} ({size:.1f} KB)")
        else:
            print(f"❌ {file:30} (NOT FOUND)")
            all_ok = False
    
    return all_ok

def test_imports():
    """Test import modules"""
    print_header("TESTING MODULE IMPORTS")
    
    try:
        print("Importing la_core_enhanced...", end=" ")
        from la_core_enhanced import LACore, LACanvas
        print("✓")
        
        print("Importing serial_interface...", end=" ")
        from serial_interface import PicoSerialInterface, MockPicoInterface
        print("✓")
        
        print("Importing protocol_decoder...", end=" ")
        from protocol_decoder import UARTDecoder, I2CDecoder, SPIDecoder
        print("✓")
        
        print("\n✓ All module imports successful")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        return False

def run_app():
    """Run the application"""
    print_header("STARTING APPLICATION")
    
    try:
        print("Launching Logic Analyzer GUI...")
        subprocess.run(
            [sys.executable, "main_enhanced.py"],
            check=False
        )
    except Exception as e:
        print(f"❌ Failed to launch: {e}")
        return False

def create_desktop_shortcut():
    """Create desktop shortcut (Windows)"""
    print_header("CREATE DESKTOP SHORTCUT (OPTIONAL)")
    
    if sys.platform != 'win32':
        print("(Skipped - not on Windows)")
        return True
    
    try:
        from win32.win32com.client import Dispatch
        
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "LogicAnalyzer.lnk"
        
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(str(shortcut_path))
        shortcut.TargetPath = os.path.abspath("main_enhanced.py")
        shortcut.WorkingDirectory = os.getcwd()
        shortcut.IconLocation = "C:\\Windows\\System32\\python.ico"
        shortcut.save()
        
        print(f"✓ Desktop shortcut created: {shortcut_path}")
        return True
    except:
        print("⚠ Could not create desktop shortcut (optional)")
        return True

def build_exe_prompt():
    """Ask user if they want to build EXE"""
    print_header("BUILD EXECUTABLE (OPTIONAL)")
    
    response = input("Do you want to build a standalone .exe? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\nBuilding executable...")
        try:
            subprocess.run(
                [sys.executable, "build_exe.py"],
                check=True
            )
            print("✓ Build completed. Check dist/ folder.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
    
    return True

def main():
    """Main setup flow"""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*15 + "Logic Analyzer - Setup & Test Guide" + " "*19 + "║")
    print("║" + " "*68 + "║")
    print("║" + " "*20 + "Version 1.0 | May 2025" + " "*25 + "║")
    print("╚" + "═"*68 + "╝")
    
    steps = [
        ("Check Python", check_python),
        ("Check Virtual Environment", check_venv),
        ("Check Project Structure", check_project_structure),
        ("Install Dependencies", install_requirements),
        ("Verify Imports", verify_imports),
        ("Test Module Imports", test_imports),
    ]
    
    results = {}
    for step_name, step_func in steps:
        results[step_name] = step_func()
        if not results[step_name] and step_name in ["Check Python", "Check Project Structure"]:
            print(f"\n❌ Setup failed at: {step_name}")
            sys.exit(1)
    
    # Summary
    print_header("SETUP SUMMARY")
    
    all_passed = all(results.values())
    
    for step, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status:8} - {step}")
    
    if all_passed:
        print("\n✓ All checks passed! Setup complete.")
        
        # Menu
        print_header("NEXT STEPS")
        print("""
1. Test with Mock Device (no hardware needed):
   python main_enhanced.py
   - Click "Connect"
   - Check "Use Mock Device"
   - Click "Connect"
   - Click "Start Capture"

2. Connect real Pico hardware:
   - Upload firmware to Pico
   - Connect via USB
   - Click "Connect" and select COM port
   - Click "Start Capture"

3. Build standalone .exe:
   python build_exe.py
   - Creates: dist/LogicAnalyzer.exe
   - Run: dist/LogicAnalyzer.exe

4. For more info:
   - README.md: User guide & features
   - REQUIREMENTS.md: Full spec
   - BUILD_GUIDE.md: Build instructions
        """)
        
        # Offer to run
        response = input("\nStart application now? (y/n): ").strip().lower()
        if response == 'y':
            run_app()
        
        # Offer to build
        build_exe_prompt()
        
        print("\n" + "="*70)
        print("Setup complete! Enjoy Logic Analyzer GUI 🎉")
        print("="*70 + "\n")
    
    else:
        print("\n❌ Setup incomplete. Please fix errors above.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
