-- ============================================================
-- MediShare Database Schema (FINAL CLEAN VERSION)
-- ============================================================

-- ---------------- USERS TABLE ----------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    address TEXT,
    role ENUM('donor','ngo','admin') NOT NULL DEFAULT 'donor',
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------- MEDICINES TABLE ----------------
CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    quantity VARCHAR(100) NOT NULL,
    expiry_date DATE NOT NULL,
    description TEXT,
    photo VARCHAR(255),
    status ENUM('pending','approved','rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ---------------- REQUESTS TABLE ----------------
CREATE TABLE IF NOT EXISTS requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ngo_id INT NOT NULL,
    medicine_id INT NOT NULL,
    note TEXT,
    status ENUM('pending','approved','in_transit','delivered','rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ngo_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);

-- ---------------- OTP TABLE ----------------
CREATE TABLE IF NOT EXISTS otp_verification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    otp VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- DEFAULT ADMIN USER (PASSWORD = admin123)
-- NOTE: Password is HASHED (IMPORTANT)
-- ============================================================

INSERT INTO users (name, email, phone, address, role, password)
VALUES (
    'Admin',
    'admin@medishare.com',
    '9999999999',
    'MediShare HQ',
    'admin',
    'pbkdf2:sha256:260000$examplehash$1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
)
ON DUPLICATE KEY UPDATE email=email;
