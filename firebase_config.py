# firebase_config.py
import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK, ensuring it only runs once.
    """
    if not firebase_admin._apps:
        try:
            # This will use the GOOGLE_APPLICATION_CREDENTIALS environment variable by default
            print("Attempting to initialize Firebase Admin SDK using Application Default Credentials...")
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://nfl-pred-default-rtdb.firebaseio.com' # IMPORTANT: Replace with your database URL
            })
            print("Firebase Admin SDK initialized successfully via Application Default Credentials.")
        except Exception as e:
            print(f"WARNING: Application Default Credentials failed: {e}")
            print("Attempting to load from local serviceAccountKey.json as a fallback.")
            try:
                cred = credentials.Certificate('nfl-pred-b17e26ba6bb9.json')
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://nfl-pred-default-rtdb.firebaseio.com' # IMPORTANT: Replace with your database URL
                })
                print("Firebase Admin SDK initialized successfully from local file.")
            except FileNotFoundError:
                print("ERROR: serviceAccountKey.json not found. Firebase Admin features will not work.")
            except Exception as e_local:
                print(f"Error initializing from local file: {e_local}")