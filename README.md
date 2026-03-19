# skyjarbot


## Chạy trực tiếp (không cần build):

**Yêu cầu:** Python 3.10+

1. Cài dependencies:
```
py -m pip install -r requirements.txt
```

> Nếu dùng `pytesseract`, cần cài thêm [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) và thêm vào PATH.

2. Chạy app:
```
py run.py
```


## Build exe (tuỳ chọn — để phân phối cho người không có Python):


```
py -m PyInstaller --onefile --windowed --name SkyjarBot --icon app/images/logo.ico run.py
```

| Flag | Ý nghĩa |
|------|---------|
| `--onefile` | Đóng gói thành 1 file .exe duy nhất |
| `--windowed` | Không hiện cửa sổ console đen khi chạy |
| `--name SkyjarBot` | Đặt tên file output |
| `--icon app/images/logo.ico` | Icon cho file .exe |
