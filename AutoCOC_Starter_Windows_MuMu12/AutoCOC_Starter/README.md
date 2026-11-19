# Auto COC – Website + License Server + Windows App (starter)

Bộ mã nguồn khởi đầu cho thương hiệu **Auto COC**, hướng tới Windows 11 + MuMu Player 12.

## Có gì trong bộ này
- Website giới thiệu sản phẩm, hiển thị 4 gói key và trang kích hoạt.
- Backend Flask + SQLite: tạo đơn hàng, phát hành key sau khi admin xác nhận thanh toán, xác thực/gia hạn/thu hồi key.
- Trang quản trị có đăng nhập, xem đơn, xác nhận thanh toán thủ công, cấp key, khóa key.
- Tích hợp MoMo ở dạng **khung tích hợp**: cần tài khoản doanh nghiệp MoMo, partnerCode/accessKey/secretKey và cấu hình IPN/return URL trước khi bật thanh toán thật.
- Ứng dụng Windows dạng Tkinter: nhập key, xác thực với server, kiểm tra phiên bản mới và mở trang tính toán tường.
- Không bao gồm bot tự động thao tác/đánh trận trong Clash of Clans. Các hành vi bot có thể vi phạm điều khoản trò chơi và gây rủi ro khóa tài khoản. Ứng dụng hiện là license client + tiện ích tính toán.

## Yêu cầu
- Python 3.11+
- Windows 10/11 hoặc máy chủ Linux
- Kết nối HTTPS và tên miền khi triển khai thật

## Chạy thử trên máy Windows
```powershell
cd server
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
py app.py
```
Mở `http://127.0.0.1:5000`.

Tài khoản admin mặc định chỉ được tạo từ biến môi trường `ADMIN_USERNAME` và `ADMIN_PASSWORD`. Hãy đặt mật khẩu mạnh trước khi chạy.

## Chạy ứng dụng desktop
Mở terminal ở thư mục gốc:
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r desktop/requirements.txt
py desktop/main.py
```
Đặt `AUTOCOC_API_URL` trong `desktop/config.json` thành URL server của bạn. Mặc định là `http://127.0.0.1:5000`.

## Tạo file EXE
```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name AutoCOC desktop/main.py
```
EXE nằm trong `dist/AutoCOC.exe`. Nên ký số code signing khi phát hành công khai.

## MoMo – bắt buộc hoàn tất trước khi nhận tiền
1. Đăng ký MoMo Payment for Business và lấy thông tin tích hợp từ MoMo.
2. Điền biến môi trường trong `.env`: `MOMO_PARTNER_CODE`, `MOMO_ACCESS_KEY`, `MOMO_SECRET_KEY`, `MOMO_ENDPOINT`, `MOMO_REDIRECT_URL`, `MOMO_IPN_URL`.
3. Hoàn thiện hàm ký HMAC-SHA256 theo đúng tài liệu phiên bản API mà MoMo cấp cho merchant. Không tự dùng thông tin mẫu để nhận tiền thật.
4. Cấu hình IPN HTTPS, xác minh chữ ký, kiểm tra amount/orderId/requestId và chống xử lý webhook trùng lặp.
5. Chạy sandbox trước, sau đó mới chuyển production.

Trong bản starter này, checkout tạo đơn ở trạng thái `pending`; website hiển thị hướng dẫn admin xác nhận chuyển khoản. Không giả lập giao dịch MoMo thành công.

## Bảo mật trước khi đưa lên mạng
- Bắt buộc HTTPS, reverse proxy, firewall.
- Đổi `SECRET_KEY`, mật khẩu admin và khóa MoMo.
- Không commit `.env` hoặc database production lên Git.
- Bật rate limit, CSRF, audit log, backup DB và giám sát.
- Chỉ cấp key sau khi xác minh thanh toán từ IPN hợp lệ hoặc đối soát merchant.
- Giới hạn thiết bị, chính sách hoàn tiền và điều khoản sử dụng cần được công bố rõ.

## Gói key mặc định
- 7 ngày: 29.000đ
- 30 ngày: 79.000đ
- 90 ngày: 189.000đ
- Vĩnh viễn: 499.000đ

Giá chỉ là giá mẫu có thể chỉnh trong `server/app.py`.
