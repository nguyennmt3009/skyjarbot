# SkyjarBot — Hướng dẫn sử dụng

> Desktop automation & blackbox UI testing tool cho Windows

---

## Mục lục

1. [Cài đặt](#1-cài-đặt)
2. [Khởi động](#2-khởi-động)
3. [Giao diện chính](#3-giao-diện-chính)
4. [Ghi lại thao tác (Record)](#4-ghi-lại-thao-tác-record)
5. [Phát lại (Playback)](#5-phát-lại-playback)
6. [Thêm step thủ công](#6-thêm-step-thủ-công)
7. [Quản lý danh sách steps](#7-quản-lý-danh-sách-steps)
8. [Lưu và tải scenario](#8-lưu-và-tải-scenario)
9. [Điều kiện màu pixel (Pixel Color)](#9-điều-kiện-màu-pixel-pixel-color)
10. [Nhận diện hình ảnh (Image Match)](#10-nhận-diện-hình-ảnh-image-match)
11. [Đọc văn bản màn hình (OCR Text)](#11-đọc-văn-bản-màn-hình-ocr-text)
12. [Biến (Variables)](#12-biến-variables)
13. [Rẽ nhánh (Branch)](#13-rẽ-nhánh-branch)
14. [Gọi scenario con (Call Scenario)](#14-gọi-scenario-con-call-scenario)
15. [Chạy song song (Parallel Runner)](#15-chạy-song-song-parallel-runner)
16. [Lịch sử & báo cáo (History)](#16-lịch-sử--báo-cáo-history)
17. [Cấu trúc file JSON scenario](#17-cấu-trúc-file-json-scenario)
18. [Câu hỏi thường gặp](#18-câu-hỏi-thường-gặp)

---

## 1. Cài đặt

### Yêu cầu

- Windows 10 / Windows 11
- Python 3.11 trở lên

### Cài dependencies

```bash
py -m pip install pynput Pillow opencv-python pytesseract numpy
```

### Cài Tesseract OCR (chỉ cần nếu dùng tính năng OCR)

1. Tải installer tại: https://github.com/UB-Mannheim/tesseract/wiki
2. Cài đặt bình thường, ghi nhớ đường dẫn cài (mặc định `C:\Program Files\Tesseract-OCR`)
3. Thêm vào PATH hoặc cấu hình trong code:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

## 2. Khởi động

Chạy từ thư mục gốc của project:

```bash
py run.py
```

---

## 3. Giao diện chính

```
┌──────────────────────────────────────────────────────────────────┐
│  ⏺ Record  ▶ Play  💾 Save  📂 Load  🗑 Clear  ➕ Add Step  📊 History  ⚡ Parallel │
├──────────────────────────────────────────────────────────────────┤
│ Status: Idle                                                     │
├───────────────────────────────┬──────────────────────────────────┤
│  Recorded Steps               │  Log                             │
│  [000] click (500, 300) [left]│  10:01:23 [INFO] Recording...    │
│  [001] delay 500 ms           │  10:01:25 [INFO] Step 000 done   │
│  [002] key_press [Key.enter]  │  ...                             │
└───────────────────────────────┴──────────────────────────────────┘
```

| Nút | Chức năng |
|-----|-----------|
| ⏺ Record | Bắt đầu / dừng ghi thao tác |
| ▶ Play | Bắt đầu / dừng phát lại |
| 💾 Save | Lưu scenario ra file JSON |
| 📂 Load | Tải scenario từ file JSON |
| 🗑 Clear | Xóa toàn bộ steps hiện tại |
| ➕ Add Step | Thêm step thủ công |
| 📊 History | Xem lịch sử chạy & xuất báo cáo |
| ⚡ Parallel | Chạy nhiều scenario song song |

---

## 4. Ghi lại thao tác (Record)

1. Nhấn **⏺ Record**
2. Thực hiện các thao tác trên màn hình: click chuột, gõ phím
3. Nhấn **⏹ Stop** để dừng ghi

> **Lưu ý:** Trong quá trình recording, khoảng nghỉ giữa các thao tác > 50ms sẽ tự động được ghi thành `DelayStep` để đảm bảo timing khi phát lại.

Các thao tác được ghi lại:

| Thao tác | Ghi chú |
|----------|---------|
| Click chuột trái | `click (x, y) [left]` |
| Click chuột phải | `click (x, y) [right]` |
| Cuộn chuột | `scroll (x, y) dx=0 dy=-3` |
| Nhấn phím | `key_press [Key.enter]` |
| Khoảng nghỉ | `delay 500 ms` |

---

## 5. Phát lại (Playback)

1. Sau khi record hoặc load scenario, nhấn **▶ Play**
2. Bot sẽ thực hiện lại toàn bộ các steps theo thứ tự
3. Step đang chạy được highlight trong danh sách
4. Nhấn **⏹ Stop** để dừng giữa chừng

> **Lưu ý:** Không di chuyển chuột hoặc thao tác trong lúc phát lại vì bot dùng chuột/bàn phím của hệ thống.

---

## 6. Thêm step thủ công

Nhấn **➕ Add Step** để mở dialog. Chọn loại step:

### Action — thực hiện thao tác

| Action type | Các trường cần điền |
|-------------|---------------------|
| `click` | X, Y, Button (left/right) |
| `mouse_move` | X, Y |
| `mouse_scroll` | X, Y, dx, dy |
| `key_press` | Key (ví dụ: `Key.enter`, `a`, `Key.ctrl_l`) |
| `type_text` | Text (hỗ trợ `{variable}`) |

### Condition — chờ điều kiện

| Condition type | Mô tả |
|----------------|-------|
| `pixel_color` | Chờ pixel tại (X,Y) có màu mong muốn |
| `image_match` | Chờ ảnh template xuất hiện trên màn hình |
| `ocr_text` | Chờ văn bản xuất hiện trên màn hình |

### Delay — chờ thời gian

Nhập số milliseconds cần chờ.

### Branch — rẽ nhánh

Xem [mục 13](#13-rẽ-nhánh-branch).

### Set Variable — đặt biến

Xem [mục 12](#12-biến-variables).

### Call Scenario — gọi scenario con

Xem [mục 14](#14-gọi-scenario-con-call-scenario).

---

## 7. Quản lý danh sách steps

**Right-click** vào bất kỳ step nào trong danh sách để:

| Menu | Chức năng |
|------|-----------|
| Delete step | Xóa step đã chọn |
| Move up | Đẩy step lên trên |
| Move down | Đẩy step xuống dưới |

---

## 8. Lưu và tải scenario

### Lưu

1. Nhấn **💾 Save**
2. Chọn vị trí lưu (mặc định vào thư mục `app/data/scenarios/`)
3. Đặt tên file `.json`

### Tải

1. Nhấn **📂 Load**
2. Chọn file `.json`
3. Danh sách steps sẽ được nạp vào giao diện

---

## 9. Điều kiện màu pixel (Pixel Color)

Chờ cho đến khi màu pixel tại tọa độ (X, Y) khớp với màu mong muốn.

**Cách thêm:**
1. Nhấn **➕ Add Step** → chọn **Condition** → `pixel_color`
2. Điền X, Y và màu R, G, B
3. Hoặc nhấn **"Sample pixel from screen"**:
   - Dialog tự thu nhỏ
   - Di chuột đến vị trí cần lấy màu trong 3 giây
   - Bot tự điền X, Y và màu tương ứng

| Trường | Mô tả | Mặc định |
|--------|-------|----------|
| X, Y | Tọa độ pixel trên màn hình | — |
| R, G, B | Màu mong muốn (0–255) | 0, 0, 0 |
| Tolerance | Sai số cho phép mỗi kênh màu | 10 |
| Timeout (ms) | Thời gian chờ tối đa | 5000 |
| Poll interval (ms) | Tần suất kiểm tra | 200 |

---

## 10. Nhận diện hình ảnh (Image Match)

Chờ cho đến khi một ảnh template xuất hiện trên màn hình.

**Cách chuẩn bị ảnh template:**
1. Chụp màn hình vùng cần nhận diện (dùng Snipping Tool hoặc tương tự)
2. Lưu thành file `.png`

**Cách thêm:**
1. Nhấn **➕ Add Step** → **Condition** → `image_match`
2. Nhấn **Browse…** chọn file ảnh template
3. Cấu hình các tham số:

| Trường | Mô tả | Mặc định |
|--------|-------|----------|
| Template path | Đường dẫn đến file ảnh | — |
| Match threshold | Độ tương đồng tối thiểu (0.0–1.0) | 0.8 |
| Search region | Vùng tìm kiếm `x,y,w,h` (bỏ trống = toàn màn hình) | trống |
| Timeout (ms) | Thời gian chờ tối đa | 5000 |

> **Tip:** Nếu bot hay bị false negative, hạ `threshold` xuống 0.7. Nếu hay bị false positive, tăng lên 0.9.

---

## 11. Đọc văn bản màn hình (OCR Text)

Chờ cho đến khi một đoạn văn bản xuất hiện trên màn hình.

**Yêu cầu:** Tesseract OCR đã được cài đặt (xem [mục 1](#1-cài-đặt)).

**Cách thêm:**
1. Nhấn **➕ Add Step** → **Condition** → `ocr_text`
2. Điền văn bản cần chờ
3. Cấu hình:

| Trường | Mô tả | Mặc định |
|--------|-------|----------|
| Expected text | Văn bản cần tìm | — |
| Substring match | Tích = chứa chuỗi con, bỏ tích = khớp toàn bộ | Tích |
| OCR region | Vùng đọc `x,y,w,h` (bỏ trống = toàn màn hình) | trống |
| Timeout (ms) | Thời gian chờ tối đa | 5000 |

> **Tip:** Giới hạn `ocr_region` về vùng nhỏ để tăng tốc độ và độ chính xác.

---

## 12. Biến (Variables)

Biến cho phép lưu giá trị trong quá trình chạy và tái sử dụng trong các step sau.

### Đặt biến

1. Nhấn **➕ Add Step** → **Set Variable**
2. Nhập tên biến và giá trị

Ví dụ:

| Name | Value |
|------|-------|
| `username` | `admin` |
| `retry` | `3` |

### Dùng biến

Trong các `ActionStep` (type_text, key_press), dùng cú pháp `{tên_biến}`:

```
type_text: "Xin chào {username}"
→ kết quả thực thi: "Xin chào admin"
```

Giá trị của biến cũng có thể tham chiếu biến khác:

```
set count = "{count}"   ← giữ nguyên nếu count chưa tồn tại
set greeting = "Hello {username}!"
```

---

## 13. Rẽ nhánh (Branch)

Thực hiện một nhóm steps khác nhau tùy theo điều kiện.

```
Branch:
  condition: pixel(500,300) == (255,0,0)
  ├─ on_true:  [click (600,400), type "yes"]
  └─ on_false: [click (700,400), type "no"]
```

**Cách tạo qua UI:**
1. Nhấn **➕ Add Step** → **Branch**
2. Cấu hình condition (hiện hỗ trợ pixel_color)
3. Step được thêm với `on_true` và `on_false` rỗng

**Thêm sub-steps vào on_true / on_false:**

Chỉnh trực tiếp trong file JSON:

```json
{
  "type": "branch",
  "condition": {
    "type": "pixel_color",
    "x": 500, "y": 300,
    "color": [255, 0, 0],
    "tolerance": 10,
    "timeout_ms": 3000,
    "poll_interval_ms": 200
  },
  "on_true": [
    { "type": "click", "x": 600, "y": 400, "button": "left" }
  ],
  "on_false": [
    { "type": "click", "x": 700, "y": 400, "button": "left" }
  ]
}
```

> **Lưu ý:** Nếu condition timeout → tự động chạy nhánh `on_false` (không báo lỗi).

---

## 14. Gọi scenario con (Call Scenario)

Cho phép tái sử dụng một scenario khác như một "hàm".

**Ví dụ:** Scenario `login.json` → gọi từ nhiều scenario khác nhau.

**Cách thêm:**
1. Nhấn **➕ Add Step** → **Call Scenario**
2. Nhấn **Browse…** chọn file `.json`

Khi chạy đến step này, bot sẽ load và chạy toàn bộ scenario đó inline, sau đó tiếp tục scenario gốc.

> **Lưu ý:** Biến từ scenario cha được truyền xuống scenario con, nên có thể dùng `{variable}` trong sub-scenario.

---

## 15. Chạy song song (Parallel Runner)

Chạy nhiều scenario cùng lúc — hữu ích cho testing nhiều luồng.

**Cách dùng:**
1. Nhấn **⚡ Parallel**
2. Nhấn **Add scenario…** → chọn một hoặc nhiều file `.json`
3. Nhấn **▶ Run all**
4. Theo dõi trạng thái từng scenario theo màu:

| Màu | Trạng thái |
|-----|-----------|
| Xám | Pending — chưa chạy |
| Xanh dương | Running — đang chạy |
| Xanh lá | Passed — hoàn thành thành công |
| Đỏ | Failed — thất bại hoặc timeout |

5. Nhấn **⏹ Stop all** để dừng tất cả

> **Lưu ý:** Mỗi scenario chạy trong thread riêng, dùng chung chuột/bàn phím hệ thống nên các scenario có thao tác input có thể xung đột nhau. Phù hợp nhất khi các scenario chỉ đọc màn hình (pixel, OCR, image match) hoặc chạy trên các vùng màn hình khác nhau.

---

## 16. Lịch sử & báo cáo (History)

### Xem lịch sử

Nhấn **📊 History** để mở cửa sổ lịch sử:

- Danh sách tất cả lần chạy (scenario, thời gian, thời lượng, số steps, kết quả)
- Nhấn vào một dòng → xem thống kê của scenario đó ở phần dưới:
  - Tổng lần chạy
  - Số lần pass / fail
  - Tỷ lệ thành công (%)
  - Thời lượng trung bình

### Xuất báo cáo HTML

| Nút | Mô tả |
|-----|-------|
| Report: all | Xuất báo cáo tất cả scenarios |
| Report: selected scenario | Xuất báo cáo riêng cho scenario đang chọn |

File HTML được lưu vào thư mục `reports/` và tự động mở trên trình duyệt.

### Xóa lịch sử

Chọn một dòng → nhấn **Delete selected** → xác nhận.

---

## 17. Cấu trúc file JSON scenario

File scenario lưu ở `app/data/scenarios/*.json`. Có thể chỉnh tay bằng text editor.

### Ví dụ đầy đủ

```json
{
  "id": "abc123",
  "name": "login_test",
  "description": "Test đăng nhập",
  "version": 1,
  "steps": [
    {
      "type": "set_variable",
      "name": "username",
      "value": "admin"
    },
    {
      "type": "click",
      "x": 500,
      "y": 300,
      "button": "left"
    },
    {
      "type": "type_text",
      "text": "{username}"
    },
    {
      "type": "key_press",
      "key": "Key.enter"
    },
    {
      "type": "pixel_color",
      "x": 200,
      "y": 150,
      "color": [0, 200, 0],
      "tolerance": 15,
      "timeout_ms": 5000,
      "poll_interval_ms": 200
    },
    {
      "type": "image_match",
      "template_path": "C:/templates/dashboard.png",
      "match_threshold": 0.85,
      "search_region": null,
      "timeout_ms": 8000,
      "poll_interval_ms": 500
    },
    {
      "type": "ocr_text",
      "expected_text": "Đăng nhập thành công",
      "ocr_contains": true,
      "ocr_region": [0, 0, 800, 100],
      "timeout_ms": 5000,
      "poll_interval_ms": 300
    },
    {
      "type": "delay",
      "duration_ms": 1000
    },
    {
      "type": "branch",
      "condition": {
        "type": "pixel_color",
        "x": 100, "y": 100,
        "color": [255, 0, 0],
        "tolerance": 10,
        "timeout_ms": 2000,
        "poll_interval_ms": 200
      },
      "on_true": [
        { "type": "click", "x": 400, "y": 500, "button": "left" }
      ],
      "on_false": []
    },
    {
      "type": "call_scenario",
      "scenario_path": "app/data/scenarios/logout.json"
    }
  ]
}
```

### Tất cả loại step

| type | Trường bắt buộc | Trường tuỳ chọn |
|------|-----------------|-----------------|
| `click` | `x`, `y` | `button` (left/right/middle) |
| `mouse_move` | `x`, `y` | — |
| `mouse_scroll` | `x`, `y`, `dx`, `dy` | — |
| `key_press` | `key` | — |
| `type_text` | `text` | — |
| `delay` | `duration_ms` | — |
| `pixel_color` | `x`, `y`, `color` | `tolerance`, `timeout_ms`, `poll_interval_ms` |
| `image_match` | `template_path` | `match_threshold`, `search_region`, `timeout_ms` |
| `ocr_text` | `expected_text` | `ocr_contains`, `ocr_region`, `timeout_ms` |
| `branch` | `condition` | `on_true`, `on_false` |
| `set_variable` | `name`, `value` | — |
| `call_scenario` | `scenario_path` | — |

---

## 18. Câu hỏi thường gặp

**Q: Bot click sai vị trí so với lúc record?**
A: Có thể do DPI scaling. Vào Settings → Display → Scale và đặt về 100%, hoặc chỉnh tọa độ thủ công trong file JSON.

**Q: Condition timeout liên tục dù màn hình đúng?**
A: Tăng `tolerance` cho pixel_color, hoặc hạ `match_threshold` cho image_match. Kiểm tra lại tọa độ bằng nút "Sample pixel from screen".

**Q: OCR không nhận diện được chữ?**
A: Giới hạn `ocr_region` về vùng nhỏ hơn. Đảm bảo Tesseract đã cài đúng và thêm vào PATH.

**Q: Lưu scenario ở đâu?**
A: Mặc định trong `app/data/scenarios/`. Có thể lưu bất kỳ đâu khi dùng hộp thoại Save.

**Q: Chạy `py run.py` báo lỗi import?**
A: Chạy từ đúng thư mục gốc (chứa file `run.py`). Kiểm tra đã cài đủ dependencies chưa bằng `py -m pip install -r requirements.txt`.

**Q: Muốn thêm sub-steps vào Branch qua UI?**
A: Hiện tại sub-steps của Branch chỉ chỉnh được qua JSON. Mở file `.json` bằng text editor và thêm vào `on_true`/`on_false`.

---

*SkyjarBot v1.0 — Built with Python + Tkinter + pynput + Pillow + OpenCV + pytesseract*
