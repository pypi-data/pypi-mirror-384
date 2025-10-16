from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.install import install
from setuptools.command.develop import develop
import os


PTH_CODE = """
try:
    from pathlib import Path
    import sys
    import os
    
    CONFIG_NAME = '.pypath'
    current = Path.cwd()
    config_path = None
    
    while True:
        p = current / CONFIG_NAME
        if p.exists() and p.is_file():
            config_path = p
            break
        if current.parent == current:
            break
        current = current.parent
    
    if config_path:
        config_dir = config_path.parent
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if not line:
                    continue
                if os.path.isabs(line):
                    path = Path(line)
                else:
                    path = (config_dir / line).resolve()
                if path.exists():
                    path_str = str(path)
                    if path_str not in sys.path:
                        sys.path.insert(0, path_str)
except:
    pass
"""

# 將程式碼轉換成單行 - 使用 repr()
PTH_CONTENT = f"import sys; exec({repr(PTH_CODE)})\n"


class BuildPyWithPthFile(build_py):
    """將 .pth 檔案包含到 wheel 中"""

    def run(self):
        super().run()

        pth_filename = "path_loader_auto.pth"

        # 在專案根目錄建立 .pth 檔案
        source_pth = os.path.join(os.path.dirname(__file__), pth_filename)
        with open(source_pth, "w", encoding="utf-8") as f:
            f.write(PTH_CONTENT)

        # 複製到 build 目錄
        destination = os.path.join(self.build_lib, pth_filename)
        self.copy_file(source_pth, destination, preserve_mode=0)

        print(f"✓ .pth 檔案已加入 wheel: {pth_filename}")


def create_pth_file():
    """為從原始碼安裝建立 .pth 檔案"""
    try:
        from sysconfig import get_path

        site_packages = get_path("purelib")
    except ImportError:
        from distutils.sysconfig import get_python_lib

        site_packages = get_python_lib()

    pth_file = os.path.join(site_packages, "path_loader_auto.pth")

    try:
        with open(pth_file, "w", encoding="utf-8") as f:
            f.write(PTH_CONTENT)
        print(f"\n✓ 成功建立 .pth 檔案: {pth_file}")
        print(f"   Python 啟動時會自動搜尋並載入 .pypath 配置檔")
        return True
    except Exception as e:
        print(f"\n✗ 警告: 無法建立 .pth 檔案: {e}")
        return False


class PostInstallCommand(install):
    """pip install . 或 pip install *.tar.gz 時執行"""

    def run(self):
        install.run(self)
        print("\n" + "=" * 60)
        print("正在初始化 path-loader...")
        print("=" * 60)
        create_pth_file()


class PostDevelopCommand(develop):
    """pip install -e . 時執行"""

    def run(self):
        develop.run(self)
        print("\n" + "=" * 60)
        print("正在初始化 path-loader...")
        print("=" * 60)
        create_pth_file()


setup(
    cmdclass={
        "build_py": BuildPyWithPthFile,
        "install": PostInstallCommand,
        "develop": PostDevelopCommand,
    },
)
