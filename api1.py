from flask import Flask, jsonify, request
from flask_cors import CORS
import pyodbc
import datetime

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
            cursor.execute("SELECT * FROM Account WHERE tenDangNhap = ? AND matKhau = ?", username, password)
            row = cursor.fetchone()
            if row:
                return jsonify({"success": True, "message": "Đăng nhập thành công"}), 200
            else:
                return jsonify({"success": False, "message": "Sai tài khoản hoặc mật khẩu"}), 401
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

            # 1. Tạo idKhachHang tự động
            cursor.execute("SELECT COUNT(*) FROM KhachHang")
            kh_count = cursor.fetchone()[0]
            new_kh_id = f"KH{kh_count + 1:03}"

            # 2. Thêm vào bảng KhachHang
            cursor.execute(
                "INSERT INTO KhachHang (idKhachHang, Ten, sdt, idAccount) VALUES (?, ?, ?, ?)",
                new_kh_id, ten, sdt, "AC002"
            )

            # 3. Tìm bàn trống
            cursor.execute("SELECT TOP 1 idBan FROM Ban WHERE trangThai = N'Trống'")
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Không còn bàn trống"}), 400
            idBan = row[0]

            # 4. Tạo id đặt bàn
            cursor.execute("SELECT COUNT(*) FROM DatBan")
            count = cursor.fetchone()[0]
            idDatBan = f"DB{count + 1:03}"

            # 5. Thêm vào bảng DatBan
            cursor.execute(
                """
                INSERT INTO DatBan (idDatBan, idBan, ngayDat, gioDat, trangThaiDat, idKhachHang)
                VALUES (?, ?, ?, ?, N'Đã đặt', ?)
                """,
                idDatBan, idBan, ngay, gio, new_kh_id
            )

            # 6. Thêm vào bảng DatBanOnline
            cursor.execute(
                """
                INSERT INTO DatBanOnline (idDatBanOnline, tenKhachHang, email, soDienThoai,
                ngayDat, gioDat, soNguoi, ghiChu, trangThai, ngayGui)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, N'Chưa xử lý', ?)
                """,
                idDatBan, ten, email, sdt, ngay, gio, soNguoi, ghiChu, datetime.datetime.now()
            )

            # 7. Cập nhật trạng thái bàn
            cursor.execute(
                "UPDATE Ban SET trangThai = N'Đặt trước' WHERE idBan = ?",
                idBan
            )

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
            for r in cursor.fetchall():
                ngay = r[3]
                gio = r[4]

                ngay_str = ngay.strftime('%Y-%m-%d') if isinstance(ngay, datetime.date) else str(ngay)
                gio_str = gio.strftime('%H:%M') if isinstance(gio, datetime.time) else str(gio)[:5]

                results.append({
                    'id': r[0],
                    'ban': r[1],
                    'tenKhach': r[2],
                    'ngay': ngay_str,
                    'gio': gio_str,
                    'trangThai': r[5]
                })
            return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



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
                    ngayLap = datetime.datetime.strptime(ngayLap, "%Y-%m-%d")

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


if __name__ == '__main__':
    print("✅ Flask server is running at http://localhost:5000")
    app.run(debug=True)