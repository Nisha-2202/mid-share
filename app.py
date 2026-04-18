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

otp_storage = {}   # ✅ fixed OTP storage

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

        # ✅ Safe form handling
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        role = request.form.get('role')
        password_raw = request.form.get('password')

        # ✅ Validation (prevents 500 error)
        if not name or not email or not phone or not role or not password_raw:
            flash('All fields are required', 'error')
            return redirect('/register')

        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            flash('Email already registered', 'error')
            return redirect('/register')

        # Hash password
        password = generate_password_hash(password_raw)

        # Insert user
        cur.execute("""
            INSERT INTO users (name, email, phone, address, role, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            name,
            email,
            phone,
            address if address else '',
            role,
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
            elif  user['role'] == 'ngo':
                 return redirect('/ngo_dashboard') 
            else:
                return redirect('/donor')

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

# SEND OTP
@app.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.form['email']

    # check user exists
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    db.close()

    if not user:
        flash('Email not registered', 'error')
        return redirect('/forgot-password')

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp

    print(f"OTP for {email}: {otp}")  # console OTP

    flash('OTP sent! Check console', 'info')
    return redirect('/forgot-password')

# VERIFY OTP
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form['email']
    user_otp = request.form['otp']

    if email in otp_storage and otp_storage.get(email) == user_otp:
        session['reset_email'] = email   # ✅ store verified email
        flash('OTP Verified! Now reset password', 'success')
        return redirect('/forgot-password')
    else:
        flash('Invalid OTP', 'error')
        return redirect('/forgot-password')

# RESET PASSWORD
@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = session.get('reset_email')

    if not email:
        flash('Verify OTP first', 'error')
        return redirect('/forgot-password')

    new_password = request.form['new_password']

    db = get_db()
    cur = db.cursor()

    hashed = generate_password_hash(new_password)

    cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, email))

    db.commit()
    db.close()

    # cleanup
    otp_storage.pop(email, None)
    session.pop('reset_email', None)

    flash('Password updated successfully', 'success')
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

# -------- MEDICINES --------
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

# -------- REQUEST --------
@app.route('/request_medicine/<int:med_id>', methods=['POST'])
def request_medicine(med_id):
    if session.get('user_role') != 'ngo':
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO requests (ngo_id, medicine_id, note, status)
        VALUES (%s, %s, %s, 'pending')
    """, (
        session['user_id'],
        med_id,
        request.form.get('note', '')
    ))

    db.commit()
    db.close()

    flash('Request sent successfully', 'success')
    return redirect('/ngo_dashboard')
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
    all_meds = cur.fetchall()

    cur.execute("SELECT * FROM medicines WHERE status='pending'")
    pending_meds = cur.fetchall()

    pending = len(pending_meds)

    cur.execute("SELECT * FROM medicines WHERE status='approved'")
    approved = len(cur.fetchall())
    cur.execute("SELECT COUNT(*) FROM users WHERE role='donor'")
    donors = cur.fetchone()['COUNT(*)']
    db.close()

    return render_template(
        'admin_dashboard.html',
        all_meds=all_meds,
        pending_meds=pending_meds,
        pending=pending,
        approved=approved,
        total_req=0,
        donors=donors,  
        all_requests=[]
    )
@app.route('/reset-password-direct', methods=['POST'])
def reset_password_direct():
    email = request.form['email']
    new_password = request.form['new_password']

    db = get_db()
    cur = db.cursor()

    # check user exists
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()

    if not user:
        flash('Email not registered', 'error')
        return redirect('/forgot-password')

    hashed = generate_password_hash(new_password)

    cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, email))
    db.commit()
    db.close()

    flash('Password updated successfully', 'success')
    return redirect('/login')


@app.route('/ngo_dashboard')
def ngo_dashboard():
    if session.get('user_role') != 'ngo':
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    # Get approved medicines
    cur.execute("SELECT * FROM medicines WHERE status='approved'")
    medicines = cur.fetchall()

    # Get NGO requests
    cur.execute("""
        SELECT r.*, m.name AS medicine_name
        FROM requests r
        JOIN medicines m ON r.medicine_id = m.id
        WHERE r.ngo_id=%s
        ORDER BY r.id DESC
    """, (session['user_id'],))
    
    my_requests = cur.fetchall()

    db.close()

    return render_template(
        'ngo_dashboard.html',
        medicines=medicines,
        my_requests=my_requests
    )

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
