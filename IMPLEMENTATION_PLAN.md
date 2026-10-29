# Kế hoạch triển khai SALB3PM

Checklist theo thứ tự từ chuẩn bị dữ liệu đến báo cáo. Chọn người phụ trách từng nhóm việc khi chia nhóm; cập nhật checkbox sau khi có đầu ra kiểm tra được. Không đánh dấu hoàn thành chỉ vì đã có code hoặc đã chạy được một lần.

## 0. Chốt quy ước và phân công

- [ ] Chốt thành viên, người phụ trách chính và người review cho: dữ liệu/validator, MaxSAT, baseline, thực nghiệm, báo cáo.
- [ ] Đọc yêu cầu môn học và paper; thống nhất giả định về thời gian rời rạc, khoảng thực hiện task `[start, start + duration)`, precedence và ý nghĩa công suất.
- [ ] Chốt schema instance, solution và result trước khi nhiều nhánh cùng triển khai; cập nhật ví dụ trong README và tài liệu dataset.
- [ ] Chốt nhánh, commit message, review và cách cập nhật checklist theo [CONTRIBUTING.md](CONTRIBUTING.md).

## 1. Chuẩn bị benchmark và dữ liệu SALB3PM

### 1.1 Chọn nguồn SALBP-1 gốc

- [ ] Dùng **Scholl 1993 benchmark** làm tập chính để tái lập hướng làm trong paper SALB3PM. Bộ này gồm các tập kinh điển Talbot et al. và Hoffmann; đọc mô tả precedence graph và file format đi kèm trước khi viết parser. Nguồn và file tải được liên kết tại [trang benchmark Scholl 1993](https://assembly-line-balancing.de/salbp/benchmark-data-sets-1993/).
- [ ] Chỉ thêm **Otto et al. 2013 benchmark** làm tập mở rộng sau khi pipeline cho tập chính chạy ổn; đây là bộ dữ liệu SALBP-1 thiết kế có hệ thống, format và nguồn tải riêng ở [trang benchmark Otto 2013](https://assembly-line-balancing.de/salbp/benchmark-data-sets-2013/).
- [ ] Không lấy các bộ dữ liệu rất lớn hoặc không liên quan trực tiếp chỉ để tăng số instance. Giữ phạm vi chạy phù hợp thời gian, license solver và máy của nhóm.

### 1.2 Chuyển SALBP-1 thành instance SALB3PM

- [ ] Lưu riêng dữ liệu tải nguyên bản ở thư mục benchmark local (đang được Git ignore); commit metadata, hướng dẫn tải và script chuyển đổi, không commit archive lớn nếu chưa rõ quyền phân phối.
- [ ] Ghi tên bộ dữ liệu, URL, ngày/phiên bản tải, giấy phép/điều khoản, checksum SHA-256, mô tả định dạng và script chuyển đổi trong [docs/DATASET.md](docs/DATASET.md).
- [ ] Giữ precedence graph và cycle time từ SALBP-1 source. Chọn số station `m` theo nghiệm SALBP-1 `m*` đã được chứng minh tối ưu như paper; nếu dùng nghiệm feasible chưa chứng minh, ghi rõ đó là biến thể benchmark và kiểm tra tính khả thi.
- [ ] Sinh công suất task theo đúng giao thức paper: phân phối đều trong khoảng 5–50. Chốt rõ số nguyên hay số thực, hai đầu mút có bao gồm không, bộ sinh số ngẫu nhiên và seed; không tự nhận đã tái lập chính xác nếu paper không công bố seed.
- [ ] Nếu nhóm đủ thời gian, hướng tới quy mô 97 instance SALB3PM như paper; Table I báo cáo riêng năm family lớn (50 instance). Ghi rõ phần nào là tái lập protocol và phần nào dùng power realization/seed mới.
- [ ] Tạo nhiều lần gán công suất có seed khác nhau trên cùng graph nếu cần phân tích ảnh hưởng công suất; giữ các bản sinh độc lập, không ghi đè instance.
- [ ] Tạo ba tầng dữ liệu: toy fixture có đáp án kiểm tra được; pilot gồm vài instance đa dạng; benchmark chính được sinh/tái lập theo giao thức đã ghi. Chỉ thêm dataset Otto 2013 vào tầng mở rộng.
- [ ] Mỗi instance chuẩn hóa theo schema thống nhất: `name`, `cycle_time`, `num_stations`, tasks (`id`, `duration`, `power`), và danh sách precedence arcs.
- [ ] Kiểm tra số task, precedence arcs, cycle time, `m`, phân phối power và tính duy nhất của ID sau chuyển đổi; lưu manifest CSV/JSON gồm các thuộc tính này.
- [ ] Không gắn nhãn một kết quả là benchmark hoặc optimum nếu thiếu nguồn, trạng thái chứng minh hoặc lệnh tái lập.

**Đầu ra:** parser/convert script, manifest, toy fixtures, benchmark provenance và một lệnh dựng lại dữ liệu.

## 2. Hoàn thiện hợp đồng dữ liệu và validator độc lập

- [ ] Viết schema instance và kiểm tra kiểu/ràng buộc: ID task duy nhất, duration dương, power không âm, cycle time và số station dương, precedence chỉ tới task có thật.
- [ ] Kiểm tra precedence graph là DAG; phát hiện cycle và instance bất khả thi hiển nhiên, ví dụ task dài hơn cycle time.
- [ ] Chốt miền thời gian start và feasible start window dựa trên cycle time; giải thích rõ indexing trong code và paper.
- [ ] Định nghĩa solution format gồm đúng một station và start time cho mỗi task.
- [ ] Viết validator độc lập với solver: assignment hợp lệ, task nằm trong cycle, precedence giữa station và theo thời gian khi cùng station, không chồng lấn trên một station.
- [ ] Tính lại power profile từng time unit và peak từ schedule; không tin objective do solver trả về nếu chưa kiểm tra lại.
- [ ] Thêm test cho instance hợp lệ, sai schema, precedence cycle, thiếu/trùng task, vượt cycle, overlap, schedule không tôn trọng precedence và power peak mẫu.
- [ ] Dùng ví dụ Figure 1 trong paper làm fixture kiểm tra; xác nhận lời giải mẫu có peak 9 khi biểu diễn đúng dữ liệu và giả định của hình.

**Đầu ra:** schema version, validator, fixture và test suite. Thay đổi schema cần cập nhật importer, writer và tài liệu cùng một PR.

## 3. Cài mô hình SAT/MaxSAT theo paper

### 3.1 Từ công thức đến thiết kế

- [ ] Lập bảng mapping từng biến/ràng buộc của Fig. 3 và Fig. 4 sang module và hàm tạo CNF; ghi trang, số phương trình và index domains trong [docs/PAPER_MAPPING.md](docs/PAPER_MAPPING.md).
- [ ] Thống nhất biến `X[i,s]` (station assignment), `B[i,t]` (start trigger), `A[i,t]` (active), và biến ngưỡng/bit công suất đỉnh; xác nhận chính xác thời điểm task active theo khoảng nửa kín.
- [ ] Tính cận `LB` và `UB` theo paper, kiểm tra trường hợp `LB = UB`, `UB` nhỏ, `UB` không là lũy thừa của 2 và power/task bounds.
- [ ] Tạo ID/variable pool tập trung, bảo đảm biến phụ do PBEnc không đụng ID với biến mô hình.

### 3.2 Unary/inaugural MaxSAT

- [ ] Mã hóa hard constraints assignment, station precedence, temporal precedence, đúng một start, start window, activity, và không overlap cùng station theo Fig. 3 constraints (2)–(8).
- [ ] Cài unary threshold literals và soft clauses cho peak theo constraints (1), (9)–(11); kiểm tra quan hệ đơn điệu của threshold literals và objective có đúng bằng peak.
- [ ] Dùng PySAT `PBEnc` cho các pseudo-Boolean inequalities; cấu hình Binary Merger như giao thức paper khi tương thích, ghi rõ `EncType` và encoding version trong kết quả.
- [ ] Dùng PySAT MaxSAT/RC2 để tối ưu weighted/unweighted soft clauses; xác nhận hard/soft clauses được nạp đúng định dạng.
- [ ] Tách bước build formula, solve, decode và validate để đo riêng thời gian encoding và solve.

### 3.3 Binary MaxSAT

- [ ] Cài binary representation theo Fig. 4 constraints (1′)–(11′), gồm trọng số bit và PB constraints so sánh tổng power với peak.
- [ ] Xử lý chính xác số bit cần dùng và bit-pattern ngoài miền `[LB, UB]`; bảo đảm nghiệm MaxSAT biểu diễn giá trị peak hợp lệ.
- [ ] Giải mã peak và schedule, sau đó đối chiếu objective với validator độc lập.
- [ ] Trên toy/pilot, so sánh unary và binary về status, optimum, số biến, số clause, runtime và memory.

### 3.4 Kiểm chứng encoding

- [ ] Review mapping với thành viên khác; kiểm tra từng ràng buộc ở các giá trị biên và chiều implication.
- [ ] So sánh SAT/MaxSAT result với vét cạn cho instance cực nhỏ và với validator độc lập.
- [ ] Thêm regression test cho peak=LB, peak=UB, power bằng nhau, chuỗi precedence, task không thể bắt đầu tại một số time unit và nhiều task cùng station.
- [ ] Ghi các khác biệt giữa paper và code, kể cả encoding PySAT hoặc cách dựng instance, thay vì mô tả là tái lập y nguyên.

**Đầu ra:** hai solver `unary` và `binary` có interface/result schema giống nhau và có kiểm chứng trên instance nhỏ.

## 4. Xây dựng exact baselines

- [ ] Chốt cùng biến thể SALB3PM, schema, dữ liệu, timeout và cách đo cho mọi baseline.
- [ ] Cài CP-SAT bằng OR-Tools; mô hình hóa station/start/active và peak, rồi kiểm tra schedule bằng validator chung.
- [ ] Cài CPLEX MIP và Gurobi MIP bằng API phù hợp; ghi rõ phiên bản, objective, bounds và gap.
- [ ] Cài CPLEX CP/CP Optimizer nếu máy và license cho phép; phân biệt API `docplex` với solver thực sự được cài.
- [ ] Kiểm tra trạng thái license riêng trước benchmark; ghi `NOT_RUN` và lý do khi thiếu solver/license, không ghi thành timeout.
- [ ] So sánh từng baseline trên toy instances trước; xác nhận objective và feasibility khớp validator/MaxSAT.

## 5. CLI, experiment runner và result schema

- [ ] Bổ sung lệnh CLI để validate instance, solve bằng model đã chọn, chạy một instance và chạy batch benchmark.
- [ ] Result record tối thiểu: instance/dataset ID, model/solver, version, encoding settings, seed, status, objective, best bound/gap, build time, solve time, total time, memory nếu có, command, commit hash và error/license note.
- [ ] Chuẩn hóa status: `OPTIMAL`, `FEASIBLE`, `UNSAT`, `TIMEOUT`, `ERROR`, `NOT_RUN`; không biến timeout/license error thành objective giả.
- [ ] Hỗ trợ timeout có kiểm soát, ghi thời gian đơn vị thống nhất, log riêng theo run; tránh chạy đồng thời làm nhiễu so sánh nếu tài nguyên dùng chung.
- [ ] Cho runner dừng/tiếp tục an toàn, không ghi đè raw results; mỗi lần chạy dùng output path hoặc experiment ID riêng.
- [ ] Thêm test cho parser kết quả, status normalization, timeout và validator của kết quả solver.

## 6. Pilot, benchmark chính và protocol công bằng

- [ ] Chạy smoke trên Figure 1 và toy suite; sửa encoding trước khi tiêu tốn thời gian benchmark.
- [ ] Pilot trên một vài graph nhỏ/vừa/lớn và power seeds để ước lượng runtime, lỗi parser, memory và thời hạn khả thi.
- [ ] Chốt số lần lặp, seed list, timeout, phần cứng, phiên bản solver, thread count và tiêu chí dừng trước batch chính; nêu khác biệt với paper (paper dùng cutoff 3600 giây).
- [ ] So sánh hai MaxSAT models trên cùng instance, cùng seed và cùng hardware; chạy các baseline trên cùng tập subset khả thi.
- [ ] Chạy benchmark chính theo family và kích thước; nếu không đủ tài nguyên cho toàn bộ, công bố rõ subset và cách chọn, không chỉ chọn các instance dễ.
- [ ] Lưu toàn bộ raw CSV/JSON và logs trong `results/`; giữ lệnh, config, commit, manifest dataset và trạng thái kể cả khi solver không chạy.
- [ ] Tính median/mean phù hợp phân phối runtime, số optimum, timeout, objective gap, model size và thời gian; không xóa các lần fail khỏi mẫu.
- [ ] Chạy lại các kết quả bất thường và xác minh mọi nghiệm bằng validator độc lập trước khi tổng hợp.

## 7. Phân tích và trực quan hóa

- [ ] Viết script tạo bảng tổng hợp từ raw results; không nhập tay số trong manuscript.
- [ ] Dùng `cnsplots` theo yêu cầu môn học để vẽ runtime/quality comparison, biểu đồ log-scale khi cần, và biểu đồ cumulative solved instances nếu phù hợp.
- [ ] Gắn nhãn timeout, `NOT_RUN`, license error và missing values đúng ngữ nghĩa; không vẽ missing thành runtime bằng 0.
- [ ] Lưu script/cấu hình, hình xuất và chỉ rõ dữ liệu đầu vào để tái tạo từng figure/table.
- [ ] Kiểm tra caption, đơn vị, tên trục, thứ tự solver và quy tắc làm tròn thống nhất giữa chart, table và text.

## 8. Hoàn thiện báo cáo và phát hành

- [ ] Điền tác giả, cơ quan, email, abstract và keywords vào [report/manuscript.tex](report/manuscript.tex); xóa mọi placeholder/TODO trước bản nộp.
- [ ] Viết problem definition, encoding, exact baselines, dataset provenance, experimental protocol, results, limitations và conclusion dựa trên code/data đã kiểm tra.
- [ ] Trích dẫn paper chủ đề, SALBP dataset gốc, PySAT, solver và benchmark nguồn; kiểm tra mọi citation có entry trong `references.bib`.
- [ ] Tạo figure/table từ raw results; kiểm tra PDF cuối, references, lỗi/undefined citation và các TODO còn sót.
- [ ] Điền URL GitHub thật vào Data Availability; kiểm tra repository clone được và hướng dẫn setup chạy từ môi trường sạch.
- [ ] Ghi các giới hạn license/hardware, phương pháp không chạy được, random seeds, cutoff và phạm vi dữ liệu.
- [ ] Review chéo toàn bài; so khớp mọi con số giữa PDF, CSV, log và commit.

## Definition of done

- [ ] Dataset có nguồn/phiên bản/checksum/giấy phép và tái tạo được từ script.
- [ ] Validator độc lập xác nhận schedule và objective của mọi kết quả được báo cáo.
- [ ] Unary/binary và baseline có cùng contract, chạy được ít nhất trên fixture và pilot; test suite/CI chạy thành công.
- [ ] Raw results và figures có thể tái tạo bằng lệnh/configuration đã lưu.
- [ ] README, experiment protocol, implementation plan và manuscript mô tả nhất quán trạng thái thực tế.
- [ ] Không còn placeholder, số liệu không nguồn hoặc claim vượt quá dữ liệu trong bản nộp.

## Trạng thái hiện tại

- [x] Starter directory layout, `uv` packaging, lockfile và clone instructions
- [x] PySAT PB + RC2 environment smoke command
- [x] Elsevier CAS report template, build script và manuscript outline
- [ ] Chọn/thu thập SALBP benchmark và chốt giao thức sinh power
- [ ] Instance schema, parser và independent solution validator
- [ ] Unary MaxSAT model
- [ ] Binary MaxSAT model
- [ ] CP-SAT, CPLEX CP/MIP và Gurobi baselines
- [ ] Experiment runner, benchmark results và `cnsplots` figures
- [ ] Hoàn thiện report và tái lập từ clone sạch
