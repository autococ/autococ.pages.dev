# Checklist trước khi bán thật

- [ ] Đăng ký tên miền và hosting/VPS.
- [ ] Cấu hình HTTPS.
- [ ] Đổi SECRET_KEY và ADMIN_PASSWORD bằng chuỗi ngẫu nhiên mạnh.
- [ ] Tích hợp MoMo merchant thật theo tài liệu API được cấp.
- [ ] Xác minh IPN bằng chữ ký và đối soát số tiền/mã đơn.
- [ ] Không cấp key chỉ dựa vào trang redirect của trình duyệt.
- [ ] Thêm CSRF protection, rate limiting, audit log và backup.
- [ ] Kiểm thử kích hoạt, hết hạn, khóa key, giới hạn thiết bị.
- [ ] Build, kiểm thử và ký số EXE.
- [ ] Công bố chính sách bảo mật, điều khoản, hoàn tiền và hỗ trợ.
