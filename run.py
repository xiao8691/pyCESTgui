#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CEST GUI 工具 - 快速操作脚本
用于快速启动应用或生成.exe可执行文件
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header():
    """打印标题"""
    print("\n" + "="*70)
    print(" "*15 + "CEST 图像处理 GUI 工具")
    print(" "*20 + "快速操作脚本 v1.0")
    print("="*70 + "\n")


def check_dependencies():
    """检查依赖"""
    print("检查环境...")
    
    try:
        import PyQt5
        import nibabel
        import matplotlib
        import numpy
        import scipy
        import sklearn
        print("✓ 所有依赖已安装\n")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("\n建议运行: pip install -r requirements.txt\n")
        return False


def run_gui():
    """运行GUI应用"""
    print("启动CEST GUI应用...\n")
    try:
        subprocess.run([sys.executable, "main.py"], check=False)
    except Exception as e:
        print(f"✗ 启动失败: {e}")
        sys.exit(1)


def build_exe():
    """构建.exe文件"""
    print("准备构建.exe文件...\n")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller已安装: {PyInstaller.__version__}\n")
    except ImportError:
        print("✗ PyInstaller未安装，正在安装...\n")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                      check=False)
    
    # 运行打包脚本
    print("执行打包...\n")
    try:
        subprocess.run([sys.executable, "build_exe.py"], check=False)
    except Exception as e:
        print(f"✗ 打包失败: {e}")
        sys.exit(1)


def generate_example_data():
    """生成示例数据"""
    print("生成示例数据...\n")
    
    try:
        if Path("example_data").exists():
            response = input("示例数据已存在，是否重新生成? (y/n): ").lower()
            if response != 'y':
                print("已跳过\n")
                return
        
        subprocess.run([sys.executable, "generate_example_data.py"], check=False)
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        sys.exit(1)


def run_tests():
    """运行测试"""
    print("运行完整流程测试...\n")
    
    try:
        subprocess.run([sys.executable, "test_full_pipeline.py"], check=False)
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        sys.exit(1)


def show_menu():
    """显示菜单"""
    print("\n请选择操作 (Choose an operation):")
    print("-" * 70)
    print("  1  运行GUI应用 (Run GUI application)")
    print("  2  生成示例数据 (Generate example data)")
    print("  3  运行完整测试 (Run full pipeline test)")
    print("  4  构建.exe文件 (Build .exe executable)")
    print("  5  安装更新依赖 (Install/Update dependencies)")
    print("  6  查看文档 (View documentation)")
    print("  0  退出 (Exit)")
    print("-" * 70 + "\n")


def view_documentation():
    """查看文档"""
    print("\n可用文档:")
    print("  • README.md - 完整功能说明")
    print("  • QUICK_START.md - 快速开始指南")
    print("  • PROJECT_SUMMARY.md - 项目完成总结")
    print("  • example_data/README.txt - 示例数据说明\n")
    
    response = input("请选择要查看的文档 (1-4) 或按Enter返回: ").lower()
    
    doc_map = {
        '1': 'README.md',
        '2': 'QUICK_START.md',
        '3': 'PROJECT_SUMMARY.md',
        '4': 'example_data/README.txt'
    }
    
    if response in doc_map:
        doc_path = Path(doc_map[response])
        if doc_path.exists():
            # 尝试用默认应用打开
            try:
                import webbrowser
                if response == '3':
                    # Markdown文件用记事本打开
                    os.startfile(str(doc_path))
                else:
                    os.startfile(str(doc_path))
            except:
                # 备选：打印到终端
                with open(doc_path, 'r', encoding='utf-8') as f:
                    print("\n" + f.read() + "\n")
        else:
            print(f"\n✗ 文件未找到: {doc_path}\n")


def main():
    """主函数"""
    print_header()
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("✗ 需要Python 3.8或更高版本")
        print(f"  当前版本: {sys.version}\n")
        sys.exit(1)
    
    # 检查工作目录
    if not Path("main.py").exists():
        print("✗ 错误: 请在项目根目录运行此脚本\n")
        sys.exit(1)
    
    # 主循环
    while True:
        show_menu()
        choice = input("请输入选择 (Enter choice): ").strip()
        
        if choice == '1':
            # 检查依赖后运行GUI
            if check_dependencies():
                run_gui()
            else:
                response = input("是否现在安装依赖? (y/n): ").lower()
                if response == 'y':
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", 
                                  "requirements.txt"], check=False)
                    run_gui()
        
        elif choice == '2':
            generate_example_data()
        
        elif choice == '3':
            if not Path("example_data").exists():
                print("✗ 示例数据不存在，请先生成\n")
                response = input("是否现在生成? (y/n): ").lower()
                if response == 'y':
                    generate_example_data()
            else:
                run_tests()
        
        elif choice == '4':
            if check_dependencies():
                build_exe()
            else:
                response = input("是否现在安装依赖? (y/n): ").lower()
                if response == 'y':
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", 
                                  "requirements.txt"], check=False)
                    build_exe()
        
        elif choice == '5':
            print("安装依赖...\n")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", 
                          "requirements.txt", "-U"], check=False)
            print()
        
        elif choice == '6':
            view_documentation()
        
        elif choice == '0':
            print("\n感谢使用! (Thank you for using!)\n")
            sys.exit(0)
        
        else:
            print("✗ 无效选择，请重试\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已中止 (Program terminated)\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 发生错误: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
