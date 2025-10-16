"""
Path Loader 核心功能模組

負責搜尋、解析 .pypath 配置檔並載入路徑到 sys.path
"""

import sys
import os
from pathlib import Path
from typing import Optional, List


# 預設配置檔名稱 (只用於手動呼叫時的預設值)
# 自動載入(.pth)只會搜尋 .pypath
CONFIG_NAMES = [".pypath"]


def find_pypath_file(
    start_dir: Optional[str] = None, config_names: Optional[List[str]] = None
) -> Optional[Path]:
    """
    從指定目錄開始向上搜尋配置檔

    會依序搜尋指定的檔案名稱,找到第一個就回傳。

    Args:
        start_dir: 起始搜尋目錄,若為 None 則從當前工作目錄開始
        config_names: 要搜尋的檔名列表,若為 None 則只搜尋 '.pypath'

    Returns:
        找到的配置檔路徑,若找不到則回傳 None

    Examples:
        >>> # 使用預設檔名 (.pypath)
        >>> config = find_pypath_file()
        >>> if config:
        ...     print(f"找到配置檔: {config}")

        >>> # 搜尋自訂檔名
        >>> config = find_pypath_file(config_names=['my_paths.conf'])

        >>> # 從特定目錄開始搜尋
        >>> config = find_pypath_file(start_dir='/project/root')

        >>> # 搜尋多個檔名
        >>> config = find_pypath_file(config_names=['dev.conf', '.pypath', 'prod.conf'])
    """
    if config_names is None:
        config_names = CONFIG_NAMES

    if start_dir is None:
        start_dir = Path.cwd()
    else:
        start_dir = Path(start_dir)

    current = start_dir.resolve()

    # 向上搜尋直到根目錄
    while True:
        for config_name in config_names:
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

    Examples:
        >>> config = find_pypath_file()
        >>> if config:
        ...     paths = parse_pypath_file(config)
        ...     print(f"找到 {len(paths)} 個路徑")
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


def load_paths(
    start_dir: Optional[str] = None,
    config_names: Optional[List[str]] = None,
) -> int:
    """
    搜尋並載入配置檔中的路徑到 sys.path

    Args:
        start_dir: 起始搜尋目錄,若為 None 則從當前工作目錄開始
        config_names: 自訂要搜尋的配置檔名稱列表,若為 None 則只搜尋 '.pypath'

    Returns:
        成功載入的路徑數量

    Examples:
        >>> # 基本使用 (只搜尋 .pypath)
        >>> count = load_paths()
        >>> print(f"載入了 {count} 個路徑")

        >>> # 搜尋自訂配置檔名
        >>> load_paths(config_names=['my_paths.conf'])

        >>> # 搜尋多個配置檔 (找到第一個就停止)
        >>> load_paths(config_names=['dev.conf', '.pypath', 'prod.conf'])

        >>> # 從特定目錄搜尋
        >>> load_paths(start_dir='/project/root')

        >>> # 組合使用
        >>> load_paths(
        ...     start_dir='/my/project',
        ...     config_names=['dev_paths.txt', '.pypath']
        ... )
    """
    config_path = find_pypath_file(start_dir, config_names)

    if not config_path:
        return 0

    paths = parse_pypath_file(config_path)
    loaded_count = 0

    for path in paths:
        if path not in sys.path:
            sys.path.insert(1, path)
            loaded_count += 1

    return loaded_count
