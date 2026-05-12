import psycopg2

conn = psycopg2.connect(
    'postgresql://mid_share_db_user:2LapMudIUusti2qPQqOujxtZiY1vQaa2@dpg-d81bv7u7r5hc73cbs11g-a.singapore-postgres.render.com/mid_share_db',
    sslmode='require'
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    address TEXT,
    role VARCHAR(10) NOT NULL DEFAULT 'donor' CHECK (role IN ('donor','ngo','admin')),
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medicines (
    id SERIAL PRIMARY KEY,
    donor_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    quantity VARCHAR(100) NOT NULL,
    expiry_date DATE NOT NULL,
    description TEXT,
    photo VARCHAR(255),
    status VARCHAR(10) DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requests (
    id SERIAL PRIMARY KEY,
    ngo_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    medicine_id INT NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    note TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS otp_verification (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    otp VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email, phone, address, role, password)
VALUES ('Admin', 'admin@medishare.com', '9999999999', 'MediShare HQ', 'admin',
'scrypt:32768:8:1$ghQt9QhamchO8vC0$2d4370e3fcc4b5f5c5d592c91b86207af2ba1614d84e24b762a697f1a3c9253fdc23e4c612ebd2a586afdb8d1cc210af24835eb8bb3d09292bd6ab6c546fb238')
ON CONFLICT (email) DO NOTHING;
""")

conn.commit()
conn.close()
print("Tables created successfully!")
