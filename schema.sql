-- ============================================================
-- MediShare Database Schema
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(120) NOT NULL,
    email      VARCHAR(120) NOT NULL UNIQUE,
    phone      VARCHAR(20) NOT NULL,
    address    TEXT,
    role       ENUM('donor','ngo','admin') NOT NULL DEFAULT 'donor',
    password   VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medicines (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    donor_id    INT NOT NULL,
    name        VARCHAR(200) NOT NULL,
    quantity    VARCHAR(100) NOT NULL,
    expiry_date DATE NOT NULL,
    description TEXT,
    photo       VARCHAR(255),
    status      ENUM('pending','approved','rejected') DEFAULT 'pending',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS requests (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    ngo_id      INT NOT NULL,
    medicine_id INT NOT NULL,
    note        TEXT,
    status      ENUM('pending','approved','in_transit','delivered',rejected) DEFAULT 'pending',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ngo_id) REFERENCES users(id),
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);
CREATE TABLE IF NOT EXISTS otp_verification (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(120),
  otp VARCHAR(10),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default admin account (login: admin@medishare.com / admin123)
INSERT IGNORE INTO users (name, email, phone, address, role, password)
VALUES (
    'Admin',
    'admin@medishare.com',
    '9999999999',
    'MediShare HQ',
    'admin',
    'admin123'
    'scrypt:32768:8:1$D7TUSmaXBdx1NhvM$ccb1c2e828c029a3b25a55fcc8546bdc3b56593143c320a8036eab7c8869d0f675f86bc8e78543446b328e1bfff9c092943f5ce2a3c0c40934f64433602592a1'
);
