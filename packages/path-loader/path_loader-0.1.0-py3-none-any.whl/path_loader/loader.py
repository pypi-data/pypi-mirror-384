"""
Path Loader 核心功能模組

負責搜尋、解析 .pypath 配置檔並載入路徑到 sys.path
"""

import sys
import os
from pathlib import Path
from typing import Optional, List


# 支援的配置檔名稱(優先順序由高到低)
CONFIG_NAMES = [".pypath", "pythonpath.txt", "sys_paths.conf"]


def find_pypath_file(start_dir: Optional[str] = None) -> Optional[Path]:
    """
    從指定目錄開始向上搜尋配置檔

    會依序搜尋以下檔案名稱:
    - .pypath (推薦)
    - pythonpath.txt
    - sys_paths.conf

    Args:
        start_dir: 起始搜尋目錄,若為 None 則從當前工作目錄開始

    Returns:
        找到的配置檔路徑,若找不到則回傳 None

    Examples:
        >>> config = find_pypath_file()
        >>> if config:
        ...     print(f"找到配置檔: {config}")
    """
    if start_dir is None:
        start_dir = Path.cwd()
    else:
        start_dir = Path(start_dir)

    current = start_dir.resolve()

    # 向上搜尋直到根目錄
    while True:
        for config_name in CONFIG_NAMES:
            config_path = current / config_name
            if config_path.exists() and config_path.is_file():
                return config_path

        # 已到達根目錄
        if current.parent == current:
            break
        current = current.parent

    return None


def parse_pypath_file(config_path: Path) -> List[str]:
    """
    解析配置檔內容

    支援的格式:
    - 每行一個路徑
    - 支援 # 開頭的註解
    - 支援相對路徑(相對於配置檔所在目錄)
    - 支援絕對路徑
    - 自動忽略空白行

    Args:
        config_path: 配置檔路徑

    Returns:
        解析出的有效路徑列表
    """
    paths = []
    config_dir = config_path.parent

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                # 移除註解和前後空白
                line = line.split("#")[0].strip()

                if not line:
                    continue

                # 處理相對路徑和絕對路徑
                if os.path.isabs(line):
                    path = Path(line)
                else:
                    # 相對於配置檔所在目錄
                    path = (config_dir / line).resolve()

                # 檢查路徑是否存在
                if path.exists():
                    paths.append(str(path))

    except Exception:
        pass

    return paths


def load_paths(start_dir: Optional[str] = None, prepend: bool = False) -> int:
    """
    搜尋並載入配置檔中的路徑到 sys.path

    Args:
        start_dir: 起始搜尋目錄,若為 None 則從當前工作目錄開始
        prepend: False(預設)=使用 append, True=使用 insert(0)

    Returns:
        成功載入的路徑數量
    """
    config_path = find_pypath_file(start_dir)

    if not config_path:
        return 0

    paths = parse_pypath_file(config_path)
    loaded_count = 0

    for path in paths:
        if path not in sys.path:
            if prepend:
                sys.path.insert(0, path)
            else:
                sys.path.append(path)
            loaded_count += 1

    return loaded_count
