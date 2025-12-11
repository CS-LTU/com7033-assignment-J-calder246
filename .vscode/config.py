
import os

#configuration
class Config:
    BASE_DIR = os.getcwd() #current directory
    SECRET_KEY = os.environ.get("SECRET_KEY", "Buglady458") #makes secret key

    DB_PATH = os.path.join(BASE_DIR, "users.db") #path to users.db
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads") #directory to saved csvs
    ALLOWED_EXTENSIONS = {"csv"} #restricts uploads to csv
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    #Mongo configuration
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://2511607_db_user:8eOYxezbnZPcBiHh@stroke-dataset.w6p63mq.mongodb.net/")
    MONGO_DB = "medicaldata"
    MONGO_STROKE_COLLECTION = "strokedata"
    MONGO_LOGS_COLLECTION = "logs"


