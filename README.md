# Smore Sports NFL Predictions & Survivor Pool

Welcome to Smore Sports, a web application that provides data-driven NFL game predictions and hosts an interactive Survivor Pool game. The project uses historical and current season data to predict game outcomes and allows users to compete against each other in a weekly pick'em challenge.

---

## Live Demo

You can check out a live version of the application here:
**[https://smoresports.onrender.com/](https://smoresports.onrender.com/)**

**Note**: The application is hosted on a free service. If the server is asleep, it may take 30-60 seconds to boot up on your first visit.

---

## Features

* **NFL Game Predictions**: View weekly game predictions based on a statistical model that analyzes team performance data. Win probabilities are displayed for each matchup.
* **Survivor Pool Game**: A "Last Man Standing" style game where users pick one winning team each week to advance. The game includes complex rules such as:
    * **Sequential Picks**: Users must make picks for weeks in order.
    * **Divisional Lockout**: A division is locked after a team from it is picked, until all 8 divisions have been used in a cycle.
    * **Weekly Lockouts**: Picks for a given week are locked once the first game of that week begins.
* **User Authentication**: Secure sign-up and login functionality using Firebase Authentication.
* **Live Leaderboard**: A real-time leaderboard that tracks each player's total wins and current winning streak.
* **Historical Standings**: Compare the model's predicted season records against the actual NFL standings for past seasons.
* **Automated Weekly Updates**: A backend script, designed to be run as a cron job or GitHub Action, automatically processes weekly results, updates player picks (correct/incorrect), and advances the game.

---

## Tech Stack

* **Backend**: Python with Flask
* **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript
* **Database**: Firebase Realtime Database for game data
* **Authentication**: Firebase Authentication for user management
* **Automation**: GitHub Actions for scheduled jobs
* **Data Source**: Live NFL game data is fetched from the ESPN API.

---

## Setup and Installation locally

Follow these steps to get the application running locally.

### 1. Prerequisites

* Python 3.8+
* A Google Firebase account

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-name>
```

### 3. Set Up Python Environment

Create and activate a virtual environment:

```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Configure Firebase

1.  **Create a Firebase Project**: Go to the [Firebase Console](https://console.firebase.google.com/) and create a new project.
2.  **Create a Web App**: In your project, create a new Web App. Firebase will provide you with a `firebaseConfig` object.
3.  **Enable Authentication**: Go to **Build > Authentication > Sign-in method** and enable the **Email/Password** provider.
4.  **Create Realtime Database**: Go to **Build > Realtime Database**, create a database, and start in **Test mode** for now.
5.  **Set Security Rules**: In the **Rules** tab of your Realtime Database, paste the following rules and click **Publish**:
    ```json
    {
      "rules": {
        "last_man_standing": {
          ".read": "auth != null",
          ".write": "auth != null"
        }
      }
    }
    ```
6.  **Generate a Service Account Key**:
    * In your Firebase project settings, go to the **Service Accounts** tab.
    * Click **Generate new private key**. A JSON file will be downloaded.
    * Save this file securely. **Do not commit it to your repository.**

### 5. Set Environment Variables

The application requires two environment variables to connect to Firebase.

1.  **`FIREBASE_CONFIG`**: Set this to the `firebaseConfig` JSON object from step 4.2.
2.  **`GOOGLE_APPLICATION_CREDENTIALS`**: Set this to the absolute path of the service account JSON file you downloaded in step 4.6.

```bash
# For macOS/Linux
export FIREBASE_CONFIG='{"apiKey": "...", "authDomain": "...", ...}'
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/serviceAccountKey.json"

# For Windows
set FIREBASE_CONFIG='{"apiKey": "...", "authDomain": "...", ...}'
set GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\serviceAccountKey.json"
```

### 6. Generate Historical Data

The prediction model needs historical data to function. Run the `history_generator.py` script once to create the necessary files. This will take a few minutes.

```bash
python history_generator.py
```

---

## Running the Application

Once the setup is complete, you can start the Flask web server:

```bash
flask run
```

The application will be available at `http://127.0.0.1:5000`.

---

## Automated Jobs

The `cron_jobs.py` script is responsible for processing weekly game results.

* **Functionality**: It fetches the winners of all completed games for a given week and updates each player's pick in the database with a "correct" or "incorrect" result.
* **Manual Execution**: You can run it manually for a specific week like this:
    ```bash
    # Example: Process results for Week 2 of the 2025 season
    python cron_jobs.py 2025 2
    ```
* **Automation**: This script is designed to be run automatically by the GitHub Action defined in `.github/workflows/weekly_job.yml`. The action is scheduled to run every Tuesday morning and will dynamically calculate the correct week to process.
