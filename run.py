from pathlib import Path
import os

# Use absolute path to ensure we're in the right directory
ROOT = Path('/workspaces/com7033-assignment-J-calder246').resolve()
TEMPLATES = ROOT / 'templates'
UPLOADS = ROOT / 'uploads'

# Create uploads directory if it doesn't exist
try:
    UPLOADS.mkdir(exist_ok=True, mode=0o755)
except (PermissionError, OSError) as e:
    # Directory might already exist with different permissions
    if not UPLOADS.exists():
        raise Exception(f"Cannot create uploads directory: {e}")

print("Using templates", TEMPLATES.resolve())
print("Using uploads", UPLOADS.resolve())
print("Templates exists:", TEMPLATES.exists())




from app4 import app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5869)#run flask app

