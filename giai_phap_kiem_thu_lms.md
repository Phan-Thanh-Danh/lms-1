# Giải Pháp Kiểm Thử Tự Động - Dự Án Frappe LMS

Tài liệu này trình bày chi tiết về kiến trúc, công cụ và chiến lược thực thi của giải pháp kiểm thử tự động được áp dụng cho dự án Frappe LMS. Giải pháp được thiết kế nhằm đảm bảo chất lượng phần mềm xuyên suốt quá trình phát triển, đồng thời tối ưu hóa thời gian chạy test đáp ứng quy trình CI/CD hiện đại.

---

## 1. Kiến Trúc Tổng Thể & Công Cụ (Tech Stack)

Hệ thống Automation Test của dự án được xây dựng trên nền tảng Python, tận dụng sức mạnh của các thư viện mã nguồn mở hàng đầu:

*   **Core Framework - Pytest:** Đóng vai trò là Test Runner chính. Dự án sử dụng mạnh mẽ các tính năng nâng cao của Pytest như:
    *   **Fixtures:** Khởi tạo và dọn dẹp môi trường (setup/teardown) như khởi tạo Browser, login API, chuẩn bị dummy data.
    *   **Markers:** Phân loại và gom nhóm (tagging) các test case để chạy theo từng kịch bản cụ thể.
    *   **Hooks:** Can thiệp sâu vào vòng đời chạy test (ví dụ: chụp ảnh khi fail).
*   **Web Automation - Selenium WebDriver:** Tương tác trực tiếp với giao diện người dùng trên trình duyệt (thực hiện click, điền form, xác thực DOM).
*   **Quản lý Web Driver - Webdriver Manager:** Tự động tải xuống và quản lý các file thực thi của trình duyệt (Chrome/Chromium), loại bỏ việc cài đặt driver thủ công.
*   **Cấu trúc dự án (Project Structure):**
    *   `conftest.py`: "Trái tim" của framework cấu hình Pytest nền tảng, định nghĩa Fixtures, Options và Hooks.
    *   `helpers.py`: Tách biệt các hàm tương tác UI dùng chung (wait, login, navigate) ra khỏi logic của test case (hướng tiếp cận tương đồng với Page Object Model).
    *   Các kịch bản thực thi dạng Batch/Bash script (`run_quick`, `run_smoke`) cho đa nền tảng (Windows, Linux, WSL).

---

## 2. Chiến Lược Phân Tầng Kiểm Thử (Test Suites Strategy)

Thay vì gom tất cả các test case thành một bộ nguyên khối chạy chậm chạp, dự án áp dụng chiến lược đa tầng (Multi-tier Strategy). Việc này giúp các lập trình viên có thể nhận feedback liên tục mà không phải chờ đợi quá lâu.

| Tên Bộ Test / Marker | Mục Đích Kinh Doanh | Đặc Điểm Kỹ Thuật | Thời gian kỳ vọng |
| :--- | :--- | :--- | :--- |
| **Quick Suite** <br/>`@pytest.mark.quick` | Kiểm tra hồi quy hàng ngày (Daily Regression). Đảm bảo kết nối và các luồng sống còn (Login, Tạo user) không bị sập. | Tốc độ thực thi cực nhanh, tuyệt đối không dùng Seed Data gây tốn tài nguyên. | Rất nhanh (< 1p) |
| **Smoke Suite** <br/>`@pytest.mark.smoke` | Tính bao phủ (Coverage) rộng hơn. Kiểm tra tính sẵn sàng của các Module cốt lõi trước/sau khi Release. | Tự động đi qua các trang chính, kiểm tra hiển thị trên Mobile, kiểm tra Badge... | Nhanh (~ 2-3p) |
| **UI Phase 1** <br/>`@pytest.mark.ui_phase1` | Kiểm thử giao diện tĩnh và các tính năng không trạng thái (Stateless E2E). | Chạy **song song đa luồng** (Parallel) qua xdist. Tập trung vào Validate hiển thị UI components. | Nhanh (chạy đa luồng) |
| **UI Phase 2** <br/>`@pytest.mark.ui_phase2` | Kiểm thử luồng nghiệp vụ phức tạp từ người dùng thật (Ghi danh > Học > Thi > Nộp bài > Nhận chứng chỉ). | Có trạng thái (Stateful). Cần bộ dữ liệu mẫu (Seed Data) chuẩn hóa được đổ vào trước khi test. | Trung bình / Lâu |

---

## 3. Các Điểm Sáng Kỹ Thuật (Technical Implementation Highlights)

Giải pháp của dự án đi theo các "Best Practices" chuẩn công nghiệp thông qua một số kỹ thuật triển khai nổi bật:

### 3.1. Tối Ưu Selenium Headless & Container-Ready
Trình duyệt được cấu hình mặc định chạy ở chế độ **Headless (ẩn giao diện)**. Không những vậy, driver được tiêm thêm các tùy chọn tối ưu hóa sâu:
*   `--disable-gpu`, `--no-sandbox`, `--disable-dev-shm-usage`: Tối ưu RAM, vô hiệu hoạ Sandbox để đảm bảo chạy mượt mà ngay cả khi đặt trong Docker Container hoặc môi trường cấp phát tài nguyên thấp như CI/CD pipelines.

### 3.2. Chạy Song Song (Parallel Execution) Để Giảm Thời Gian
Với bộ test UI Phase 1, dự án áp dụng `pytest-xdist` (`-n auto`) để tung các test case ra chạy đồng thời trên nhiều luồng nhân CPU. Điều này giúp đẩy nhanh tốc độ kiểm thử lên cực hạn mà không bị thắt nút cổ chai ở tốc độ trình duyệt.

### 3.3. Tự Động Bắt Ảnh Chụp Màn Hình (Auto-Screenshot on Failure)
Tại `conftest.py`, hệ thống sử dụng hook `pytest_runtest_makereport` để lắng nghe kết quả. Bất cứ khi nào một test case xảy ra lỗi (AssertionError, TimeoutException...), trình duyệt sẽ tự động chụp lại trạng thái màn hình hiện tại và lưu vào `artifacts/screenshots/`. Điều này cung cấp bằng chứng trực quan, hỗ trợ fix bug nhanh chóng.

### 3.4. Dummy Data Generation & Lock Files
*   **Dữ liệu ảo hóa:** Hệ thống dùng Python để tự sinh ra file PDF lỗi ảo, file Image dung lượng cực nhỏ (Tiny PNG), file .exe... đưa vào Fixtures nhằm mục đích test các giới hạn upload dung lượng, sai định dạng mà không cần lưu trữ file rác cứng ở trong hệ thống mã nguồn.
*   **Seed Lock:** Khi chạy đa luồng, việc tạo ra `seed_data.lock` giúp ngăn ngừa tình trạng hai luồng thi nhau gọi tạo dữ liệu đồng bộ làm gián đoạn và ô nhiễm Database.

---

## 4. Hệ Thống Báo Cáo Chuyên Nghiệp (Reporting)

Kiểm thử tự động sẽ trở nên vô nghĩa nếu không có báo cáo tốt. Dự án tích hợp thư viện `pytest-html` để xuất bản kết quả:

1.  **Giao diện trực quan:** Cung cấp file HTML (ví dụ `quick_testcase_report.html`) đánh giá được tỉ lệ Pass/Fail một cách trực quan, đầy đủ Stack Trace lỗi.
2.  **Thông tin Metadata:** Nhúng các thông tin về môi trường chạy (Base URL thực tế kết nối, phiên bản Python, trạng thái Headless).
3.  **Tích hợp bằng chứng:** Hình ảnh chụp tự động tại bước 3.3 tự động được cắm thẳng vào báo cáo HTML giúp Project Manager và Developer đối chiếu ngay tức thì.
4.  **Tương thích CI:** Sinh ra file chuẩn định dạng `junitxml` giúp các hệ thống bên thứ 3 (như Jenkins, GitLab, Azure DevOps) parse kết quả và vẽ thành biểu đồ đo lường chất lượng dự án.

---

## 5. Kết Luận
Cấu trúc Automation cho LMS hiện tại là một giải pháp trưởng thành. Nó thỏa mãn 3 yếu tố quan trọng:
- **Tính chính xác:** Kịch bản sát với luồng kinh doanh (Stateful Flow).
- **Tính tốc độ:** Quy hoạch các bộ test (Quick/Smoke) và chạy song song đa luồng.
- **Tính minh bạch:** Cung cấp ảnh lỗi và báo cáo HTML trực quan.
