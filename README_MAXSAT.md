# SALB3PM MaxSAT Models Implementation

Triển khai mã nguồn mô hình hóa và giải bài toán **Simple Assembly Line Balancing Problem with Power Peak Minimization (SALB3PM)** bằng **Maximum Satisfiability (MaxSAT)** dựa trên bài báo khoa học:
> *Zhifei Zheng, Sami Cherif, Rui Sá Shibasaki.* **"Optimizing Power Peaks in Simple Assembly Line Balancing through Maximum Satisfiability"**, *IEEE ICTAI 2024*.

---

## Cấu trúc thư mục

Dự án được chia thành 2 thư mục tương ứng với 2 mô hình theo yêu cầu:

```
.
├── inaugural_model/             # Mô hình MaxSAT cơ sở (Inaugural Model - Section III-A, Fig 3)
│   ├── __init__.py
│   ├── encoder.py              # Bộ mã hóa WCNF (Unary variables U_j, PB constraints)
│   ├── solver.py               # Runner giải bằng PySAT (RC2) & xuất DIMACS WCNF
│   └── main.py                 # CLI chạy mô hình Inaugural
│
├── binary_model/                # Mô hình MaxSAT cải tiến biểu diễn nhị phân (Section III-B, Fig 4)
│   ├── __init__.py
│   ├── encoder.py              # Bộ mã hóa WCNF (Binary variables binU_j, PB constraints)
│   ├── solver.py               # Runner giải bằng PySAT (RC2) & xuất DIMACS WCNF
│   └── main.py                 # CLI chạy mô hình Binary
│
├── common/                      # Module dùng chung
│   ├── instance.py             # Cấu trúc dữ liệu bài toán SALB3PM, parser JSON & validator
│   ├── pb_encoder.py           # Mã hóa Pseudo-Boolean (PB) sang CNF bằng BDD / Cardinality
│   └── visualizer.py           # Báo cáo kết quả, biểu đồ Gantt trạm & biểu đồ công suất
│
├── data/                        # Dữ liệu thử nghiệm
│   ├── example_paper.json      # Instance ví dụ trong Fig 1 của bài báo (n=4, m=3, c=5)
│   └── instance_medium_8tasks.json # Instance thử nghiệm quy mô vừa (n=8, m=4, c=12)
│
├── compare.py                   # Script so sánh hiệu năng trực tiếp giữa 2 mô hình
├── requirements.txt             # Danh sách thư viện phụ thuộc
└── README.md
```

---

## 1. Cài đặt môi trường với `uv` và `venv`

### Bước 1: Tạo môi trường ảo với `uv`
```powershell
uv venv .venv
```

### Bước 2: Kích hoạt môi trường ảo
- **Windows (PowerShell):**
  ```powershell
  .\.venv\Scripts\activate
  ```
- **Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```

### Bước 3: Cài đặt thư viện với `uv`
```powershell
uv pip install -r requirements.txt --python .venv\Scripts\python.exe
```

---

## 2. Hướng dẫn chạy chương trình

### A. Chạy mô hình MaxSAT cơ sở (Inaugural Model)
```powershell
.\.venv\Scripts\python.exe -m inaugural_model.main
```
Hoặc chạy với file instance tùy chọn:
```powershell
.\.venv\Scripts\python.exe -m inaugural_model.main --file data/example_paper.json
```
Xuất file DIMACS WCNF (để dùng cho các solver bên ngoài như EvalMaxSAT, MaxHS, WMaxCDCL):
```powershell
.\.venv\Scripts\python.exe -m inaugural_model.main --export inaugural_formula.wcnf
```

### B. Chạy mô hình cải tiến biểu diễn nhị phân (Binary Representation Model)
```powershell
.\.venv\Scripts\python.exe -m binary_model.main
```
Hoặc với file dữ liệu:
```powershell
.\.venv\Scripts\python.exe -m binary_model.main --file data/instance_medium_8tasks.json
```
Xuất file DIMACS WCNF:
```powershell
.\.venv\Scripts\python.exe -m binary_model.main --export binary_formula.wcnf
```

### C. Chạy so sánh hiệu năng (Benchmark & Comparison)
Chạy so sánh cả 2 mô hình trên toàn bộ dữ liệu mẫu trong thư mục `data/`:
```powershell
.\.venv\Scripts\python.exe compare.py --all --details
```

---

## 3. Bảng so sánh 2 mô hình

| Đặc điểm | Mô hình Inaugural (Unary $U_j$) | Mô hình Binary ($\text{binU}_j$) |
| :--- | :--- | :--- |
| **Biến mục tiêu** | $U_j \in \{0, 1\}, \forall j \in \{1, \dots, UB\}$ ($UB$ biến) | $\text{binU}_j \in \{0, 1\}, \forall j \in \{0, \dots, \lceil \log_2 UB \rceil\}$ ($\approx \log_2 UB$ biến) |
| **Ràng buộc mềm** | $(\neg U_j, \text{weight}=1)$ | $(\neg \text{binU}_j, \text{weight}=2^j)$ |
| **Không gian tìm kiếm** | Lớn (tỷ lệ tuyến tính theo $UB$) | Nhỏ gọn (tỷ lệ logarithm theo $UB$) |
| **Số mệnh đề CNF** | Lớn hơn đáng kể khi $UB$ lớn | Giảm từ **3x - 5x** số biến và mệnh đề |
| **Tốc độ giải** | Chậm hơn trên các bài toán lớn | **Nhanh và ổn định vượt trội** |
