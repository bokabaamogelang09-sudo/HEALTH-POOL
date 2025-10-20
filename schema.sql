-- Health Pool Database Schema

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS payouts;
DROP TABLE IF EXISTS contributions;
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS members;

-- Members table
CREATE TABLE members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    id_number TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    plan TEXT NOT NULL,
    monthly_amount REAL NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Contributions table
CREATE TABLE IF NOT EXISTS contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    reference_id TEXT UNIQUE,
    status TEXT DEFAULT 'PENDING',
    momo_reference TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (id)
);

-- Claims table
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    hospital TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'PENDING',
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (id)
);

-- Payouts table
CREATE TABLE IF NOT EXISTS payouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    reference_id TEXT UNIQUE,
    status TEXT DEFAULT 'PENDING',
    momo_reference TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims (id)
);

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('admin', 'member')),
    member_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (id)
);

-- Insert sample data
INSERT OR IGNORE INTO members (id, name, id_number, phone, plan, monthly_amount, status) VALUES
(1, 'Nomsa Mthembu', '8001015800084', '27721234567', 'Standard Care', 250, 'active'),
(2, 'Thabo Khumalo', '7508125900123', '27734567890', 'Basic Care', 150, 'active'),
(3, 'Sipho Dlamini', '9203041234567', '27765432100', 'Premium Care', 350, 'active'),
(4, 'Zanele Ndlovu', '8505201234567', '27787654321', 'Standard Care', 250, 'active'),
(5, 'Mandla Mokoena', '7701151234567', '27798765432', 'Basic Care', 150, 'active');

INSERT OR IGNORE INTO claims (id, member_id, type, amount, hospital, priority, status) VALUES
(1, 1, 'Emergency', 1200, 'Chris Hani Baragwanath', 'high', 'PENDING'),
(2, 2, 'Regular', 450, 'Charlotte Maxeke', 'medium', 'PENDING'),
(3, 3, 'Specialist', 800, 'Netcare Milpark', 'low', 'APPROVED');

-- Sample contributions
INSERT OR IGNORE INTO contributions (member_id, amount, status) VALUES
(1, 250, 'SUCCESSFUL'),
(2, 150, 'SUCCESSFUL'),
(3, 350, 'SUCCESSFUL'),
(1, 250, 'SUCCESSFUL'),
(2, 150, 'PENDING');