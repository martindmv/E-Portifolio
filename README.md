# 🎓 E-Portfolio

**Live Demonstration:** https://e-portifolio-4zsc.onrender.com/portfolios

## 📖 About The Project
This web application allows users to create and manage E-Portfolios to highlight their competencies. It serves as a digital resume designed to showcase:
* Personal Information
* Formations & Education
* Competencies & Skills
* Professional Experiences
* Academic or Personal Projects
* Social Links (GitHub, LinkedIn)

## 🛠️ Technology Stack
* **Backend Framework:** FastAPI (Python)
* **ORM:** SQLAlchemy
* **Database:** PostgreSQL (Production) / SQLite (Local Development)
* **Storage:** Firebase (for image and media storage)
* **Hosting & CI/CD:** Render.com

---

## 💻 Local Development Setup
Follow these instructions to run the project locally on your machine.

### 1. Prerequisites
* Python 3.8+ installed on your machine.
* A Firebase account and project set up.

### 2. Environment Setup
Clone the repository and navigate to the project folder. Create and activate a virtual environment:

**On Windows:**
```bash
py -m venv env
.\env\Scripts\activate
```

*(On Mac/Linux: `python3 -m venv env` then `source env/bin/activate`)*

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Secrets & Environment Variables 🔑
For security reasons, sensitive keys are not tracked on GitHub. You must configure them locally:

1. **Database:** The application uses SQLite by default for local development. To connect to a remote PostgreSQL database, create a `.env` file at the root of the project and add: `DATABASE_URL=your_postgres_connection_url`.
2. **Firebase Configuration:** Download your Firebase service account private key from the Firebase Console. Place the file at the root of the project and rename it exactly to `serviceAccountKey.json`. *(Note: This file is ignored by Git and will not be pushed).*
3. **Admin mode:** Administrators have the permission to delete any portfolio. To set up the admin account, you must add the ADMIN_EMAIL variable to your `.env` file.

### 4. Run the Application
Start the local server using Uvicorn:
```bash
uvicorn main:app --reload
```
*(Alternatively, you can run `fastapi dev`)*

Once running, the API and documentation will be accessible at `http://localhost:8000`.

---

## 🚀 Deployment & CI/CD (Production)
This application is fully configured for continuous integration and deployment (CI/CD) on **Render.com**.

* **Automatic Deployments:** Any code pushed or merged into the `master` branch on GitHub automatically triggers a zero-downtime deployment on Render.
* **Database Persistence:** Production data is safely stored on a dedicated Render PostgreSQL database, ensuring no data is lost during server sleeps or restarts. If you wish to visualize your data, you can connect your Postgresql to a SQL Client like `DBeaver`. 
* **Secret Management:** Production credentials (`DATABASE_URL` and the Firebase `serviceaccountkey.json`) are securely injected into the build using Render's "Environment Variables" and "Secret Files" configurations.

