"""
自動載入模組

這個模組會被 .pth 檔案自動執行,在 Python 啟動時載入路徑。
不建議直接 import 這個模組。
"""

# 在模組載入時自動執行
try:
    from .loader import load_paths

    load_paths(prepend=True)

except Exception:
    # 如果發生任何錯誤,靜默忽略以免影響 Python 啟動
    pass
