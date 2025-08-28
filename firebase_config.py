# firebase_config.py
import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK, ensuring it only runs once.
    """
    if not firebase_admin._apps:
        try:
            # IMPORTANT: Ensure your Firebase service account key file is in the root directory
            # or provide the correct path.
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://nfl-pred-default-rtdb.firebaseio.com'
            })
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {e}")