


from datetime import datetime
import json
import os
from threading import Lock

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config import Config


class LocalCollection:
    def __init__(self, path, default=None):
        self.path = path
        self.lock = Lock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, 'w', encoding='utf8') as f:
                json.dump(default or [], f)

    def _read(self):
        with open(self.path, 'r', encoding='utf8') as f:
            txt = f.read()
        try:
            return json.loads(txt)
        except Exception:
            import re
            arrays = re.findall(r"\[.*?\]", txt, flags=re.S)
            combined = []
            for a in arrays:
                try:
                    part = json.loads(a)
                    if isinstance(part, list):
                        combined.extend(part)
                except Exception:
                    continue
            return combined

    def _write(self, data):
        with open(self.path, 'w', encoding='utf8') as f:
            json.dump(data, f, default=str, indent=2)

    def find(self, query=None):
        docs = self._read()
        if not query:
            return docs
        def match(d):
            for k, v in query.items():
                if d.get(k) != v:
                    return False
            return True
        return [d for d in docs if match(d)]

    def insert_one(self, doc):
        with self.lock:
            docs = self._read()
            docs.append(doc)
            self._write(docs)
            return {'acknowledged': True}

    def count_documents(self, query=None):
        return len(self.find(query))


# Try Mongo with a short timeout; fall back to LocalCollection on failure.
_use_local = False
_local_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(_local_dir, exist_ok=True)
_strokepath = os.path.join(_local_dir, 'sample_strokedata.json')
_logpath = os.path.join(_local_dir, 'sample_logs.json')

_sample_stroke = [
    {
        "id": 1,
        "gender": "Female",
        "age": 68,
        "hypertension": 0,
        "heart_disease": 1,
        "stroke": 1,
        "customer_id": "sample-cid-1"
    }
]

try:
    _client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=2000)
    # quick ping
    _client.admin.command('ping')
    _mdb = _client[Config.MONGO_DB]
    logs_collection = _mdb[Config.MONGO_LOGS_COLLECTION]
    stroke_collection = _mdb[Config.MONGO_STROKE_COLLECTION]
except Exception as e:
    print('mongo error:', e)
    _use_local = True
    stroke_collection = LocalCollection(_strokepath, default=_sample_stroke)
    logs_collection = LocalCollection(_logpath, default=[])


def log_action(action, actor_cid, details=None):
    doc = {
        "action": action,
        "actor_customer_id": actor_cid,
        "details": details or {},
        "ts": datetime.utcnow().isoformat()
    }
    try:
        if _use_local:
            logs_collection.insert_one(doc)
        else:
            logs_collection.insert_one(doc)
    except PyMongoError as e:
        print("Log insert failed", e)
    except Exception as e:
        print("Local log insert failed", e)

