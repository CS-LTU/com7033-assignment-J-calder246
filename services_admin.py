
from db_sqlite import get_db

def is_admin(customer_id: str) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admins WHERE customer_id = ?", (customer_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None
#^^ this fuction checks if a customer id exists in the admin table, if true the user has admin permissions

