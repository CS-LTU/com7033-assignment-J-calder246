
import os
from werkzeug.utils import secure_filename
from config import Config

ALLOWED_EXTENSIONS = {"csv"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_save_upload(file_storage, upload_folder=None):
    upload_folder = upload_folder or Config.UPLOAD_FOLDER
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(file_storage.filename)
    filepath = os.path.join(upload_folder, filename)
    file_storage.save(filepath)
    return filepath, filename

'''
Path("auth_utils.py").write_text(code)
print("auth_utils.py loaded")'''