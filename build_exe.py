"""
cx_Freeze打包脚本
将PyQt5应用打包为Windows可分发目录
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def remove_path(target_path: Path):
    """删除文件或目录。"""
    if not target_path.exists():
        return
    if target_path.is_dir():
        shutil.rmtree(target_path, ignore_errors=True)
    else:
        target_path.unlink(missing_ok=True)


def prune_distribution(dist_dir: Path):
    """移除分发目录中明显无用的测试和开发资源。"""
    prune_dirs = [
        dist_dir / "lib" / "joblib" / "test",
        dist_dir / "lib" / "nibabel" / "benchmarks",
        dist_dir / "lib" / "PyQt5" / "bindings",
        dist_dir / "lib" / "matplotlib" / "mpl-data" / "sample_data",
        dist_dir / "PyQt5.uic.widget-plugins",
    ]

    for target_dir in prune_dirs:
        remove_path(target_dir)

    prune_globs = [
        "lib/**/*.pyi",
        "lib/**/*.sip",
        "lib/**/*.toml",
        "lib/**/*.pyx",
        "lib/**/*.pyx.tp",
        "lib/**/meson.build",
        "lib/**/pytest*.ini",
        "lib/**/conftest.pyc",
        "lib/**/tests",
        "lib/**/testing",
        "lib/**/__pycache__",
    ]

    for pattern in prune_globs:
        for target_path in dist_dir.glob(pattern):
            remove_path(target_path)


def get_directory_size_mb(target_dir: Path) -> float:
    """返回目录大小，单位 MB。"""
    total_bytes = 0
    for path in target_dir.rglob("*"):
        if path.is_file():
            total_bytes += path.stat().st_size
    return total_bytes / (1024 * 1024)

def build_exe():
    """构建可执行文件"""

    print("="*60)
    print("CEST图像处理GUI工具 - 打包脚本 v3")
    print("="*60)
    print(f"脚本路径: {Path(__file__).resolve()}")

    # 检查cx_Freeze
    try:
        import cx_Freeze
        print(f"[OK] cx_Freeze已安装: {cx_Freeze.__version__}")
    except ImportError:
        print("[INFO] cx_Freeze未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "cx-Freeze"], check=True)

    # 项目目录
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    setup_script = project_dir / "setup_freeze.py"

    print(f"\n项目目录: {project_dir}")

    # 清理旧的构建结果
    if Path("dist").exists():
        print("\n清理旧的构建文件...")
        shutil.rmtree("dist", ignore_errors=True)
    if Path("build").exists():
        shutil.rmtree("build", ignore_errors=True)

    pyinstaller_cmd = [
        sys.executable,
        str(setup_script),
        "build_exe",
        "--build-exe",
        str(project_dir / "dist" / "CESTGui"),
    ]

    print("\n开始打包...")
    print(f"命令: {' '.join(pyinstaller_cmd)}\n")

    # 执行打包
    result = subprocess.run(pyinstaller_cmd, check=False)

    if result.returncode == 0:
        dist_root_dir = project_dir / "dist" / "CESTGui"
        size_before_prune_mb = get_directory_size_mb(dist_root_dir)
        prune_distribution(dist_root_dir)
        size_after_prune_mb = get_directory_size_mb(dist_root_dir)

        bundled_pyqt5_dir = project_dir / "dist" / "CESTGui" / "lib" / "PyQt5"
        required_files = [
            project_dir / "dist" / "CESTGui" / "CESTGui.exe",
            bundled_pyqt5_dir / "__init__.py",
            bundled_pyqt5_dir / "QtCore.pyd",
            bundled_pyqt5_dir / "QtGui.pyd",
            bundled_pyqt5_dir / "QtWidgets.pyd",
            bundled_pyqt5_dir / "Qt5" / "plugins" / "platforms" / "qwindows.dll",
        ]

        missing_files = [path for path in required_files if not path.exists()]
        if missing_files:
            print("\n" + "="*60)
            print("[ERROR] 打包产物缺少PyQt5运行时文件")
            print("="*60)
            for missing_file in missing_files:
                print(f"缺失: {missing_file}")
            return False

        print("\n" + "="*60)
        print("[OK] 打包成功！")
        print("="*60)
        exe_path = project_dir / "dist" / "CESTGui" / "CESTGui.exe"
        print(f"\n可执行文件位置: {exe_path}")
        print(f"打包体积: {size_before_prune_mb:.1f} MB -> {size_after_prune_mb:.1f} MB")
        print("\n使用说明:")
        print("1. 将整个 dist/CESTGui 文件夹发给对方")
        print("2. 对方双击 CESTGui.exe 运行应用")
        print("3. 无需安装Python环境")

        # 创建快捷方式说明
        shortcut_text = """
        ===== 创建桌面快捷方式 =====
        1. 在 dist/CESTGui/CESTGui.exe 上右键
        2. 选择"发送到" -> "桌面(快捷方式)"
        3. 完成！您现在可以从桌面运行应用
        """
        print(shortcut_text)

    else:
        print("\n" + "="*60)
        print("[ERROR] 打包失败")
        print("="*60)
        print("\n故障排除:")
        print("1. 确保所有依赖已安装: python -m pip install -r requirements.txt")
        print("2. 确保Python版本 >= 3.8")
        print("3. 检查是否有权限写入dist目录")
        return False

    return True


def create_installer():
    """创建NSIS安装程序（可选）"""
    print("\n" + "="*60)
    print("是否生成Windows安装程序? (需要NSIS) [y/n]")
    choice = input().lower()

    if choice == 'y':
        try:
            print("\n生成安装程序配置文件...")
            from pathlib import Path

            nsis_content = '''
; NSIS Installation Script for CEST GUI Tool
; Requires NSIS 3.0 or later

!include "MUI2.nsh"

Name "CEST Image Processing GUI"
OutFile "CESTGui_Installer.exe"
InstallDir "$PROGRAMFILES\\CESTGui"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "dist\\CESTGui\\*"
    CreateDirectory "$SMPROGRAMS\\CESTGui"
    CreateShortcut "$SMPROGRAMS\\CESTGui\\CEST GUI.lnk" "$INSTDIR\\CESTGui.exe"
    CreateShortcut "$DESKTOP\\CEST GUI.lnk" "$INSTDIR\\CESTGui.exe"
SectionEnd
            '''

            with open("CESTGui.nsi", "w", encoding="utf-8") as f:
                f.write(nsis_content)

            print("[OK] NSIS配置文件已生成: CESTGui.nsi")
            print("  请使用NSIS编译器生成安装程序")

        except Exception as e:
            print(f"[ERROR] 生成NSIS配置失败: {e}")


if __name__ == "__main__":
    success = build_exe()

    if success and "--installer" in sys.argv:
        create_installer()

    print("\n打包流程完成！\n")
