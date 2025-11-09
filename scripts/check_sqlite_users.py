from sqlite3 import connect
import os

def get_users():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'users.db')
    if not os.path.exists(db_path):
        print("Database file not found at:", db_path)
        return
        
    conn = connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, email, phone, is_verified FROM user")
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the database.")
            return
            
        print("\nRegistered Users:")
        print("=" * 80)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Phone':<15} {'Verified':<8}")
        print("-" * 80)
        
        for user in users:
            print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {user[3]:<15} {user[4]:<8}")
            
    except Exception as e:
        print("Error reading from database:", str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    get_users()