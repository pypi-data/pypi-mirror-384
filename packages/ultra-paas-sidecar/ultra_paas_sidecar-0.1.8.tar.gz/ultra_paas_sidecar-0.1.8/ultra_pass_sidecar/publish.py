#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Paas Sidecar 智能发布脚本

功能描述:
- 版本管理（自动递增或手动设置）
- 发布环境选择（TestPyPI/正式PyPI）
- 自动化构建和发布
- 一键完成所有操作

@author: lzg
@created: 2025-07-07 16:33:28
@version: 1.0.0
"""

import os
import sys
import subprocess
import shutil
import re
from pathlib import Path


def run_command(cmd, description):
    """运行命令并处理错误"""
    print(f"🔄 {description}...")
    print(f"   执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ {description}失败:")
        print(f"   错误代码: {result.returncode}")
        print(f"   错误输出: {result.stderr}")
        if result.stdout.strip():
            print(f"   标准输出: {result.stdout}")
        return False
    else:
        print(f"✅ {description}成功")
        if result.stdout.strip():
            print(f"   输出: {result.stdout}")
        return True


def clean_build():
    """清理构建文件"""
    print("🧹 清理构建文件...")
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    
    for pattern in dirs_to_clean:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"   删除目录: {path}")
            elif path.is_file():
                path.unlink()
                print(f"   删除文件: {path}")


def get_current_version():
    """获取当前版本号"""
    try:
        with open('setup.py', 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'version="([^"]+)"', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"❌ 读取版本号失败: {e}")
    return None


def increment_version(version, increment_type='patch'):
    """递增版本号"""
    try:
        parts = version.split('.')
        if len(parts) != 3:
            print(f"❌ 版本号格式错误: {version}")
            return None
        
        major, minor, patch = map(int, parts)
        
        if increment_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif increment_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    except Exception as e:
        print(f"❌ 版本号递增失败: {e}")
        return None


def update_version_in_setup(new_version):
    """更新setup.py中的版本号"""
    try:
        with open('setup.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换版本号
        new_content = re.sub(r'version="[^"]+"', f'version="{new_version}"', content)
        
        with open('setup.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 版本号已更新为: {new_version}")
        return True
    except Exception as e:
        print(f"❌ 更新版本号失败: {e}")
        return False


def build_package():
    """构建包"""
    return run_command("python setup.py sdist bdist_wheel", "构建包")


def check_package():
    """检查包"""
    return run_command("twine check dist/*", "检查包")


def run_command_with_env(cmd, description, env):
    """运行命令并处理错误（带环境变量）"""
    print(f"🔄 {description}...")
    print(f"   执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        print(f"❌ {description}失败:")
        print(f"   错误代码: {result.returncode}")
        print(f"   错误输出: {result.stderr}")
        if result.stdout.strip():
            print(f"   标准输出: {result.stdout}")
        return False
    else:
        print(f"✅ {description}成功")
        if result.stdout.strip():
            print(f"   输出: {result.stdout}")
        return True


def upload_to_testpypi():
    """上传到TestPyPI"""
    print("📤 上传到TestPyPI...")

    # TestPyPI token 由用户指定，不要自动覆盖或修改！
    # 如需更换请手动修改此处
    testpypi_token = "pypi-AgENdGVzdC5weXBpLm9yZwIkMGQ4ZWUxOWEtZmQyNi00M2EyLTgwYzAtZDk1NDAwNzc2ZjA5AAIqWzMsImIyYzQyYTAyLWU3NjgtNGY0My04Zjc2LTgxMTRiMjllYzg0NiJdAAAGIEc0LIB4u8XJlVlYSenZsgzqgQWUBYJVirzHxZRvrS_x"
    
    # 创建环境变量
    env = os.environ.copy()
    env['TWINE_USERNAME'] = '__token__'
    env['TWINE_PASSWORD'] = testpypi_token
    
    print("✅ TestPyPI token 已通过环境变量配置（由用户指定，不会被覆盖）")

    # 使用环境变量上传
    result = run_command_with_env("twine upload --repository testpypi dist/*", "上传到TestPyPI", env)
    return result


def upload_to_pypi():
    """上传到PyPI"""
    print("📤 上传到PyPI...")
    
    # 正式 PyPI token 由用户指定，不要自动覆盖或修改！
    # 如需更换请手动修改此处
    pypi_token = "pypi-AgEIcHlwaS5vcmcCJDVlM2Y5MWQxLWY2ZjQtNDc1Mi04NTAzLWYzMmM4YTBmYTk3MgACKlszLCI3NjY1M2U2NS0yODNmLTQ4YTQtOTJkMi1iNWU4OGU5Nzg1NGIiXQAABiAJj7wre-5GpyeR1mlsa16YVoZMDmnaki8IKWmuahSVdQ"
    
    # 创建环境变量
    env = os.environ.copy()
    env['TWINE_USERNAME'] = '__token__'
    env['TWINE_PASSWORD'] = pypi_token
    
    print("✅ 正式PyPI token 已通过环境变量配置（由用户指定，不会被覆盖）")
    print("⚠️  这是正式发布，请确认版本号正确!")
    
    response = input("是否继续上传到正式PyPI? (y/N): ")
    if response.lower() == 'y':
        result = run_command_with_env("twine upload dist/*", "上传到正式PyPI", env)
        return result
    else:
        print("⏭️  跳过正式PyPI上传")
        return True


def smart_publish():
    """智能发布流程"""
    print("🚀 Ultra Paas Sidecar 智能发布工具")
    print("=" * 50)
    
    # 检查必要文件
    required_files = ['setup.py', 'README.md']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            sys.exit(1)
    
    # 获取当前版本号
    current_version = get_current_version()
    if not current_version:
        print("❌ 无法获取当前版本号")
        sys.exit(1)
    
    print(f"📋 当前版本: {current_version}")
    
    # 1. 版本管理
    print("\n📋 版本管理:")
    print("1. 自动递增补丁版本 (+0.0.1)")
    print("2. 自动递增次版本 (+0.1.0)")
    print("3. 自动递增主版本 (+1.0.0)")
    print("4. 手动输入版本号")
    print("5. 保持当前版本")
    
    version_choice = input("请选择版本管理方式 (1-5): ").strip()
    
    new_version = None
    if version_choice == '1':
        new_version = increment_version(current_version, 'patch')
    elif version_choice == '2':
        new_version = increment_version(current_version, 'minor')
    elif version_choice == '3':
        new_version = increment_version(current_version, 'major')
    elif version_choice == '4':
        new_version = input("请输入新版本号 (格式: x.y.z): ").strip()
        if not re.match(r'^\d+\.\d+\.\d+$', new_version):
            print("❌ 版本号格式错误，应为 x.y.z 格式")
            sys.exit(1)
    elif version_choice == '5':
        new_version = current_version
    else:
        print("❌ 无效选择")
        sys.exit(1)
    
    if not new_version:
        print("❌ 版本号生成失败")
        sys.exit(1)
    
    # 更新版本号
    if new_version != current_version:
        if not update_version_in_setup(new_version):
            print("❌ 版本号更新失败")
            sys.exit(1)
    
    # 2. 清理构建文件
    clean_build()
    
    # 3. 构建包
    if not build_package():
        print("❌ 构建失败，退出")
        sys.exit(1)
    
    # 4. 检查包
    if not check_package():
        print("❌ 包检查失败，退出")
        sys.exit(1)
    
    # 5. 选择发布环境
    print(f"\n📋 发布版本 {new_version} 到:")
    print("1. TestPyPI (测试环境)")
    print("2. 正式PyPI (生产环境)")
    print("3. 先TestPyPI后正式PyPI")
    
    env_choice = input("请选择发布环境 (1-3): ").strip()
    
    if env_choice == '1':
        # 仅发布到TestPyPI
        if not upload_to_testpypi():
            print("❌ TestPyPI上传失败")
            sys.exit(1)
        print(f"\n🎉 TestPyPI发布完成! 版本: {new_version}")
        print("📦 包已成功上传到TestPyPI")
        print("🔗 测试安装命令:")
        print(f"pip install --index-url https://test.pypi.org/simple/ ultra-paas-sidecar=={new_version}")
        
    elif env_choice == '2':
        # 仅发布到正式PyPI
        if not upload_to_pypi():
            print("❌ 正式PyPI上传失败")
            sys.exit(1)
        print(f"\n🎉 正式PyPI发布完成! 版本: {new_version}")
        print("📦 包已成功上传到正式PyPI")
        print("🔗 安装命令:")
        print(f"pip install ultra-paas-sidecar=={new_version}")
        
    elif env_choice == '3':
        # 先TestPyPI后正式PyPI
        if not upload_to_testpypi():
            print("❌ TestPyPI上传失败")
            sys.exit(1)
        print("✅ TestPyPI上传成功")
        
        if not upload_to_pypi():
            print("❌ 正式PyPI上传失败")
            sys.exit(1)
        print(f"\n🎉 完整发布完成! 版本: {new_version}")
        print("📦 包已成功上传到TestPyPI和正式PyPI")
        
    else:
        print("❌ 无效选择")
        sys.exit(1)


def manual_publish():
    """手动发布流程（保留原有功能）"""
    print("🚀 Ultra Paas Sidecar 手动发布工具")
    print("=" * 50)
    
    # 检查必要文件
    required_files = ['setup.py', 'README.md', '__init__.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            sys.exit(1)
    
    # 清理
    clean_build()
    
    # 构建
    if not build_package():
        print("❌ 构建失败，退出")
        sys.exit(1)
    
    # 检查
    if not check_package():
        print("❌ 包检查失败，退出")
        sys.exit(1)
    
    # 选择上传目标
    print("\n📋 选择上传目标:")
    print("1. 仅上传到TestPyPI (测试)")
    print("2. 仅上传到PyPI (正式)")
    print("3. 先TestPyPI后PyPI")
    print("4. 仅构建，不上传")
    
    choice = input("请选择 (1-4): ").strip()
    
    if choice == '1':
        upload_to_testpypi()
    elif choice == '2':
        upload_to_pypi()
    elif choice == '3':
        upload_to_testpypi()
        upload_to_pypi()
    elif choice == '4':
        print("✅ 构建完成，未上传")
    else:
        print("❌ 无效选择")
        sys.exit(1)
    
    print("\n🎉 发布流程完成!")


def main():
    """主函数"""
    print("🚀 Ultra Paas Sidecar 智能发布工具")
    print("=" * 50)
    print("1. 智能发布 (推荐) - 版本管理 + 发布")
    print("2. 手动发布 - 传统方式")
    
    choice = input("请选择发布模式 (1-2): ").strip()
    
    if choice == '1':
        smart_publish()
    elif choice == '2':
        manual_publish()
    else:
        print("❌ 无效选择")
        sys.exit(1)


if __name__ == "__main__":
    main() 