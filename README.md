MediShare — Medicine Donation Platform
MediShare is a web application that connects medicine donors with NGOs. Donors can list unused medicines, NGOs can request them, and admins verify and manage the process.

🌐 Live Demo
https://web-production-e49906.up.railway.app

📁 Project Structure
mid-share/
├── app.py                    ← Flask backend (all routes)
├── schema.sql                ← MySQL database schema
├── requirements.txt          ← Python dependencies
├── Procfile                  ← Railway/Gunicorn start command
├── runtime.txt               ← Python version
├── static/
│   └── css/style.css         ← Stylesheet
└── templates/
    ├── base.html             ← Base layout
    ├── index.html            ← Landing page
    ├── login.html            ← Login page
    ├── register.html         ← Register (Donor / NGO)
    ├── donate.html           ← Donate medicine form
    ├── donor_dashboard.html  ← Donor view
    ├── ngo_dashboard.html    ← NGO view
    └── admin_dashboard.html  ← Admin panel

⚙️ Tech Stack

Backend: Python, Flask
Database: MySQL
Frontend: HTML, CSS (Jinja2 templates)
Deployment: Railway


👥 User Roles
RoleHow to AccessDonorRegister on the website → select "Donor"NGORegister on the website → select "NGO"AdminCredentials managed privately by the administrator

🚀 How to Use
As a Donor:

Register → select Donor
Login → click "+ Donate Medicine"
Fill in medicine name, quantity, expiry date, and upload a photo
Submit → wait for admin verification

As an NGO:

Register → select NGO
Login → browse available (approved) medicines
Click "Request This" on any medicine
Track your request status in the "My Requests" tab

As Admin:

Login with admin credentials
Review pending donations → Approve or Reject
Manage NGO requests → update delivery status


🗄️ Database Setup (for local development)

Install MySQL and create a database
Run the schema:

bashmysql -u root -p your_database < schema.sql

Set environment variables:

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=your_database
MYSQL_PORT=3306
SECRET_KEY=your_secret_key

Install dependencies:

bashpip install -r requirements.txt

Run the app:

bashpython app.py

📦 Deployment
This project is deployed on Railway using:

Gunicorn as the WSGI server
Railway MySQL as the database
Environment variables for all sensitive configuration


📌 Note
This is a final year college project built to demonstrate a full-stack web application using Python (Flask) and MySQL.
