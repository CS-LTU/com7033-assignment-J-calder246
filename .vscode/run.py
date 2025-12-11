from pathlib import Path
import os

ROOT = Path(__file__).parent.parent.resolve()
TEMPLATES = ROOT / 'templates'
UPLOADS = ROOT / 'uploads'

# Create uploads directory if it doesn't exist
try:
    UPLOADS.mkdir(exist_ok=True, mode=0o755)
except (PermissionError, OSError) as e:
    # Directory might already exist with different permissions
    if not UPLOADS.exists():
        raise Exception(f"Cannot create uploads directory: {e}")

assert TEMPLATES.exists(), "templates / folder not found"

print("Using templates", TEMPLATES.resolve())
print("Using uploads", UPLOADS.resolve())




from app4 import app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5340)#run flask app

