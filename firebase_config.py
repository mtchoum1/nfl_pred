# firebase_config.py
import os
import json
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
            cred = None
            firebase_config_string = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', None)
            if firebase_config_string:
                cred = credentials.Certificate(json.loads(firebase_config_string))
            else:
                print("WARNING: 'GOOGLE_APPLICATION_CREDENTIALS' environment variable not set. Attempting to load from nfl-pred-db58a7919c16.json.")
                try:
                    with open('nfl-pred-db58a7919c16.json', 'r') as f:
                        cred = credentials.Certificate(json.load(f))
                    print("Successfully loaded Firebase config from nfl-pred-db58a7919c16.json.")
                except FileNotFoundError:
                    print("ERROR: nfl-pred-db58a7919c16.json not found. Firebase client-side features will not work.")
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://nfl-pred-default-rtdb.firebaseio.com'
            })
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {e}")