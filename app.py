from flask import Flask, render_template, request, redirect, session, flash
import random
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.secret_key = os.environ.get('SECRET_KEY', 'medishare_secret_2024')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

otp_storage = {}
verified_users = set()

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

# ---------------- HOME ----------------
@app.route('/')
def index():
    return render_template('index.html')

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()

        email = request.form['email']
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            flash('Email already registered', 'error')
            return redirect('/register')

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

        flash('Registered successfully', 'success')
        return redirect('/login')

    return render_template('register.html')

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (request.form['email'],))
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            session['user_role'] = user['role']

            if user['role'] == 'admin':
                return redirect('/admin')
            else:
                return redirect('/medicines')

        flash('Invalid login', 'error')

    return render_template('login.html')

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# -------- FORGOT PASSWORD --------
@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.form['email']
    otp = str(random.randint(100000, 999999))

    otp_storage[email] = otp
    print(f"OTP for {email}: {otp}")

    flash('OTP sent! Check console', 'info')
    return redirect('/forgot-password')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form['email']
    user_otp = request.form['otp']

    if otp_storage.get(email) == user_otp:
        verified_users.add(email)
        otp_storage.pop(email, None)
        flash('OTP Verified', 'success')
    else:
        flash('Invalid OTP', 'error')

    return redirect('/forgot-password')

@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.form['email']

    if email not in verified_users:
        flash('Verify OTP first', 'error')
        return redirect('/forgot-password')

    db = get_db()
    cur = db.cursor()

    hashed = generate_password_hash(request.form['new_password'])

    cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, email))

    db.commit()
    db.close()

    verified_users.remove(email)

    flash('Password updated', 'success')
    return redirect('/login')

# -------- DONOR --------
@app.route('/donor')
def donor_dashboard():
    if session.get('user_role') != 'donor':
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM medicines WHERE donor_id=%s", (session['user_id'],))
    medicines = cur.fetchall()

    db.close()

    return render_template('donor_dashboard.html', medicines=medicines)

# -------- DONATE --------
@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if session.get('user_role') != 'donor':
        return redirect('/login')

    if request.method == 'POST':
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

        flash('Medicine added', 'success')
        return redirect('/donor')

    return render_template('donate.html')

# -------- MEDICINES (ALL USERS) --------
@app.route('/medicines')
def medicines():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM medicines WHERE status='approved'")
    medicines = cur.fetchall()

    db.close()

    return render_template('ngo_dashboard.html', medicines=medicines)

# -------- REQUEST / ORDER --------
@app.route('/request/<int:med_id>', methods=['POST'])
def request_medicine(med_id):
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO requests (ngo_id,medicine_id,note,status)
        VALUES (%s,%s,%s,'pending')
    """, (session['user_id'], med_id, request.form.get('note', '')))

    request_id = cur.lastrowid

    db.commit()
    db.close()

    return redirect(f'/payment/{request_id}')

# -------- PAYMENT --------
@app.route('/payment/<int:request_id>')
def payment_page(request_id):
    return render_template('payment.html', request_id=request_id)

@app.route('/payment-success/<int:request_id>', methods=['POST'])
def payment_success(request_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("UPDATE requests SET status='approved' WHERE id=%s", (request_id,))

    db.commit()
    db.close()

    flash('Payment Successful! Order Confirmed', 'success')
    return redirect('/medicines')

# -------- ADMIN --------
@app.route('/admin')
def admin_dashboard():
    if session.get('user_role') != 'admin':
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM medicines")
    medicines = cur.fetchall()

    db.close()

    return render_template('admin_dashboard.html', medicines=medicines)

@app.route('/admin/medicine/<int:med_id>/<action>')
def admin_action(med_id, action):
    status = 'approved' if action == 'approve' else 'rejected'

    db = get_db()
    cur = db.cursor()

    cur.execute("UPDATE medicines SET status=%s WHERE id=%s", (status, med_id))

    db.commit()
    db.close()

    return redirect('/admin')

# -------- RUN --------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
