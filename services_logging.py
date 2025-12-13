from datetime import datetime
from config import Config
from pymongo import MongoClient

_client = MongoClient(Config.MONGO_URI)
_mdb = _client[Config.MONGO_DB]
stroke_collection = _mdb[Config.MONGO_STROKE_COLLECTION]
logs_collection = _mdb[Config.MONGO_LOGS_COLLECTION]

def log_action(action, actor_cid, details=None):
    try:
        logs_collection.insert_one({
        "action": action,
        "actor_customer_id": actor_cid,
        "details": details,
        "timestamp": datetime.utcnow()
        })
    except Exception as e:
        print(f"failed to log action: {e}")
        