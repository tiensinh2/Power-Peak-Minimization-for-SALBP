# Power Peak Minimization for SALBP (SALB3PM)

Dự án bài tập lớn số 2, chủ đề 9 — môn Các vấn đề hiện đại trong Khoa học máy tính, HK I 2026–2027.

Mục tiêu là xây dựng và đánh giá các mô hình SAT/MaxSAT cho **Simple Assembly Line Balancing Problem with Power Peak Minimization (SALB3PM)**. Đây là bộ khung khởi đầu: encoding SALB3PM hoàn chỉnh và các baseline chưa được triển khai.

Paper tham khảo chính: Z. Zheng, S. Cherif, R. S. Shibasaki, “Optimizing Power Peaks in Simple Assembly Line Balancing through Maximum Satisfiability,” ICTAI 2024, [DOI: 10.1109/ICTAI62512.2024.00060](https://doi.org/10.1109/ICTAI62512.2024.00060). Tóm tắt cách nối paper với các module dự kiến ở [docs/PAPER_MAPPING.md](docs/PAPER_MAPPING.md).

## Bắt đầu sau khi clone

Yêu cầu: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/) và Python 3.11. uv tự chọn Python theo `.python-version` nếu máy đã có sẵn; cài Python bằng `uv python install 3.11` khi cần.

```powershell
git clone https://github.com/tiensinh2/Power-Peak-Minimization-for-SALBP.git
cd Power-Peak-Minimization-for-SALBP
uv sync --locked --extra dev
uv run salb3pm smoke
```

`uv sync` tạo môi trường `.venv`, cài PySAT cùng thư viện PB encoding, và cài các công cụ phát triển. Không cần kích hoạt môi trường thủ công. Kết quả cuối của lệnh smoke phải là `PySAT PB encoding + MaxSAT RC2: OK`.

Để cài baseline cụ thể, chỉ thêm dependency tương ứng:

```powershell
uv sync --locked --extra dev --extra cp-sat
uv sync --locked --extra dev --extra mip-gurobi
uv sync --locked --extra dev --extra mip-cplex
uv sync --locked --extra dev --extra plots
```

Các nhóm này chỉ cài API Python. Gurobi và IBM CPLEX/CP Optimizer có thể cần solver riêng, license và cấu hình môi trường. Ghi `NOT_RUN` cùng lý do nếu không thể chạy; không ghi là timeout hay UNSAT. Xem [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md).

## Cấu trúc dự án

```text
.
├── data/
│   ├── instances/       # instance nhỏ để phát triển và kiểm tra
│   ├── solutions/       # lời giải mẫu / lời giải dùng đối chiếu
│   └── benchmarks/      # hướng dẫn nguồn và nơi đặt benchmark ngoài
├── docs/                # paper mapping, dữ liệu, protocol thực nghiệm
├── report/              # bài báo LaTeX theo mẫu cas-sc
├── results/
│   ├── raw/             # CSV/JSON kết quả có thể tái lập
│   ├── logs/            # log solver
│   └── figures/         # biểu đồ báo cáo
├── src/salb3pm/
│   ├── cli.py           # entry point; currently provides setup smoke command
│   ├── smoke.py         # checks PySAT PB encoding and MaxSAT RC2
│   ├── encodings/       # PB/CNF helpers
│   ├── experiments/     # runner và xuất kết quả
│   └── models/          # các mô hình SAT, MaxSAT và baseline
├── tests/               # kiểm tra schema, validator và encoding
├── CONTRIBUTING.md
├── IMPLEMENTATION_PLAN.md
├── pyproject.toml
└── uv.lock
```

Các thư mục chưa có chức năng được giữ bằng `.gitkeep`; thay bằng mã/tài liệu khi bắt đầu phần việc tương ứng. Không commit `.venv`, dữ liệu benchmark tải về, license hoặc kết quả chưa có cấu hình chạy để tái lập.

## Lệnh làm việc

```powershell
uv run salb3pm smoke
uv run ruff format .
uv run ruff check .
```

Lệnh smoke chỉ kiểm tra cài đặt PySAT PB encoder và MaxSAT RC2, chưa giải instance SALB3PM. Cập nhật tiến độ và hướng dẫn lệnh chạy trong `IMPLEMENTATION_PLAN.md` khi thêm mô hình/CLI.

Thư mục `tests/` đã được chuẩn bị nhưng bộ kiểm tra tự động sẽ được thêm cùng các module đầu tiên; hiện chưa có test suite để chạy.

## Hướng nghiên cứu và yêu cầu môn học

- Cài đặt mô hình SAT/MaxSAT theo paper; dùng pseudo-Boolean encoding của PySAT và MaxSAT như yêu cầu chủ đề 9.
- So sánh với các phương pháp chính xác: CPLEX CP, CPLEX MIP, Gurobi và CP-SAT (phụ thuộc khả năng cài đặt/license).
- Thử nghiệm trên benchmark đủ lớn, lưu kết quả và command để tái lập.
- Trình bày báo cáo dạng bài báo khoa học theo template Elsevier `cas-sc`; trực quan hóa bằng `cnsplots`.
- Đưa URL repository vào Data Availability của báo cáo.

Report dùng cùng định dạng Elsevier `cas-sc` một cột với dự án N-Queens. Cài MiKTeX/LaTeX có `pdflatex` và `bibtex`, rồi xem [report/README.md](report/README.md) để biên dịch manuscript.

Chi tiết dataset và protocol nằm ở [docs/DATASET.md](docs/DATASET.md) và [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md). Không xem ví dụ toy hoặc smoke test là kết quả tối ưu của mô hình.
