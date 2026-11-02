import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("\n=======================================================")
    print("HOC VIEN LMS - PHAN HE M10: KHAO THI SO & HOC LIEU")
    print(f"Server dang chay tai: http://127.0.0.1:{port}")
    print(f"Cổng Đăng nhập & RBAC:   http://127.0.0.1:{port}/login")
    print(f"Giao diện chuẩn M10.G1:  http://127.0.0.1:{port}/curriculum")
    print(f"Quản lý Lớp & Sinh viên: http://127.0.0.1:{port}/students")
    print(f"Ngan hang AI EduLLM:     http://127.0.0.1:{port}/questions")
    print(f"Phe duyet Hoc lieu M1:   http://127.0.0.1:{port}/approvals")
    print("=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=True)
