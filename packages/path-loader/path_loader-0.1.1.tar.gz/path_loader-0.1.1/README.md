# Path Loader

自動從配置檔載入 Python 路徑到 `sys.path`。

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 安裝

```bash
pip install path-loader
```

## 快速開始

### 1. 建立配置檔

在專案根目錄建立 `.pypath`:

```
# .pypath
src
lib
```

### 2. 使用

Python 啟動時會自動載入:

```python
# 直接 import 你的模組
import my_module
```

## 配置檔格式

```
# 支援註解

# 相對路徑 (相對於 .pypath 所在目錄)
src
lib/modules

# 絕對路徑
/usr/local/custom_lib
C:\Projects\Common

# 空白行會被忽略
```

## 手動控制

```python
import path_loader

# 基本使用
path_loader.load_paths()

# 自訂配置檔名
path_loader.load_paths(config_names=['my_config.txt'])

# 從特定目錄開始搜尋
path_loader.load_paths(start_dir='/project/root')

# 只搜尋不載入
config = path_loader.find_pypath_file()
if config:
    paths = path_loader.parse_pypath_file(config)
    print(paths)
```

## 範例

### 專案結構

```
my_project/
├── .pypath          # 內容: src\nlib
├── src/
│   └── utils.py
├── lib/
│   └── helper.py
└── main.py
```

### 使用

```python
# main.py
# 不需要任何額外程式碼,直接 import
from utils import my_function
from helper import HelperClass
```
