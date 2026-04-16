from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import random
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os, datetime

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.secret_key = os.environ.get('SECRET_KEY', 'medishare_secret_2024')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

otp_storage = {}

# ---------------- DATABASE ----------------
def get_db():
    return pymysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        database=os.environ.get('MYSQL_DB', 'railway'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

# ---------------- HELPERS ----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template('index.html')

# -------- AUTH --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            db = get_db()
            cur = db.cursor()

            email = request.form['email']

            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                flash('Email already registered.', 'error')
                return redirect(url_for('register'))

            password = generate_password_hash(request.form['password'])

            cur.execute("""
                INSERT INTO users (name,email,phone,address,role,password)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                request.form['name'],
                email,
                request.form['phone'],
                request.form['address'],
                request.form['role'],
                password
            ))

            db.commit()
            db.close()

            flash('Registration successful!', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(str(e), 'error')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            db = get_db()
            cur = db.cursor()

            cur.execute("SELECT * FROM users WHERE email=%s", (request.form['email'],))
            user = cur.fetchone()
            db.close()

            if user and check_password_hash(user['password'], request.form['password']):
                session['user_id'] = user['id']
                session['user_role'] = user['role']

                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'ngo':
                    return redirect(url_for('ngo_dashboard'))
                else:
                    return redirect(url_for('donor_dashboard'))

            flash('Invalid login', 'error')

        except Exception as e:
            flash(str(e), 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -------- OTP --------
@app.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.form['email']
    otp = str(random.randint(100000, 999999))

    otp_storage[email] = otp

    msg = Message('OTP Verification',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.body = f'Your OTP is {otp}'

    mail.send(msg)
    return "OTP Sent"


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    if otp_storage.get(request.form['email']) == request.form['otp']:
        return "OTP Verified"
    return "Invalid OTP"
    @app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/reset-password', methods=['POST'])
def reset_password():
    db = get_db()
    cur = db.cursor()

    hashed = generate_password_hash(request.form['new_password'])

    cur.execute("UPDATE users SET password=%s WHERE email=%s",
                (hashed, request.form['email']))

    db.commit()
    db.close()

    return "Password Updated"

# -------- DONOR --------
@app.route('/donor')
def donor_dashboard():
    if session.get('user_role') != 'donor':
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM medicines WHERE donor_id=%s",
                (session['user_id'],))
    medicines = cur.fetchall()

    db.close()

    return render_template('donor_dashboard.html', medicines=medicines)


@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if session.get('user_role') != 'donor':
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            photo = request.files.get('photo')
            filename = ''

            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            db = get_db()
            cur = db.cursor()

            cur.execute("""
                INSERT INTO medicines (donor_id,name,quantity,expiry_date,description,photo,status)
                VALUES (%s,%s,%s,%s,%s,%s,'pending')
            """, (
                session['user_id'],
                request.form['medicine_name'],
                request.form['quantity'],
                request.form['expiry_date'],
                request.form['description'],
                filename
            ))

            db.commit()
            db.close()

            flash('Submitted!', 'success')

        except Exception as e:
            flash(str(e), 'error')

        return redirect(url_for('donor_dashboard'))

    return render_template('donate.html')

# -------- NGO --------
@app.route('/ngo')
def ngo_dashboard():
    if session.get('user_role') != 'ngo':
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM medicines WHERE status='approved'")
    medicines = cur.fetchall()

    db.close()

    return render_template('ngo_dashboard.html', medicines=medicines)


@app.route('/request/<int:med_id>', methods=['POST'])
def request_medicine(med_id):
    if session.get('user_role') != 'ngo':
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO requests (ngo_id,medicine_id,note,status)
        VALUES (%s,%s,%s,'pending')
    """, (session['user_id'], med_id, request.form.get('note', '')))

    db.commit()
    db.close()

    flash('Request sent!', 'success')
    return redirect(url_for('ngo_dashboard'))

# -------- ADMIN --------
@app.route('/admin')
def admin_dashboard():
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM medicines")
    medicines = cur.fetchall()

    db.close()

    return render_template('admin_dashboard.html', medicines=medicines)


@app.route('/admin/medicine/<int:med_id>/<action>')
def admin_action(med_id, action):
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))

    status = 'approved' if action == 'approve' else 'rejected'

    db = get_db()
    cur = db.cursor()

    cur.execute("UPDATE medicines SET status=%s WHERE id=%s",
                (status, med_id))

    db.commit()
    db.close()

    return redirect(url_for('admin_dashboard'))

# -------- RUN --------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
