import oracledb
import psycopg2

USER = "SYSTEM"
PASSWORD = "admin123456" 
DSN = "localhost:1521/FREEPDB1"

def get_connection():
    # oracledb is the modern driver for Oracle 26ai
    conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
    return conn


def getConnectionPostgreCloud():
    # 1. Try the Cloud first
    try:
        url = "postgresql://neondb_owner:npg_tA4kblqDgwi6@ep-spring-tooth-aijb08o0-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
        # We add a timeout so it doesn't wait forever if internet is slow
        conn = psycopg2.connect(url)
        # print(">>> Connected to NEON CLOUD")
        return conn
    
    # 2. If Cloud fails (no internet or server down), use Local
    except psycopg2.OperationalError:
        # print(">>> Internet/Cloud unavailable. Switching to LOCAL database...")
        return psycopg2.connect(
            dbname="demodatabase",
            user="postgres",
            password="admin123456",
            host="localhost",
            port="5432"
        )
