# backend/test_connection.py
from database import get_db_connection
import sys

def test_connection():
    """Test the Supabase database connection."""
    try:
        print("Testing Supabase connection...")
        conn = get_db_connection()
        cur = conn.cursor()

        # Test query
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Connected successfully!")
        print(f"PostgreSQL version: {version[0]}")

        # Check if pgvector extension is enabled
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cur.fetchone()
        if result:
            print(f"✅ pgvector extension is enabled")
        else:
            print(f"❌ pgvector extension is NOT enabled")

        # Check if products table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'products'
            );
        """)
        table_exists = cur.fetchone()[0]
        if table_exists:
            print(f"✅ products table exists")
        else:
            print(f"❌ products table does NOT exist")

        cur.close()
        conn.close()

        print("\n🎉 All checks passed! Database is ready.")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
