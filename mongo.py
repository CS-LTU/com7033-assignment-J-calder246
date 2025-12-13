from pymongo import MongoClient;
from bson.objectid import ObjectId;
import pandas as pd;
from flask import Flask, render_template;

# Initialize MongoDB client
client = MongoClient('mongodb+srv://2511607_db_user:8eOYxezbnZPcBiHh@stroke-dataset.w6p63mq.mongodb.net/')

# Getting server info
server_info = client.server_info()
mongo_version = server_info['version']
print(f'MongoDB Version: {mongo_version}')

# Access database and collection
db = client['medicaldata']
collection = db['strokedata']