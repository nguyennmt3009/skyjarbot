# skyjarbot


## Build exe:


```
py -m PyInstaller --onefile --windowed --name SkyjarBot --icon app/images/logo.ico run.py
```

| Flag | Ý nghĩa |
|------|---------|
| `--onefile` | Đóng gói thành 1 file .exe duy nhất |
| `--windowed` | Không hiện cửa sổ console đen khi chạy |
| `--name SkyjarBot` | Đặt tên file output |
| `--icon app/images/logo.ico` | Icon cho file .exe |
