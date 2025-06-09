from flask import Flask, jsonify, request
from flask_cors import CORS
import pyodbc
import datetime
from datetime import time, date,datetime,timedelta
from dateutil import parser

app = Flask(__name__)
CORS(app)

# Ham lay ket noi moi moi lan goi
def get_connection():
    return pyodbc.connect(
        r"Driver={SQL Server};"
        r"Server=DESKTOP-3KJNUII\SQLEXPRESS;"
        r"Database=QuanLyCafe;"
        r"Trusted_Connection=yes;"
    )

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT A.idAccount, A.loaiTaiKhoan, KH.Ten, KH.sdt
                FROM Account A
                JOIN KhachHang KH ON KH.idAccount = A.idAccount
                WHERE A.tenDangNhap = ? AND A.matKhau = ?
            """, username, password)
            row = cursor.fetchone()
            if row:
                return jsonify({
                    "success": True,
                    "message": "Đăng nhập thành công",
                    "userId": row[0],
                    "role": row[1],  # ví dụ: 'admin' hoặc 'user'
                    "ten": row[2],     # 👈 Trả về tên người dùng
                    "sdt": row[3]      # 👈 Trả về số điện thoại
                }), 200
            else:
                return jsonify({"success": False, "message": "Sai tài khoản hoặc mật khẩu"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/dangky', methods=['POST'])
def dang_ky():
    data = request.get_json()
    tenDangNhap = data.get("username")
    matKhau = data.get("password")
    ten = data.get("hoTen")
    sdt = data.get("sdt")
    loaiTaiKhoan = data.get("loaiTaiKhoan", "user")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 🔒 Kiểm tra trùng tên đăng nhập
            cursor.execute("SELECT COUNT(*) FROM Account WHERE tenDangNhap = ?", tenDangNhap)
            if cursor.fetchone()[0] > 0:
                return jsonify({"success": False, "message": "Tên đăng nhập đã tồn tại"}), 400

            # ✅ Sinh idAccount kiểu AC001, AC002,...
            cursor.execute("SELECT idAccount FROM Account")
            account_rows = cursor.fetchall()
            account_ids = [int(row[0][2:]) for row in account_rows if row[0].startswith("AC")]
            new_account_number = max(account_ids) + 1 if account_ids else 1
            idAccount = f"AC{new_account_number:03d}"

            # ✅ Thêm vào bảng Account
            cursor.execute("""
                INSERT INTO Account (idAccount, tenDangNhap, matKhau, loaiTaiKhoan)
                VALUES (?, ?, ?, ?)
            """, idAccount, tenDangNhap, matKhau, loaiTaiKhoan)

            # ✅ Sinh idKhachHang kiểu KH001, KH002,...
            cursor.execute("SELECT idKhachHang FROM KhachHang")
            kh_rows = cursor.fetchall()
            kh_ids = [int(row[0][2:]) for row in kh_rows if row[0].startswith("KH")]
            new_kh_number = max(kh_ids) + 1 if kh_ids else 1
            idKhachHang = f"KH{new_kh_number:03d}"

            # ✅ Thêm vào bảng KhachHang
            cursor.execute("""
                INSERT INTO KhachHang (idKhachHang, sdt, Ten, idAccount)
                VALUES (?, ?, ?, ?)
            """, idKhachHang, sdt, ten, idAccount)

            conn.commit()
            return jsonify({"success": True, "message": "Đăng ký thành công"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/phanquyen', methods=['GET'])
def phan_quyen():
    user_id = request.args.get("id")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT loaiTaiKhoan FROM Account WHERE idAccount = ?", user_id)
            row = cursor.fetchone()
            if row:
                return jsonify({"success": True, "role": row[0]}), 200
            else:
                return jsonify({"success": False, "message": "Không tìm thấy tài khoản"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ✅ API: lấy toàn bộ sản phẩm từ bảng ThucDon
@app.route('/api/thucdon', methods=['GET'])
def get_all_thucdon():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ThucDon")
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#API khuyến mãi
@app.route('/api/khuyenmai', methods=['GET'])
def get_all_khuyenmai():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM KhuyenMai")
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


    try:
        return datetime.strptime(gio_str, "%H:%M")  # ví dụ: '00:30'
    except ValueError:
        try:
            return datetime.strptime(gio_str, "%I:%M %p")  # ví dụ: '12:30 AM'
        except ValueError:
            try:
                gio_str = gio_str.split('.')[0]  # loại bỏ .0000000 nếu có
                return datetime.strptime(gio_str, "%H:%M:%S")
            except Exception as e:
                raise ValueError(f"❌ Không parse được giờ: {gio_str}, lỗi: {e}")
@app.route('/api/datbanonline', methods=['POST'])
def dat_ban():
    data = request.get_json()
    ten = data.get("ten")
    sdt = data.get("sdt")
    email = data.get("email")
    ngay = data.get("ngayDat")
    gio = data.get("gioDat")
    soNguoi = data.get("soNguoi")
    ghiChu = data.get("ghiChu")


    try:
        with get_connection() as conn:
            cursor = conn.cursor()


            # 1 Tìm bàn trống theo thời gian hợp lệ
            cursor.execute("SELECT idBan FROM Ban")
            all_bans = [row[0] for row in cursor.fetchall()]

            # Ghép datetime đặt mới
            gio = gio.split(":")[0] + ":" + gio.split(":")[1]  # lấy 'HH:MM' phần đầu
            gio_dat =   datetime.strptime(gio, "%H:%M")
            ngay_dat = datetime.strptime(ngay, "%Y-%m-%d").date()
            thoidiem_dat_moi = datetime.combine(ngay_dat, gio_dat.time())

            valid_ban = None
            for idBan in all_bans:
                cursor.execute("""
                    SELECT ngayDat, gioDat FROM DatBan
                    WHERE idBan = ? AND ngayDat = ?
                """, idBan, ngay)
                rows = cursor.fetchall()

                conflict = False
                for r in rows:
                    # r[0] = ngayDat, r[1] = gioDat
                    print("⏰ Giờ đã đặt:", r[1])
                    gio_str = str(r[1]).split('.')[0]  # cắt bỏ phần .0000000 nếu có
                    gio_db = datetime.strptime(f"{r[0]} {gio_str}", "%Y-%m-%d %H:%M:%S")

                    print("🆚 So với giờ mới:", thoidiem_dat_moi)
                    print("⏱ Chênh lệch:", abs((thoidiem_dat_moi - gio_db).total_seconds()))

                    if abs((thoidiem_dat_moi - gio_db).total_seconds()) < 7200:
                        conflict = True
                        print("❌ Trùng giờ với lịch:", gio_db)
                        break

                if not conflict:
                    valid_ban = idBan
                    break

            if not valid_ban:
                return jsonify({"error": "Không còn bàn nào trống vào khung giờ đó (mỗi bàn cách nhau ít nhất 2 tiếng)"}), 400
            # 2. Tạo idKhachHang tự động (kiểm tra nếu đã tồn tại thì không tạo mới)
            cursor.execute("SELECT idKhachHang FROM KhachHang WHERE sdt = ?", sdt)
            khach = cursor.fetchone()
            if khach:
                new_kh_id = khach[0]
            else:
                cursor.execute("SELECT COUNT(*) FROM KhachHang")
                kh_count = cursor.fetchone()[0]
                new_kh_id = f"KH{kh_count + 1:03}"
                cursor.execute(
                    "INSERT INTO KhachHang (idKhachHang, Ten, sdt, idAccount) VALUES (?, ?, ?, ?)",
                    new_kh_id, ten, sdt, None
                )
            # 3. Tạo id đặt bàn
            cursor.execute("SELECT COUNT(*) FROM DatBan")
            count = cursor.fetchone()[0]
            idDatBan = f"DB{count + 1:03}"

            # 4. Thêm vào DatBan
            cursor.execute("""
                INSERT INTO DatBan (idDatBan, idBan, ngayDat, gioDat, trangThaiDat, idKhachHang)
                VALUES (?, ?, ?, ?, N'Đã đặt', ?)
            """, idDatBan, valid_ban, ngay, gio, new_kh_id)

            # 5. Thêm vào bảng DatBanOnline
            cursor.execute("""
                INSERT INTO DatBanOnline (idDatBanOnline, tenKhachHang, email, soDienThoai,
                ngayDat, gioDat, soNguoi, ghiChu, trangThai, ngayGui)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, N'Chưa xử lý', ?)
            """, idDatBan, ten, email, sdt, ngay, gio, soNguoi, ghiChu, datetime.now())

            # 6. Cập nhật trạng thái bàn
            cursor.execute("UPDATE Ban SET trangThai = N'Đặt trước' WHERE idBan = ?", valid_ban)

            conn.commit()
            return jsonify({"message": "Đặt bàn thành công", "maDatBan": idDatBan}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

# API: Lấy danh mục món
@app.route('/api/danhmuc', methods=['GET'])
def get_danh_muc():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM DanhMucMon")
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: Lấy danh sách đặt bàn
@app.route('/api/datban', methods=['GET'])
def get_dat_ban():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT db.idDatBan, db.idBan, kh.Ten, db.ngayDat, db.gioDat, db.trangThaiDat
                FROM DatBan db
                JOIN KhachHang kh ON db.idKhachHang = kh.idKhachHang
            """)
            results = []
            now = datetime.now()
            two_hours_later = now + timedelta(hours=2)

            for r in cursor.fetchall():
                id, ban, ten, ngay, gio, trangThai = r

                # Convert ngày và giờ đúng định dạng
                ngay_dt = ngay if isinstance(ngay, date) else datetime.strptime(str(ngay), '%Y-%m-%d').date()
                gio_str = str(gio).split('.')[0]  # ✅ Xử lý lỗi .0000000
                gio_dt = datetime.strptime(gio_str, '%H:%M:%S').time()

                # So sánh ngày giờ
                thoiDiemDat = datetime.combine(ngay_dt, gio_dt)
                new_status = "Đã sử dụng" if thoiDiemDat < now else "Đã đặt"

                # Cập nhật trạng thái nếu cần
                if trangThai != new_status:
                    update_cursor = conn.cursor()
                    update_cursor.execute(
                        "UPDATE DatBan SET trangThaiDat = ? WHERE idDatBan = ?",
                        new_status, id
                    )
                    conn.commit()
                    trangThai = new_status

                results.append({
                    'id': id,
                    'ban': ban,
                    'tenKhach': ten,
                    'ngay': ngay_dt.strftime('%Y-%m-%d'),
                    'gio': gio_dt.strftime('%H:%M'),
                    'trangThai': trangThai
                })
            # Truy vấn các bàn hiện đang trống (không có đặt bàn hợp lệ sắp tới)
            cursor.execute("""
                SELECT b.idBan, b.tenBan
                FROM Ban b
                WHERE b.idBan NOT IN (
                    SELECT db.idBan
                    FROM DatBan db
                    WHERE 
                        db.trangThaiDat = 'Đã đặt'
                        AND (
                             CAST(db.ngayDat AS DATETIME)+ CAST(db.gioDat AS DATETIME) BETWEEN ? AND ?
                        )
                )
            """, (now,two_hours_later))

            ban_trong = [{"idBan": row[0], "tenBan": row[1]} for row in cursor.fetchall()]


            return jsonify({
                "datBan": results,
                "banTrong": ban_trong
            }), 200

    except Exception as e:
        print("🔥 LỖI API /api/datban:", e)
        return jsonify({'error': str(e)}), 500

@app.route("/api/taohoadon", methods=["POST"])
def tao_hoa_don():
    data = request.get_json()
    idBan = data.get("idBan")
    danh_sach_mon = data.get("mon", [])  # mảng nhiều món
    isKhachMoi = data.get("isKhachMoi", False)
    khachMoi = data.get("khachMoi", {})
    phuongthucThanhToan = data.get("phuongthucThanhToan", "Tiền mặt")

    if not danh_sach_mon:
        return jsonify({"error": "Danh sách món trống!"}), 400

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Xử lý khách hàng
            idKhach = None
            if isKhachMoi:
                sdt = khachMoi.get("sdt")
                ten = khachMoi.get("ten")
                cursor.execute("SELECT idKhachHang FROM KhachHang WHERE sdt = ?", sdt)
                kh = cursor.fetchone()
                if kh:
                    idKhach = kh[0]
                else:
                    cursor.execute("SELECT COUNT(*) FROM KhachHang")
                    count_kh = cursor.fetchone()[0]
                    idKhach = f"KH{count_kh + 1:03}"
                    cursor.execute("INSERT INTO KhachHang (idKhachHang, Ten, sdt, idAccount) VALUES (?, ?, ?, NULL)",
                                   idKhach, ten, sdt)
            else:
                cursor.execute("""
                    SELECT idKhachHang FROM DatBan 
                    WHERE idBan = ? AND trangThaiDat = N'Đã đặt'
                    ORDER BY ngayDat DESC, gioDat DESC
                """, idBan)
                row = cursor.fetchone()
                if row:
                    idKhach = row[0]
                else:
                    return jsonify({"error": "Không tìm thấy khách đặt trước"}), 400

            # 2. Tạo hóa đơn
            cursor.execute("SELECT COUNT(*) FROM HoaDonBan")
            count_hd = cursor.fetchone()[0]
            idHDB = f"HDB{count_hd + 1:03}"
            ngayLap = datetime.now()

            cursor.execute("""
                INSERT INTO HoaDonBan (idHDB, phuongThucThanhToan, idKhachHang, ngayLap)
                VALUES (?, ?, ?,?)
            """, idHDB, phuongthucThanhToan, idKhach, ngayLap)

            tongTien = 0

            # 3. Ghi nhiều món vào ChiTietHDB
            for mon in danh_sach_mon:
                idMon = mon.get("idMon")
                soLuong = int(mon.get("soLuong", 0))
                if soLuong <= 0:
                    continue

                # Lấy đơn giá
                cursor.execute("SELECT giaBan FROM ThucDon WHERE idMon = ?", idMon)
                gia = cursor.fetchone()
                if not gia:
                    continue  # bỏ qua nếu món không tồn tại
                gia = gia[0]
                thanhTien = gia * soLuong
                tongTien += thanhTien

                # Sinh idChiTietHDB
                cursor.execute("SELECT COUNT(*) FROM ChiTietHDB")
                count_ct = cursor.fetchone()[0]
                idChiTietHDB = f"CTHDB{count_ct + 1:03}"

                cursor.execute("""
                    INSERT INTO ChiTietHDB (idChiTietHDB, idHDB, idMon, soLuongBan, thanhTienBan)
                    VALUES (?, ?, ?, ?, ?)
                """, idChiTietHDB, idHDB, idMon, soLuong, thanhTien)

            # 4. Cập nhật tổng tiền hóa đơn nếu cần
            cursor.execute("UPDATE HoaDonBan SET tongTienBan = ? WHERE idHDB = ?", tongTien, idHDB)

            # 5. Cập nhật trạng thái bàn
            if isKhachMoi:
                cursor.execute("UPDATE Ban SET trangThai = N'Đã sử dụng' WHERE idBan = ?", idBan)
            else:
                cursor.execute("UPDATE DatBan SET trangThaiDat = N'Đã sử dụng' WHERE idBan = ?", idBan)
                cursor.execute("UPDATE Ban SET trangThai = N'Đã sử dụng' WHERE idBan = ?", idBan)

            conn.commit()
            return jsonify({"message": f"Hóa đơn {idHDB} đã được tạo.", "tongTien": tongTien}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API: Lấy danh sách món đầy đủ
@app.route('/api/thucdon_full', methods=['GET'])
def get_thucdon_full():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT td.idMon, td.tenMon, td.giaBan, td.idDanhMuc, dm.tenDanhMuc, td.GioiThieuMon
                FROM ThucDon td
                JOIN DanhMucMon dm ON td.idDanhMuc = dm.idDanhMuc
            """)
            rows = cursor.fetchall()
            result = [dict(
                idMon=row[0],
                tenMon=row[1],
                giaBan=row[2],
                idDanhMuc=row[3],
                tenDanhMuc=row[4],
                gioiThieuMon=row[5]
            ) for row in rows]
            return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: Thêm món mới
@app.route('/api/themmon', methods=['POST'])
def them_mon():
    try:
        data = request.get_json()
        idMon = data.get("idMon")
        tenMon = data.get("tenMon")
        giaBan = data.get("giaBan")
        idDanhMuc = data.get("idDanhMuc")
        gioiThieuMon = data.get("gioiThieuMon")

        if not all([idMon, tenMon, giaBan, idDanhMuc]):
            return jsonify({"error": "Thiếu thông tin bắt buộc!"}), 400

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ThucDon (idMon, tenMon, giaBan, idDanhMuc, GioiThieuMon)
                VALUES (?, ?, ?, ?, ?)
            """, idMon, tenMon, giaBan, idDanhMuc, gioiThieuMon)
            conn.commit()
            return jsonify({"message": "✅ Thêm món thành công!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API: Xóa món
@app.route('/api/xoamon/<idMon>', methods=['DELETE'])
def xoa_mon(idMon):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ThucDon WHERE idMon = ?", idMon)
            conn.commit()
            return jsonify({"message": "✅ Đã xóa món thành công!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Hàm phụ trợ

def get_idDanhMuc_by_tenDanhMuc(tenDanhMuc):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT idDanhMuc FROM DanhMucMon WHERE tenDanhMuc = ?", tenDanhMuc)
        row = cursor.fetchone()
        return row[0] if row else None

# API: Sửa món
@app.route('/api/suamon', methods=['PUT'])
def sua_mon():
    try:
        data = request.get_json()
        idMon = data.get("idMon")
        tenMon = data.get("tenMon")
        giaBan = data.get("giaBan")
        tenDanhMuc = data.get("tenDanhMuc")
        gioiThieuMon = data.get("gioiThieuMon")

        idDanhMuc = get_idDanhMuc_by_tenDanhMuc(tenDanhMuc)
        if not idDanhMuc:
            return jsonify({"error": f"Không tìm thấy danh mục '{tenDanhMuc}'"}), 400

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ThucDon
                SET tenMon = ?, giaBan = ?, idDanhMuc = ?, GioiThieuMon = ?
                WHERE idMon = ?
            """, tenMon, giaBan, idDanhMuc, gioiThieuMon, idMon)
            conn.commit()
            return jsonify({"message": "✅ Cập nhật thành công!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#thong ke
@app.route('/api/thongke/doanhthu', methods=['GET'])
def thong_ke_doanh_thu():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    hdb.idHDB, 
                    hdb.ngayLap, 
                    SUM(ct.thanhTienBan) AS tongTien
                FROM HoaDonBan hdb
                JOIN ChiTietHDB ct ON hdb.idHDB = ct.idHDB
                GROUP BY hdb.idHDB, hdb.ngayLap
            """)
            rows = cursor.fetchall()

            thongke = {
                "theoNgay": {},
                "theoThang": {},
                "theoNam": {},
                "theoQuy": {}
            }

            for idHDB, ngayLap, tongTien in rows:
                if isinstance(ngayLap, str):
                    ngayLap = datetime.strptime(ngayLap, "%Y-%m-%d")

                ngay = ngayLap.strftime("%Y-%m-%d")
                thang = ngayLap.strftime("%Y-%m")
                nam = ngayLap.year
                quy = (ngayLap.month - 1) // 3 + 1
                key_quy = f"{nam}-Q{quy}"

                # Cộng dồn doanh thu vào từng loại thống kê
                thongke["theoNgay"][ngay] = thongke["theoNgay"].get(ngay, 0) + tongTien
                thongke["theoThang"][thang] = thongke["theoThang"].get(thang, 0) + tongTien
                thongke["theoNam"][str(nam)] = thongke["theoNam"].get(str(nam), 0) + tongTien
                thongke["theoQuy"][key_quy] = thongke["theoQuy"].get(key_quy, 0) + tongTien

            return jsonify(thongke), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/donhang', methods=['POST'])
def them_don_hang():
    data = request.get_json()
    ten = data.get('ten')
    sdt = data.get('sdt')
    diachi = data.get('diaChi')
    phiShip = data.get('phiShip') or 0
    phiShip = int(phiShip)
    gioHang = data.get('gioHang')
    idAccount = data.get("idAccount")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Tính tổng tiền
            tongTien = sum(item['gia'] * item['soLuong'] for item in gioHang) + phiShip

            # Thêm vào bảng DonHang
            cursor.execute("""
                INSERT INTO DonHang (tenNguoiNhan, sdt, diaChi, phiShip, tongTien,trangThai,idAccount)
                OUTPUT INSERTED.idDonHang
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ten, sdt, diachi, phiShip, tongTien,"Chờ xác nhận",idAccount
            )
            id_don = cursor.fetchone()[0]

            # Thêm các sản phẩm vào ChiTietDonHang
            for item in gioHang:
                cursor.execute("""
                    INSERT INTO ChiTietDonHang (idDonHang, idMon, tenMon, gia, soLuong)
                    VALUES (?, ?, ?, ?, ?)""",
                    id_don, item['id'], item['ten'], item['gia'], item['soLuong']
                )

            conn.commit()

        return jsonify({"success": True, "message": "Đặt hàng thành công!"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
@app.route('/api/donhang_user/<idAccount>', methods=['GET'])
def get_donhang_user(idAccount):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT idDonHang, tenNguoiNhan, diaChi, tongTien, phiShip, trangThai
                FROM DonHang
                WHERE idAccount = ?
                ORDER BY idDonHang DESC
            """, idAccount)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    "idDonHang": row[0],
                    "ten": row[1],
                    "diaChi": row[2],
                    "tongTien": row[3],
                    "phiShip": row[4],
                    "trangThai": row[5]
                })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/api/huy_donhang/<idDonHang>', methods=['PUT'])
def huy_don_hang(idDonHang):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Chỉ cho hủy nếu đang ở trạng thái "Chờ xác nhận"
            cursor.execute("SELECT trangThai FROM DonHang WHERE idDonHang = ?", idDonHang)
            row = cursor.fetchone()
            if not row or row[0] != "Chờ xác nhận":
                return jsonify({"success": False, "message": "Không thể hủy đơn hàng này."}), 400

            cursor.execute("UPDATE DonHang SET trangThai = 'Đã hủy' WHERE idDonHang = ?", idDonHang)
            conn.commit()
        return jsonify({"success": True, "message": "Đã hủy đơn hàng."}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/donhang/cho_duyet", methods=["GET"])
def lay_don_hang_cho_duyet():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT idDonHang, tenNguoiNhan, sdt, diaChi, tongTien, trangThai
                FROM DonHang
                WHERE trangThai = N'Chờ xác nhận'
            """)
            rows = cursor.fetchall()
            result = [{
                "idDonHang": r[0],
                "ten": r[1],
                "sdt": r[2],
                "diaChi": r[3],
                "tongTien": r[4],
                "trangThai": r[5]
            } for r in rows]
            return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/duyet_donhang/<idDonHang>", methods=["PUT"])
def duyet_don_hang(idDonHang):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE DonHang SET trangThai = N'Đã xác nhận' 
                WHERE idDonHang = ? AND trangThai = N'Chờ xác nhận'
            """, (idDonHang,))
            conn.commit()
            return jsonify({"message": "Đơn hàng đã được duyệt!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/nhan_hang/<idDonHang>", methods=["PUT"])
def nhan_hang(idDonHang):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Cập nhật trạng thái đơn hàng thành "Đã hoàn thành"
            cursor.execute("""
                UPDATE DonHang
                SET trangThai = N'Đã hoàn thành'
                WHERE idDonHang = ?
            """, idDonHang)

            # Thêm vào bảng HoaDonBan
            cursor.execute("SELECT idAccount, tongTien FROM DonHang WHERE idDonHang = ?", idDonHang)
            info = cursor.fetchone()
            if not info:
                return jsonify({"error": "Không tìm thấy đơn hàng"}), 404
            idAccount, tongTien = info

            cursor.execute("SELECT COUNT(*) FROM HoaDonBan")
            count = cursor.fetchone()[0]
            idHDB = f"HDB{count + 1:03}"
            ngayLap = datetime.now()

            cursor.execute("""
                INSERT INTO HoaDonBan (idHDB, idKhachHang, tongTienBan, ngayLap)
                VALUES (?, ?, ?, ?)
            """, idHDB, idAccount, tongTien, ngayLap)

            conn.commit()
            return jsonify({"message": "Đơn hàng đã được chuyển sang trạng thái hoàn thành và lưu vào hóa đơn bán."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("✅ Flask server is running at http://localhost:5000")
    app.run(debug=True)