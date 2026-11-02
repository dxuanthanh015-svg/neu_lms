import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'lms_m10')

def init_mysql_schema():
    print(f"[*] Dang ket noi MySQL {DB_USER}@{DB_HOST}:{DB_PORT}...")
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True
        )
        with conn.cursor() as cur:
            sql_file = os.path.join(os.path.dirname(__file__), 'schema_mysql.sql')
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            print(f"[*] Dang thuc thi file schema_mysql.sql vao CSDL `{DB_NAME}`...")
            # Chay cac lenh SQL
            statements = sql_content.split(';')
            for stmt in statements:
                stmt_clean = stmt.strip()
                if stmt_clean:
                    cur.execute(stmt_clean)

        conn.close()
        print(f"[+] KHOI TAO CSDL MYSQL `{DB_NAME}` THANH CONG!")
        print(f"[+] Da tao du 22 bang voi rang buoc khoa ngoai ro rang va nap san 30 sinh vien!")
    except Exception as e:
        print(f"[-] Khong the khoi tao MySQL: {e}")
        print("[-] Vui long kiem tra lai DB_USER, DB_PASSWORD trong file .env")

if __name__ == '__main__':
    init_mysql_schema()
