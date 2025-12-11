
from datetime import datetime
from pymongo import MongoClient
from config import Config



#MongoDB setup
client = MongoClient(Config.MONGO_URI)
mdb = client['medicaldata']
stroke_collection = mdb["strokedata"]
logs_collection = mdb['logs']  # collection of logs created




def log_action(action, actor_customer_cid, details=None):
    try:
        logs_collection.insert_one({
            "action": action,
            "actor_customer_id": actor_cid,
            "details": details or {},
            "timestamp": datetime.utcnow(),
        })
    except Exception as e:
        print("Error in logging", e)
         #means app won't break if the attempted log fails
    #^^^ function for logging actions

