import psycopg2
import traceback

def migrate():
    conn_str = "postgresql://postgres:123456@localhost:5432/viveres_app"
    try:
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()

        print("[1/2] Checking/adding is_delivery column to providers table...")
        cur.execute("""
            ALTER TABLE providers 
            ADD COLUMN IF NOT EXISTS is_delivery BOOLEAN DEFAULT FALSE;
        """)

        print("[2/2] Setting cost_usd in deliveries as nullable...")
        cur.execute("""
            ALTER TABLE deliveries
            ALTER COLUMN cost_usd DROP NOT NULL;
        """)

        conn.commit()
        print("All migrations applied successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print("Error during migration:", repr(e))
        traceback.print_exc()

if __name__ == "__main__":
    migrate()
