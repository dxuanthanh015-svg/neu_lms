import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'lms_m10')

def get_database_uri():
    # Kiem tra ket noi MySQL
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=2
        )
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()
        uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        print(f"[*] Ket noi MySQL thanh cong: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return uri, True
    except Exception as e:
        print(f"[!] Chua the ket noi MySQL (loi: {type(e).__name__}). Dang dung SQLite (lms_m10.db) de dam bao he thong luon khoi chay.")
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        sqlite_path = os.path.join(basedir, 'lms_m10.db')
        return f"sqlite:///{sqlite_path}", False

DATABASE_URI, IS_MYSQL = get_database_uri()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'lms_m10_dev_secret_key')
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    IS_MYSQL = IS_MYSQL
    TEMPLATES_AUTO_RELOAD = True
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '').strip()
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b').strip()
