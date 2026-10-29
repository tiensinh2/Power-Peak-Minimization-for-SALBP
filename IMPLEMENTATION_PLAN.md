# Implementation Plan — SALB3PM

Checklist theo các chặng triển khai chính. Cập nhật trạng thái khi có đầu ra kiểm tra được; không ghi nhận kết quả thực nghiệm nếu chưa có dữ liệu và lệnh tái lập.

## 1. Chuẩn bị dataset theo paper

- [x] Tải đúng bộ benchmark SALBP-1 mà paper sử dụng từ [Scholl 1993 benchmark data sets](https://assembly-line-balancing.de/salbp/benchmark-data-sets-1993/); đọc file mô tả graph và định dạng trước khi viết parser.
- [ ] Dựng các instance SALB3PM theo protocol paper: giữ precedence graph và cycle time; đặt số station bằng nghiệm SALBP-1 tối ưu `m*`; sinh power task theo phân phối đều `[5, 50]`.
- [ ] Paper báo cáo 97 instance SALB3PM. Ghi rõ phần nào tái lập được; lưu seed và quy tắc sinh power vì bộ power/seed gốc có thể không được công bố.
- [ ] Lưu nguồn, phiên bản, checksum, quy tắc chuyển đổi và manifest instance trong [docs/DATASET.md](docs/DATASET.md). Không đưa archive benchmark vào Git nếu chưa rõ quyền phân phối.
- [ ] Tạo một số instance nhỏ để phát triển và kiểm tra; dùng benchmark paper làm tập thực nghiệm chính. Chưa mở rộng sang dataset khác trước khi hoàn tất tập này.

## 2. Schema và kiểm chứng lời giải

- [ ] Chốt schema instance thống nhất: task ID, duration, power, cycle time, số station và precedence arcs.
- [ ] Viết parser/validator instance: kiểm tra ID, miền giá trị, precedence DAG và các điều kiện khả thi cơ bản.
- [ ] Chốt quy ước thời gian và khoảng thực hiện task `[start, start + duration)`.
- [ ] Viết validator lời giải độc lập: station assignment, cycle time, precedence, không overlap trên cùng station; tự tính power profile và peak.
- [ ] Dùng ví dụ Figure 1 của paper làm fixture đối chiếu; bổ sung test cho dữ liệu lỗi và các trường hợp biên.

## 3. Mô hình SAT/MaxSAT theo paper

- [ ] Map biến và ràng buộc Fig. 3/Fig. 4 sang code, ghi phương trình/trang trong [docs/PAPER_MAPPING.md](docs/PAPER_MAPPING.md).
- [ ] Cài mô hình unary (inaugural) và binary; giữ chung interface để giải, giải mã và kiểm chứng nghiệm.
- [ ] Dùng PySAT `PBEnc` cho pseudo-Boolean constraints; ưu tiên Binary Merger như paper. Dùng PySAT MaxSAT/RC2 cho soft clauses và ghi rõ encoding/version.
- [ ] Kiểm tra cận `LB`/`UB`, miền thời gian, biến phụ, trọng số bit và các trường hợp biên của peak.
- [ ] So sánh hai mô hình trên instance nhỏ: status, optimum, số biến/clause và runtime; đối chiếu với validator và vét cạn cho toy instance.

## 4. Exact baselines và công cụ chạy

- [x] Cài API/runtime cho các baseline đề bài yêu cầu: CP-SAT, CPLEX CP, CPLEX MIP và Gurobi MIP.
- [x] Tích hợp các baseline với instance, result schema và validator dùng chung.
- [x] Kiểm tra cài đặt/license từng solver; nếu không chạy được, ghi `NOT_RUN` cùng lý do. Smoke solve đã thành công; Gurobi xử lý được 2.001 biến nhị phân, CPLEX MIP/CP xử lý được 1.001 biến sau khi nối Python runtime với CPLEX Studio 22.2.
- [x] Bổ sung CLI/runner để chạy một instance; lưu solver/version, status, objective, bound, runtime, checksum instance và log. Batch runner còn thiếu.
- [x] Chuẩn hóa status thành `OPTIMAL`, `FEASIBLE`, `UNSAT`, `TIMEOUT`, `ERROR`, `NOT_RUN`.

## 5. Thực nghiệm và phân tích

- [ ] Chạy pilot trên vài instance thuộc các cỡ khác nhau; sau đó chạy tập benchmark paper đã chuyển đổi.
- [ ] Chốt timeout, số lần lặp, seed, hardware và solver settings trước khi chạy; paper dùng cutoff 3600 giây, ghi rõ nếu nhóm chọn giới hạn khác.
- [ ] So sánh unary/binary trên cùng instance; so sánh baseline trên cùng subset và điều kiện tài nguyên.
- [ ] Lưu raw CSV/JSON và log dưới `results/`; không bỏ các lần timeout/lỗi khỏi báo cáo.
- [ ] Xác minh mọi nghiệm bằng validator; tổng hợp objective, bound/gap, runtime, timeout và kích thước model.
- [ ] Tạo bảng/biểu đồ từ raw results bằng script; dùng `cnsplots` theo yêu cầu môn học.

## 6. Báo cáo và hoàn thiện

- [ ] Hoàn thiện [report/manuscript.tex](report/manuscript.tex) theo Elsevier `cas-sc`: phương pháp, nguồn dữ liệu, giao thức, kết quả và giới hạn.
- [ ] Trích dẫn paper, nguồn benchmark, PySAT và các solver; bảo đảm mọi bảng/số liệu khớp raw results.
- [ ] Thay author/email/repository placeholders, điền Data Availability, biên dịch PDF và rà lại citation/TODO trước khi nộp.
- [ ] Cập nhật README với lệnh cài đặt, chạy solver, chạy thực nghiệm và tái tạo hình.

## Hoàn thành khi

- [ ] Dataset theo paper có nguồn và quy trình chuyển đổi tái lập được.
- [ ] Unary/binary và baseline trả kết quả được kiểm chứng độc lập trên fixture và benchmark.
- [ ] Raw results, log, bảng và hình có thể tái tạo bằng lệnh/config đã lưu.
- [ ] README và báo cáo mô tả đúng code, dữ liệu, kết quả và giới hạn.

## Trạng thái hiện tại

- [x] Starter repo, `uv` environment/lockfile và hướng dẫn clone
- [x] Smoke check PySAT PB + MaxSAT RC2
- [x] Template report Elsevier CAS và script biên dịch
- [ ] Dataset SALBP-1 theo paper và quy trình sinh power (đã tải 25 graph `.IN2`, còn parser, manifest benchmark/SALB3PM và sinh power)
- [ ] Parser/schema và independent solution validator (đã có schema JSON và validator schedule; parser `.IN2` còn thiếu)
- [ ] Unary và binary MaxSAT models
- [ ] CP-SAT, CPLEX CP/MIP và Gurobi baselines (adapter đã triển khai; chạy đối chiếu trên fixture/benchmark còn thiếu)
- [ ] Experiment runner, benchmark results và `cnsplots` figures
- [ ] Hoàn thiện manuscript và kiểm tra tái lập từ clone sạch

Ghi chú môi trường local: `uv sync --locked --extra dev --extra cp-sat --extra mip-cplex --extra mip-gurobi` cài API cho toàn bộ solver. Trên máy hiện tại, `docplex config --upgrade` đã nối CPLEX/CP Optimizer runtime trong `.venv` với CPLEX Optimization Studio 22.2; các solver đã giải được smoke model. README ghi lệnh setup tái lập.

Ghi chú mã hiện tại: baseline adapters dùng chung formulation time-indexed và independent schedule validator; kết quả từng instance được ghi vào `results/raw/` kèm checksum đầu vào và log dưới `results/logs/`. Chưa chạy kiểm chứng tích hợp trong lượt này.
