# HƯỚNG DẪN HOÀN THIỆN FLIGHT × WEATHER VÀ DEPLOY DASHBOARD
**Flight DW 2025 · AERO INSIGHTS · bộ công cụ `FW_COMPLETION_KIT` (phiên bản fw-export-1.0.0, 18/11/2026)**

Làm lần lượt từ Bước 0 đến Bước 11. Mỗi bước có mục **Kết quả mong đợi** và **Dừng lại nếu**. Nếu gặp điều kiện dừng, đừng làm tiếp: hãy gửi file báo cáo của bước đó cho Claude.

> **Nguyên tắc an toàn trong toàn bộ quy trình**
> - Mọi công cụ chỉ chạy `SELECT`/`EXPLAIN`. Mỗi kết nối được tool đặt `SET SESSION TRANSACTION READ ONLY`, nên MySQL sẽ từ chối mọi lệnh ghi (đã kiểm thử: lỗi 1792).
> - Không chạy lại ETL; không đụng RAW/STAGING/CLEAN; không DROP/TRUNCATE/DELETE; không thay đổi schema.
> - ⚠️ **TUYỆT ĐỐI KHÔNG chạy file `flight_dw_2025_schema.sql`** trên database thật. Đó là bản mysqldump, có `DROP TABLE IF EXISTS` cho từng bảng.
> - Không ghi mật khẩu MySQL vào file. Tool sẽ hỏi mật khẩu (nhập ẩn) mỗi lần chạy.

---

## Bộ kit gồm những gì

```
03_DASHBOARD\                         (chép đè vào D:\DATA_WAREHOUSE\09_FINAL_HANDOFF\03_DASHBOARD)
├─ HUONG_DAN_HOAN_THIEN.md           tài liệu này
├─ CHANGELOG_APP.md                  chi tiết các thay đổi trong app.py
├─ 02_PYTHON_SOURCE\app.py           app đã hoàn thiện (thay app.py hiện tại)
├─ 05_SQL_EXPORTS\
│   ├─ 00_verify_bridge_status.sql   xác minh Bridge thủ công trong Workbench (tuỳ chọn)
│   └─ 01_benchmark_september_actual_arrival.sql   EXPLAIN + đo thời gian (tuỳ chọn)
├─ 06_FW_TOOLS\
│   ├─ fw_extract.py                 verify → explain → run → merge → status (chỉ SELECT)
│   ├─ fw_validate.py                kiểm định 2 CSV (không cần DB)
│   ├─ fw_common.py                  phần dùng chung
│   └─ requirements_tools.txt
├─ 07_TESTS\
│   ├─ test_dashboard.py             test toàn bộ app (route, callback, trang được bảo vệ)
│   └─ protected_functions.json      “dấu vân tay” của 4 trang Gold + trang Weather
├─ requirements.txt  .python-version  Procfile  Dockerfile  .dockerignore  .gitignore
```

**Những gì đã được kiểm thử trước khi giao.** Các test chạy trên MySQL 8.0.46 (cùng phiên bản với máy bạn), dùng đúng DDL thật của `flight_dw_2025` và dữ liệu test tổng hợp chỉ có trong sandbox.
- `verify` phát hiện đúng partition đủ, chưa nạp và nạp dở.
- Output của extractor **trùng khớp từng ô** với query gốc `01_export_flight_weather_impact_FIXED…sql` và `02_export_flight_weather_coverage.sql`.
- Test tải một tháng 560,000 chuyến (2.24 triệu dòng Bridge): khoảng 22 giây, RAM đỉnh khoảng 590 MB (đo trong sandbox; máy bạn có thể chậm hơn).
- Validator phát hiện CSV bị sửa tay.
- App: 6 trang + `/health` trả 200; 112–116 lần gọi callback qua HTTP đều thành công; chạy được dưới gunicorn.
- Tất cả đã chạy trên Python 3.12 và 3.13.

---

## Bước 0 — Sao lưu và cài kit (khoảng 5 phút)

Mở **PowerShell** và chạy từng khối lệnh:

```powershell
$Root  = 'D:\DATA_WAREHOUSE'
$Dash  = "$Root\09_FINAL_HANDOFF\03_DASHBOARD"
$Py    = "$Root\.venv312_compat\Scripts\python.exe"
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

# 0.1 Sao lưu app.py và thư mục dữ liệu hiện tại (rollback)
New-Item -ItemType Directory "$Dash\_backup_$Stamp" | Out-Null
Copy-Item "$Dash\02_PYTHON_SOURCE\app.py" "$Dash\_backup_$Stamp\app.py"
Copy-Item "$Dash\03_EXPORT_DATA" "$Dash\_backup_$Stamp\03_EXPORT_DATA" -Recurse
foreach ($f in '.gitignore','.dockerignore','requirements.txt','Procfile','Dockerfile') {
    if (Test-Path "$Dash\$f") { Copy-Item "$Dash\$f" "$Dash\_backup_$Stamp\$f" }   # file cùng tên sẽ bị kit ghi đè
}
Get-ChildItem "$Dash\_backup_$Stamp" -Recurse | Measure-Object | Select-Object Count
```

```powershell
# 0.2 Giải nén kit (đổi đường dẫn ZIP nếu bạn lưu ở chỗ khác)
$Zip = "$env:USERPROFILE\Downloads\FW_COMPLETION_KIT.zip"
Expand-Archive $Zip -DestinationPath "$env:TEMP\fw_kit_$Stamp" -Force
Copy-Item "$env:TEMP\fw_kit_$Stamp\03_DASHBOARD\*" $Dash -Recurse -Force
Set-Location $Dash
Get-ChildItem -Name
```

```powershell
# 0.3 Kiểm tra môi trường Python (đã có sẵn trong .venv312_compat)
& $Py -c "import sys,dash,plotly,pandas,mysql.connector as m; print(sys.version.split()[0], dash.__version__, plotly.__version__, pandas.__version__, m.__version__)"
```

**Kết quả mong đợi**
- 0.1: `Count` lớn hơn 0.
- 0.2: thấy các thư mục `02_PYTHON_SOURCE`, `03_EXPORT_DATA`, `04_CSS`, `05_SQL_EXPORTS`, `06_FW_TOOLS`, `07_TESTS`, cùng các file `Procfile`, `Dockerfile`, …
- 0.3: in ra `3.12.10 4.5.0 7.1.0 2.2.3 26.10.0`.

**Dừng lại nếu:** 0.3 báo `ModuleNotFoundError`. Khi đó chạy `& $Py -m pip install -r 06_FW_TOOLS\requirements_tools.txt` rồi kiểm tra lại.

**Kiểm tra nhanh rằng app mới chạy được trên dữ liệu hiện có** (chưa có CSV Flight × Weather):
```powershell
& $Py 07_TESTS\test_dashboard.py
```
Kết quả mong đợi: dòng cuối là `RESULT: PASS — 179 checks passed, 0 failed` (số checks có thể chênh nhẹ).

---

## Bước 1 — Khai báo kết nối MySQL (không lưu mật khẩu)

```powershell
$env:FLIGHT_DW_DB_HOST = '127.0.0.1'
$env:FLIGHT_DW_DB_PORT = '3306'
$env:FLIGHT_DW_DB_NAME = 'flight_dw_2025'
$env:FLIGHT_DW_DB_USER = 'root'        # hoặc tài khoản MySQL bạn đang dùng
```

Biến môi trường chỉ tồn tại trong cửa sổ PowerShell hiện tại. Nếu mở cửa sổ mới, hãy chạy lại Bước 0 (các biến `$Root…$Py`) và Bước 1. Mật khẩu **không** đặt vào biến: tool sẽ hỏi `MySQL password (hidden):` mỗi lần chạy.

> Tuỳ chọn: bạn có thể dùng một tài khoản chỉ có quyền SELECT trên `flight_dw_2025`. Việc này không bắt buộc, vì tool đã ép phiên READ ONLY. Tạo user/GRANT là thay đổi quản trị MySQL, nên chỉ làm nếu bạn muốn.

---

## Bước 2 — Xác minh trạng thái Bridge từ database (khoảng 2–15 phút)

```powershell
& $Py 06_FW_TOOLS\fw_extract.py verify
```

Tool đọc journal `D:\DATA_WAREHOUSE\06_DW_DESIGN\02_PHYSICAL_MODEL\_checkpoints\30E3_flight_weather_bridge_checkpoint_journal.jsonl` và file preview `30E3_flight_weather_bridge_preview_*.json`. Sau đó, với mỗi tháng 01–12, tool quét Bridge theo PRIMARY KEY trong đúng dải FlightKey của tháng đó (chia nhỏ theo chunk 50,000 chuyến).

**Kết quả mong đợi** (in ra màn hình và lưu ở `_fw_work\bridge_verification.txt`):
```
Result        : PASS
Verified      : 36 partitions, 20,971,684 Bridge rows
Not loaded    : 12 partitions
Failed        : 0 []
Partial (WARN): 0 []
```
- Mỗi partition tháng 01–09 có `DB rows` bằng `expected`: 01 = 539,747; 02 = 504,884; 03 = 600,872; 04 = 583,950; 05 = 605,648; 06 = 611,575; 07 = 631,428; 08 = 602,378; 09 = 562,439. Cột `Matched` bằng cột `Preview`.
- Tháng 10–12 đều `NOT_LOADED` (0 dòng).

| Nếu thấy | Ý nghĩa | Làm gì |
|---|---|---|
| `PASS_WITH_WARNINGS` + `Partial (WARN): ['10\|SCHEDULED_DEPARTURE']` | DB có tối đa vài nghìn dòng tháng 10 mà journal chưa ghi (loader dừng giữa commit và ghi journal) | Không ảnh hưởng tháng 01–09: các dòng này tự động bị loại. Ghi lại để báo cáo, rồi đi tiếp. |
| Partition 01–09 có `FAIL…` | DB không khớp journal/preview | **Dừng.** Gửi `_fw_work\bridge_verification.txt` cho Claude. |
| `STEP 30E3 journal not found` | Sai đường dẫn | Thêm `--project-root D:\DATA_WAREHOUSE` hoặc `--journal "<đường dẫn .jsonl>"`. |
| `Access denied` | Sai user/mật khẩu | Kiểm tra lại Bước 1. |
| Một chunk chạy quá 240 giây | Tool tự chia đôi chunk | Không cần làm gì. |

Sau bước này bạn có **bằng chứng DB chính thức** về trạng thái Bridge: 36/48 partition, tháng 01–09.

---

## Bước 3 — Kiểm tra kế hoạch truy vấn và benchmark một partition (khoảng 1–5 phút)

```powershell
# 3.1 Kế hoạch thực thi (chỉ EXPLAIN, không đọc dữ liệu)
& $Py 06_FW_TOOLS\fw_extract.py explain --partition 09:ACTUAL_ARRIVAL
```
**Mong đợi:** có dòng `Index range scan on b using PRIMARY over (… FlightKey …)` và hai dòng `Single-row index lookup on f using PRIMARY`, `Single-row index lookup on w using PRIMARY`.
**Dừng lại nếu:** thấy `Table scan on b`. Gửi output cho Claude.

```powershell
# 3.2 Benchmark: xuất đúng 1 partition đã có bằng chứng (tháng 9, ACTUAL_ARRIVAL)
Measure-Command { & $Py 06_FW_TOOLS\fw_extract.py run --months 09 --exposures ACTUAL_ARRIVAL | Out-Host }
```
**Mong đợi:**
```
[PASS] 09|ACTUAL_ARRIVAL: coverage 562,439 rows (matched 558,318); impact 558,318 matched rows -> … groups; flags {… all 0 …}
```
Các con số này khớp với lần bạn kiểm tra thủ công trước đây (558,318 matched + 2,886 cancelled + 1,224 diverted + 11 unresolved). Hãy ghi lại `TotalSeconds`.

**Ước tính thời gian cho toàn bộ:** tool chạy 4 exposure của cùng một tháng trong một lần quét, nên mỗi tháng tốn khoảng (thời gian benchmark × 1.5–3). Nhân với 9 tháng.

**Dừng lại nếu:** kết quả `[FAIL]`, hoặc `flags` khác 0. Gửi `_fw_work\partials\qa_09_ACTUAL_ARRIVAL.json`.

> Muốn xem thêm bằng Workbench: mở `05_SQL_EXPORTS\01_benchmark_september_actual_arrival.sql`, chạy từng câu (Ctrl+Enter).

---

## Bước 4 — Xuất toàn bộ 36 partition đã xác minh (vài phút đến khoảng 1 giờ, tuỳ máy)

```powershell
& $Py 06_FW_TOOLS\fw_extract.py run
```
- Chạy **tuần tự** từng tháng (không chạy song song, không gây tải dồn lên MySQL). Mỗi tháng quét PRIMARY KEY theo chunk 50,000 chuyến.
- Partition đã xong (ví dụ `09|ACTUAL_ARRIVAL` ở Bước 3) sẽ được bỏ qua.
- **Bị ngắt giữa chừng** (mất điện, Ctrl+C, mất kết nối)? Chỉ cần chạy lại đúng lệnh trên. Tool tiếp tục từ partition chưa xong, vì mỗi partition chỉ được ghi checkpoint khi đã hoàn tất.

**Mong đợi:** 36 dòng `[PASS] mm|EXPOSURE …`, tất cả `flags` bằng 0. Kiểm tra tiến độ bất cứ lúc nào:
```powershell
& $Py 06_FW_TOOLS\fw_extract.py status
```

| Sự cố | Cách xử lý |
|---|---|
| `hit MAX_EXECUTION_TIME; splitting in half` lặp lại nhiều lần | Bình thường. Nếu quá chậm, chạy `run --chunk-size 25000`. |
| `Lost connection` / Error 2013 | Tool tự kết nối lại 2 lần. Nếu vẫn lỗi, chạy lại `run`. |
| Thiếu RAM | `run --chunk-size 25000` (RAM đỉnh giảm theo kích thước chunk). |
| Muốn chạy từng tháng | `run --months 01`, rồi `run --months 02`, … |
| `[FAIL]` ở partition nào đó | **Dừng.** Gửi file `_fw_work\partials\qa_<mm>_<EXPOSURE>.json`. |

---

## Bước 5 — Gộp thành 2 CSV và manifest (dưới 1 phút)

```powershell
& $Py 06_FW_TOOLS\fw_extract.py merge
```
**Mong đợi:**
```
[MERGE] 36 partitions -> flight_weather_impact_2025.csv (… rows), flight_weather_coverage_2025.csv (… rows), flight_weather_manifest_2025.json
[MERGE] Scope: January–September 2025 | written to …\03_EXPORT_DATA
```
`merge` từ chối chạy nếu có partition FAIL, partition chưa được VERIFIED, hoặc journal đã thay đổi kể từ lúc export.

Ba file mới trong `03_EXPORT_DATA`:
- `flight_weather_impact_2025.csv`: chỉ các dòng MATCHED. Grain là tháng × ExposureType × sân bay × dải mưa × dải gió. Cột giữ đúng data contract mà app đang dùng.
- `flight_weather_coverage_2025.csv`: mọi WeatherCoverageStatus (matched, cancelled, diverted, unresolved, outside-window).
- `flight_weather_manifest_2025.json`: phạm vi, danh sách partition, số dòng, kết quả QA từng partition, BridgeRunID, SHA256 của journal và của 2 CSV.

---

## Bước 6 — Kiểm định độc lập 2 CSV (dưới 1 phút)

```powershell
& $Py 06_FW_TOOLS\fw_validate.py
```
**Mong đợi:** `QA PASS: … checks, 0 FAIL, … WARN`. Báo cáo chi tiết nằm ở `03_EXPORT_DATA\flight_weather_qa_report_2025.txt`.

Các nhóm kiểm tra chính:
1. SHA256 của 2 CSV khớp manifest; cột khớp data contract; grain không trùng lặp.
2. Các ràng buộc metric: Eligible ≤ Flights; Delayed ≤ Eligible; DelayRatePct = Delayed/Eligible; số WeatherKey khác nhau ≤ số dòng; độ ẩm và mây trong 0–100; phút sau mốc giờ trong 0–59.
3. Với mỗi partition: tổng coverage = số dòng kỳ vọng trong journal; số matched trong coverage = preview; tổng impact = số matched.
4. **Đối soát với Gold** (`vw_gold_monthly_summary.csv`): eligible/delayed của SCHEDULED_DEPARTURE và SCHEDULED_ARRIVAL từng tháng chỉ được thấp hơn Gold tối đa bằng số exposure không khớp thời tiết của partition đó. Ví dụ cho tháng 01–09: departure không khớp tổng cộng 3 dòng, arrival 156 dòng. Hai exposure ACTUAL chỉ ở mức cảnh báo (WARN), vì chuyến huỷ hoặc timestamp chưa duyệt không có thời điểm thực tế.

**Dừng lại nếu:** có `FAIL`. Gửi `flight_weather_qa_report_2025.txt` cho Claude.

---

## Bước 7 — Test toàn bộ app với dữ liệu thật (khoảng 1–3 phút)

```powershell
& $Py 07_TESTS\test_dashboard.py
```
**Mong đợi:**
```
   /health -> {"coverage_rows": …, "impact_rows": …, "manifest_integrity": "OK", "scope": "January–September 2025"}
RESULT: PASS — … checks passed, 0 failed
```
Test này kiểm tra:
- (1) 45 hàm của 4 trang Gold và 11 hàm của trang Weather không bị thay đổi (so bằng dấu vân tay mã nguồn).
- (2) Cả 6 trang, `/health` và các endpoint của Dash trả 200.
- (3) Mọi callback được gọi qua HTTP như từ trình duyệt, với mọi lựa chọn dropdown, khi xoá hết bộ lọc, và với ô tìm kiếm có kết quả hoặc không có kết quả.
- (4) Trang Flight × Weather không hiển thị số liệu khi thiếu snapshot.

---

## Bước 8 — Chạy và kiểm tra bằng mắt trên máy (khoảng 10 phút)

```powershell
& $Py 02_PYTHON_SOURCE\app.py
```
Mở http://127.0.0.1:8050 và kiểm tra theo danh sách:

| Trang | Kiểm tra |
|---|---|
| Overview, Airlines, Airports, Time | Giống hệt trước khi cập nhật. Thử xoá hết hãng ở trang Airlines: giờ hiện thông báo “No airline records…” thay vì lỗi. |
| Weather | Giống hệt trước khi cập nhật (dữ liệu cả năm, 352 sân bay). |
| Flight × Weather | Banner: `Validated snapshot loaded · scope January–September 2025 · BridgeRunID 20261110_030433_504879 …` |
| | Dropdown tháng chỉ có 01–09. Mặc định là `Departure · scheduled at origin`. |
| | Có 5 thẻ KPI, biểu đồ mưa, gió, xu hướng tháng, scatter sân bay, coverage và 2 bảng. |
| | Chọn `Arrival · actual at destination` + tháng `09`: coverage hiện các status CANCELLED/DIVERTED/UNRESOLVED; KPI coverage = 558,318 / 562,439 (khoảng 99.27%). |
| | Xoá hết lựa chọn quốc gia: kết quả giống “tất cả quốc gia” (lỗi cũ đã được sửa). |
| `http://127.0.0.1:8050/health` | JSON có `"status": "ok"` và `"manifest_integrity": "OK"`. |

Nhấn Ctrl+C để dừng app.

---

## Bước 9 — Chuẩn bị deploy (chế độ snapshot, không cần DB khi chạy)

**Vì sao chọn chế độ snapshot:** app chỉ đọc CSV, không mở cổng MySQL ra Internet, không cần lưu bí mật trên server, phản hồi nhanh và ổn định. Dữ liệu được làm mới bằng cách chạy lại Bước 4–7 rồi deploy lại.

Những gì được đưa lên server: `02_PYTHON_SOURCE\`, `03_EXPORT_DATA\` (6 Gold + 2 Weather + 2 Flight × Weather CSV + manifest), `04_CSS\`, `requirements.txt`, `.python-version`, `Procfile` (hoặc `Dockerfile`).

**Không đưa lên:** `.env`, mật khẩu, `.venv*`, `_fw_work\`, `_backup_*\`, các bản dump DB. Các mục này đã được liệt kê trong `.gitignore` và `.dockerignore`.

```powershell
# 9.1 Kích thước dữ liệu sẽ deploy (GitHub giới hạn 100 MB mỗi file)
Get-ChildItem 03_EXPORT_DATA -File | Select-Object Name,@{n='MB';e={[math]::Round($_.Length/1MB,2)}}
```

```powershell
# 9.2 (Nếu dashboard nằm trong repo GitHub của bạn) xem trước những gì sẽ commit
git -C $Root status --short -- "09_FINAL_HANDOFF/03_DASHBOARD"
```
Chỉ commit sau khi đã xem kỹ danh sách. Không được có `.env` hay thư mục `_fw_work`.

Lệnh khởi động trên server (đã ghi sẵn trong `Procfile`):
```
gunicorn --chdir 02_PYTHON_SOURCE app:server --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-1} --threads 4 --timeout 120
```
Health check path: `/health`. Không cần biến môi trường nào về database.

---

## Bước 10 — Deploy lên nhà cung cấp hosting

Claude sẽ hướng dẫn chi tiết theo nền tảng bạn chọn. Dưới đây là hai cách phổ biến.

**A. Render (Web Service, Python) — kết nối repo GitHub**

| Trường | Giá trị |
|---|---|
| Root Directory | `09_FINAL_HANDOFF/03_DASHBOARD` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn --chdir 02_PYTHON_SOURCE app:server --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120` |
| Health Check Path | `/health` |
| Environment | `PYTHON_VERSION=3.12.10` (không cần biến DB) |

**B. Docker (chạy được trên mọi nền tảng hỗ trợ container)**
```powershell
docker build -t aero-insights:fw1 .
docker run --rm -p 8050:8050 aero-insights:fw1
# mở http://127.0.0.1:8050/health
```

**Kiểm tra sau deploy:** `https://<tên-miền>/health` phải trả `status: ok` với `impact_rows` và `coverage_rows` giống máy local. Sau đó mở đủ 6 trang.

---

## Bước 11 — Rollback (khi cần)

| Tình huống | Cách khôi phục |
|---|---|
| App mới có vấn đề trên máy | `Copy-Item "$Dash\_backup_<Stamp>\app.py" "$Dash\02_PYTHON_SOURCE\app.py" -Force` |
| Muốn tạm ẩn số liệu Flight × Weather | Di chuyển 3 file `flight_weather_*` (impact, coverage, manifest) ra khỏi `03_EXPORT_DATA`. Trang sẽ trở về trạng thái chờ, các trang khác không bị ảnh hưởng. |
| Bản deploy có lỗi | Dùng chức năng rollback về bản deploy trước của nhà cung cấp, hoặc redeploy commit trước. |
| Bản dự phòng cuối cùng | `app_v2_snapshot_baseline.py` trong gói handoff (4 trang Gold). |

---

## Gửi lại cho Claude để nghiệm thu cuối

1. `_fw_work\bridge_verification.txt`
2. Output của Bước 3 (EXPLAIN + dòng `[PASS] 09|ACTUAL_ARRIVAL` + `TotalSeconds`)
3. `03_EXPORT_DATA\flight_weather_manifest_2025.json`
4. `03_EXPORT_DATA\flight_weather_qa_report_2025.txt`
5. Dòng cuối của `07_TESTS\test_dashboard.py`
6. 1–2 ảnh chụp trang Flight × Weather
7. Nền tảng hosting bạn muốn dùng (Render / Railway / Fly.io / VPS + Docker / …)

## Giới hạn cần ghi rõ trong báo cáo

- Phân tích Flight × Weather chỉ gồm **tháng 01–09/2025** (36/48 partition Bridge đã nạp và xác minh). Tháng 10–12 chưa được nạp vào Bridge. Bước 30E4 (kiểm định toàn cục 48/48) chưa chạy.
- Trong slide, “28.006.476 exposure / 48/48” là **số kỳ vọng / preflight file nguồn**, không phải số đã nạp vào DB.
- Số liệu đếm là **exposure events**: một chuyến bay xuất hiện một lần ở mỗi ExposureType. Không cộng dồn giữa các ExposureType.
- Dải mưa (mm) và dải gió (km/h) là nhóm khám phá, không phải thang cảnh báo thời tiết. Đây là mối liên hệ mô tả, **không phải quan hệ nhân quả**.
- Chênh lệch giữa Open-Meteo CLEAN (240 site) và Weather Fact (352 site) vẫn chưa được đối soát (nằm ngoài phạm vi lần này).
