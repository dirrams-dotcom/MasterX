import os, sqlite3, shutil, requests
from kivy.utils import platform
from kivy.app import App

class Database:
    def __init__(self):
        self.db_name = "managuru.db"
        self.db_path = None
        self.cloud_url = "https://myguru-app-default-rtdb.firebaseio.com/"

    def get_path(self):
        if self.db_path:
            return self.db_path

        if platform == 'android' or 'PYTHON_SERVICE_ARGUMENT' in os.environ:
            data_dir = App.get_running_app().user_data_dir
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            self.db_path = os.path.join(data_dir, self.db_name)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, self.db_name)

        return self.db_path

    def get_connection(self):
        try:
            conn = sqlite3.connect(self.get_path())
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError as e:
            print(f"Connection Error: {e}")
            return sqlite3.connect(self.db_name)

    def setup_db(self, *args):
        create_commands = [
            """CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT, role TEXT, is_verified INTEGER DEFAULT 0, verification_code TEXT, credits INTEGER DEFAULT 0, referral_code TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS student_profiles (email TEXT PRIMARY KEY, name TEXT, phone TEXT, house_no TEXT, street TEXT, landmark TEXT, area TEXT, city TEXT, pincode TEXT, class TEXT, subjects TEXT, aadhar_path TEXT, status TEXT DEFAULT 'pending')""",
            """CREATE TABLE IF NOT EXISTS tutor_profiles (email TEXT PRIMARY KEY, name TEXT, phone TEXT, area TEXT, city TEXT, landmark TEXT, house_no TEXT, street TEXT, pincode TEXT, subjects TEXT, qualification TEXT, experience TEXT, tuition_mode TEXT, aadhar_path TEXT, status TEXT DEFAULT 'pending')""",
            """CREATE TABLE IF NOT EXISTS credit_purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, amount REAL, status TEXT DEFAULT 'pending', request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, utr TEXT)""",
            """CREATE TABLE IF NOT EXISTS credit_usage_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, target_name TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS admin_broadcasts (id INTEGER PRIMARY KEY AUTOINCREMENT, target_role TEXT, message_text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
        ]
        try:
            with self.get_connection() as conn:
                for cmd in create_commands:
                    conn.execute(cmd)

                for table in ["student_profiles", "tutor_profiles"]:
                    cols = ["house_no", "street", "landmark", "city", "pincode", "class", "subjects", "aadhar_path"]
                    for col in cols:
                        try:
                            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
                        except:
                            pass
                conn.commit()
            self.create_default_admin()
            print("--- DATABASE SETUP COMPLETE ---")
        except Exception as e:
            print(f"DB Setup Error: {e}")

    # --- NEW METHOD FIXED INDENTATION ---
    def update_credit_cloud(self, email, new_credits):
        """Updates the credit count in Firebase for a specific student."""
        try:
            clean_email = email.replace('.', '_')
            # Using PATCH with a dictionary to fix the 400 error
            url = f"{self.cloud_url}student_profiles/{clean_email}.json"
            data = {"credits": int(new_credits)}
            response = requests.patch(url, json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Credit Sync Error: {e}")
            return False

    def create_default_admin(self):
        existing = self.query("SELECT * FROM users WHERE role='admin'", fetchone=True)
        if not existing:
            self.query("INSERT INTO users (email, password, role, is_verified) VALUES (?, ?, 'admin', 1)",
                       ("admin@gmail.com", "admin123"))
            print("--- DEFAULT ADMIN CREATED ---")

    def get_all_from_cloud(self, table):
        try:
            url = f"{self.cloud_url}{table}.json"
            response = requests.get(url)
            return response.json() if response.status_code == 200 and response.json() else {}
        except Exception as e:
            print(f"Cloud Fetch All Error: {e}")
            return {}

    def get_from_cloud(self, table):
        data = self.get_all_from_cloud(table)
        return [v for k, v in data.items()] if data else []

    def save_to_cloud(self, table, email, data):
        try:
            clean_email = email.replace('.', '_')
            url = f"{self.cloud_url}{table}/{clean_email}.json"
            response = requests.patch(url, json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Cloud Save Error: {e}")
            return False

    def query(self, sql, params=(), fetchone=False):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if not isinstance(params, (list, tuple)): params = (params,)
                cursor.execute(sql, params)
                if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                    conn.commit()
                    return cursor.lastrowid if sql.strip().upper().startswith("INSERT") else cursor.rowcount
                res = cursor.fetchone() if fetchone else cursor.fetchall()
                if fetchone: return dict(res) if res else {}
                return [dict(row) for row in res] if res else []
        except Exception as e:
            print(f"SQL Error: {e}")
            return {} if fetchone else []
