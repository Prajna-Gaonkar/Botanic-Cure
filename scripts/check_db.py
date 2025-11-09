import mysql.connector
import sys

def check_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="08*Prajna",
            database="botanic_cure"
        )
        print("✅ Successfully connected to database")
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Database connection failed: {err}")
        return None

def check_users_table(conn):
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check if table exists
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = 'botanic_cure' 
            AND TABLE_NAME = 'users'
        """)
        if not cursor.fetchone():
            print("❌ 'users' table does not exist!")
            return False
            
        # Get table structure
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        print("\nTable structure:")
        for col in columns:
            print(f"- {col['Field']}: {col['Type']}")
            
        # Count users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()['count']
        print(f"\nTotal users in database: {count}")
        
        if count > 0:
            # Show sample user (without password)
            cursor.execute("SELECT id, username, email FROM users LIMIT 1")
            sample = cursor.fetchone()
            print("\nSample user:")
            print(f"- ID: {sample['id']}")
            print(f"- Username: {sample['username']}")
            print(f"- Email: {sample['email']}")
            
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Error checking users table: {err}")
        return False
    finally:
        cursor.close()

def main():
    conn = check_db_connection()
    if conn:
        check_users_table(conn)
        conn.close()

if __name__ == "__main__":
    main()