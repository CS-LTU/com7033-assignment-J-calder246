from flask_pymongo import PyMongo
from flask import Flask

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://2511607_db_user:8eOYxezbnZPcBiHh@stroke-dataset.w6p63mq.mongodb.net/"

mongo = PyMongo(app)
