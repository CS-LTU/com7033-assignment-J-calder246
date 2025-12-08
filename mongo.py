
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

# CRUD Operations
def create_user(_id, id, gender, age, hypertension, heart_disease, ever_married, work_type, Residence_type, avg_glucose_level, bmi, smoking_status, stroke):
    new_doc = {
        "_id": _id, "id": id, "gender": gender, "age": age,
        "hypertension": hypertension, "heart_disease": heart_disease,
        "ever_married": ever_married, "work_type": work_type,
        "Residence_type": Residence_type, "avg_glucose_level": avg_glucose_level,
        "bmi": bmi, "smoking_status": smoking_status, "stroke": stroke
    }
    result = collection.insert_one(new_doc)
    print(f"[CREATE] Inserted document with _id={result.inserted_id}")
    return result.inserted_id

def read_strokedata(filter_query=None):
    if filter_query is None:
        filter_query = {}
    docs = list(collection.find(filter_query))
    print(f"[READ] Found {len(docs)} documents matching {filter_query}:")
    for d in docs:
        print(d)
    return docs

def update_strokedata(document_id, new_gender=None, new_age=None, new_hypertension=None, new_heart_disease=None, new_ever_married=None, new_work_type=None, new_Residence_type=None, new_avg_glucose_level=None, new_bmi=None, new_smoking_status=None, new_stroke=None):
    update_fields = {}
    if new_gender is not None:
        update_fields["gender"] = new_gender
    if new_age is not None:
        update_fields["age"] = new_age
    if new_hypertension is not None:
        update_fields["hypertension"] = new_hypertension
    if new_heart_disease is not None:
        update_fields["heart_disease"] = new_heart_disease
    if new_ever_married is not None:
        update_fields["ever_married"] = new_ever_married
    if new_work_type is not None:
        update_fields["work_type"] = new_work_type
    if new_Residence_type is not None:
        update_fields["Residence_type"] = new_Residence_type
    if new_avg_glucose_level is not None:
        update_fields["avg_glucose_level"] = new_avg_glucose_level
    if new_bmi is not None:
        update_fields["bmi"] = new_bmi
    if new_smoking_status is not None:
        update_fields["smoking_status"] = new_smoking_status
    if new_stroke is not None:
        update_fields["stroke"] = new_stroke
    
    result = collection.update_one({"_id": ObjectId(document_id)}, {"$set": update_fields})
    print(f"[UPDATE] Matched {result.matched_count}, Modified {result.modified_count}")

def destroy_patient(document_id):
    result = collection.delete_one({"_id": ObjectId(document_id)})
    print(f"[DELETE] Deleted {result.deleted_count} document with _id {document_id}")

# Flask app
app = Flask(__name__)

@app.route('/')
def index():
    collections = db.list_collection_names()
    data_dict = {}
    for collection_name in collections:
        collection = db[collection_name]
        data_list = list(collection.find())
        if data_list:
            df = pd.DataFrame(data_list)
            data_dict[collection_name] = df.head().to_html(classes='data', headers='true')
        else:
            data_dict[collection_name] = "no data in this collection"
    return render_template('index.html', data=data_dict)

if __name__ == "__main__":
    app.run(debug=False)

