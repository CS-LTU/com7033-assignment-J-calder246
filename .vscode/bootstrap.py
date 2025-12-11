
import bcrypt
from db_sqlite import init_sqlite_db, get_db
from services_logging import log_action

"""
BOOTSTRAP LOGIC"""
def bootstrap_once():
    init_sqlite_db()
    conn = get_db()
    cur = conn.cursor()

    #check if admin exists
    cur.execute("SELECT COUNT(1) FROM admins")
    admin_exists = cur.fetchone()[0] > 0
    
    #create admin if none exists
    if not admin_exists:
        username = "Applebee83"
        customer_id = "admin001DEA"
        age = 22
        pw_hash = bcrypt.hashpw("AdminPass42069".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur.execute("SELECT 1 FROM users WHERE customer_id = ?", (customer_id,))
        if not cur.fetchone():
            cur.execute("INSERT INTO users (username, customer_id, age, password_hash) VALUES (?, ?, ?, ?)",
        
                        (username, customer_id, age, pw_hash)
                        )
            cur.execute("INSERT OR IGNORE INTO admins (customer_id) VALUES (?)", (customer_id,))
                        

conn = get_db()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) as admin_count FROM admins")
has_admins = cur.fetchone()["admin_count"] > 0
if not has_admins:
    username = "Applebee"
    customer_id = "admin001"
    pw_hash = bcrypt.hashpw("AdminPass42069".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    #inserts admin account
    cur.execute("SELECT 1 FROM users WHERE customer_id = ?", (customer_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, customer_id, password_hash) VALUES (?, ?, ?)",
            (username, customer_id, pw_hash)
        )
    #nOW GRANTING ADMIN ROLE
    cur.execute("INSERT INTO admins (customer_id) VALUES (?)", (customer_id,))
    conn.commit()
    log_action("CREATED_DEFAULT_ADMIN", customer_id,{})
conn.close()



