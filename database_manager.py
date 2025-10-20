import sqlite3
import os
import time
import threading
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Configure logging
logger = logging.getLogger(__name__)

class CommunityPoolManager:
    def __init__(self, db_path="health_pool.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _connect(self):
        """Create database connection with better settings"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _init_db(self):
        """Initialize database tables"""
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    monthly_amount DECIMAL(10,2) NOT NULL DEFAULT 50.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'active'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    user_type TEXT NOT NULL DEFAULT 'member',
                    member_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER REFERENCES members(id),
                    amount DECIMAL(10,2) NOT NULL,
                    payment_reference VARCHAR(100) UNIQUE,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER REFERENCES members(id),
                    amount DECIMAL(10,2) NOT NULL,
                    description TEXT NOT NULL,
                    type VARCHAR(50) DEFAULT 'General',
                    hospital VARCHAR(100),
                    priority VARCHAR(20) DEFAULT 'normal',
                    status VARCHAR(20) DEFAULT 'pending',
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP NULL,
                    admin_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id INTEGER REFERENCES claims(id),
                    amount DECIMAL(10,2) NOT NULL,
                    payment_reference VARCHAR(100) UNIQUE,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP NULL
                )
            ''')
            
            # Create default admin user
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            if not cursor.fetchone():
                admin_password = generate_password_hash('admin123')
                cursor.execute("""
                    INSERT INTO users (username, password_hash, user_type)
                    VALUES ('admin', ?, 'admin')
                """, (admin_password,))
                logger.info("Created default admin user")
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_user(self, username, password, phone, email, user_type='member'):
        """Create new user account"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            # First create member
            cursor.execute('''
                INSERT INTO members (name, phone, email, monthly_amount)
                VALUES (?, ?, ?, ?)
            ''', (username, phone, email, 50.00))
            
            member_id = cursor.lastrowid
            
            # Then create user account
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, user_type, member_id)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, user_type, member_id))
            
            conn.commit()
            conn.close()
            logger.info(f"Created user: {username}")
            return member_id
            
        except sqlite3.IntegrityError as e:
            logger.error(f"User creation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in create_user: {e}")
            return None
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.password_hash, u.user_type, u.member_id, 
                       m.name, m.phone, m.email
                FROM users u 
                LEFT JOIN members m ON u.member_id = m.id 
                WHERE u.username = ?
            ''', (username,))
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                return None
                
            # Check if it's the admin user (no member_id)
            if user[3] is None:
                if check_password_hash(user[1], password):
                    return {
                        'id': user[0],
                        'username': username,
                        'user_type': user[2],
                        'member_id': None,
                        'name': 'Administrator',
                        'phone': '',
                        'email': ''
                    }
            else:
                if user and check_password_hash(user[1], password):
                    return {
                        'id': user[0],
                        'username': username,
                        'user_type': user[2],
                        'member_id': user[3],
                        'name': user[4],
                        'phone': user[5],
                        'email': user[6]
                    }
            
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def get_pool_stats(self):
        """Get pool statistics"""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Total members
            cursor.execute('SELECT COUNT(*) FROM members WHERE status = "active"')
            total_members = cursor.fetchone()[0] or 0

            # Monthly expected revenue
            cursor.execute('SELECT COALESCE(SUM(monthly_amount), 0) FROM members WHERE status = "active"')
            monthly_expected = cursor.fetchone()[0] or 0

            # Total contributions
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE status = "paid"')
            total_contributions = cursor.fetchone()[0] or 0

            # Total payouts
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM payouts WHERE status = "paid"')
            total_payouts = cursor.fetchone()[0] or 0

            # Pending claims
            cursor.execute('SELECT COUNT(*) FROM claims WHERE status = "pending"')
            pending_claims_count = cursor.fetchone()[0] or 0

            # Approved claims
            cursor.execute('SELECT COUNT(*) FROM claims WHERE status = "approved"')
            approved_claims_count = cursor.fetchone()[0] or 0

            # Total claims
            cursor.execute('SELECT COUNT(*) FROM claims')
            total_claims_count = cursor.fetchone()[0] or 0

            conn.close()
            
            return {
                'current_balance': float(total_contributions - total_payouts),
                'total_contributions': float(total_contributions),
                'total_payouts': float(total_payouts),
                'member_count': total_members,
                'pending_claims': pending_claims_count,
                'approved_claims': approved_claims_count,
                'total_claims': total_claims_count,
                'monthly_expected': float(monthly_expected)
            }
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {
                'current_balance': 0,
                'total_contributions': 0,
                'total_payouts': 0,
                'member_count': 0,
                'pending_claims': 0,
                'approved_claims': 0,
                'total_claims': 0,
                'monthly_expected': 0
            }
    
    def get_all_members(self):
        """Get all members for admin view"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.*, 
                       (SELECT COUNT(*) FROM claims WHERE member_id = m.id) as total_claims,
                       (SELECT COUNT(*) FROM contributions WHERE member_id = m.id) as total_contributions,
                       (SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE member_id = m.id AND status = "paid") as total_contributed
                FROM members m
                ORDER BY m.created_at DESC
            ''')
            
            columns = [desc[0] for desc in cursor.description]
            members = []
            for row in cursor.fetchall():
                member = dict(zip(columns, row))
                # Convert decimal to float
                for key in ['monthly_amount', 'total_contributed']:
                    if key in member:
                        member[key] = float(member[key])
                members.append(member)
            
            conn.close()
            return members
        except Exception as e:
            logger.error(f"Error getting all members: {e}")
            return []
    
    def get_recent_activity(self):
        """Get recent activity for dashboard"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            # Recent contributions
            cursor.execute('''
                SELECT c.amount, c.created_at, m.name 
                FROM contributions c 
                JOIN members m ON c.member_id = m.id 
                WHERE c.status = "paid"
                ORDER BY c.created_at DESC 
                LIMIT 5
            ''')
            recent_contributions = cursor.fetchall()
            
            # Recent claims
            cursor.execute('''
                SELECT cl.amount, cl.created_at, cl.status, m.name 
                FROM claims cl 
                JOIN members m ON cl.member_id = m.id 
                ORDER BY cl.created_at DESC 
                LIMIT 5
            ''')
            recent_claims = cursor.fetchall()
            
            conn.close()
            
            return {
                'recent_contributions': recent_contributions,
                'recent_claims': recent_claims
            }
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return {'recent_contributions': [], 'recent_claims': []}
    
    def get_member_by_user_id(self, user_id):
        """Get member by user ID"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.id, m.name, m.phone, m.email, m.monthly_amount, m.status
                FROM members m 
                JOIN users u ON m.id = u.member_id 
                WHERE u.id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "phone": row[2],
                    "email": row[3],
                    "monthly_amount": float(row[4]),
                    "status": row[5]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting member: {e}")
            return None
    
    def get_pending_claims(self):
        """Get all pending claims for admin review"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, m.name as member_name, m.phone, m.email
                FROM claims c
                JOIN members m ON c.member_id = m.id
                WHERE c.status = 'pending'
                ORDER BY c.created_at DESC
            ''')
            
            columns = [desc[0] for desc in cursor.description]
            claims = []
            for row in cursor.fetchall():
                claim = dict(zip(columns, row))
                if 'amount' in claim:
                    claim['amount'] = float(claim['amount'])
                claims.append(claim)
            
            conn.close()
            return claims
        except Exception as e:
            logger.error(f"Error getting pending claims: {e}")
            return []
    
    def get_all_claims(self):
        """Get all claims for admin view"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, m.name as member_name, u.username as reviewer_name
                FROM claims c
                JOIN members m ON c.member_id = m.id
                LEFT JOIN users u ON c.reviewed_by = u.id
                ORDER BY c.created_at DESC
            ''')
            
            columns = [desc[0] for desc in cursor.description]
            claims = []
            for row in cursor.fetchall():
                claim = dict(zip(columns, row))
                if 'amount' in claim:
                    claim['amount'] = float(claim['amount'])
                claims.append(claim)
            
            conn.close()
            return claims
        except Exception as e:
            logger.error(f"Error getting all claims: {e}")
            return []
    
    def update_claim_status(self, claim_id, status, admin_id, admin_notes=None):
        """Update claim status and record admin action"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            logger.info(f"Updating claim {claim_id} to status {status} by admin {admin_id}")
            
            cursor.execute('''
                UPDATE claims 
                SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP, admin_notes = ?
                WHERE id = ?
            ''', (status, admin_id, admin_notes, claim_id))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Claim update affected {affected_rows} rows")
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error updating claim status: {e}")
            return False
    
    def debug_claim_update(self, claim_id, admin_id):
        """Debug method to check claim and admin user"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            # Check if claim exists
            cursor.execute('SELECT id, status, member_id FROM claims WHERE id = ?', (claim_id,))
            claim = cursor.fetchone()
            
            # Check if admin user exists
            cursor.execute('SELECT id, username, user_type FROM users WHERE id = ?', (admin_id,))
            admin = cursor.fetchone()
            
            conn.close()
            
            return {
                'claim_exists': bool(claim),
                'claim_details': claim,
                'admin_exists': bool(admin),
                'admin_details': admin
            }
        except Exception as e:
            logger.error(f"Debug error: {e}")
            return {'error': str(e)}
    
    def get_member_contributions(self, member_id):
        """Get member contributions"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT amount, status, created_at 
                FROM contributions 
                WHERE member_id = ? 
                ORDER BY created_at DESC
            ''', (member_id,))
            contributions = cursor.fetchall()
            conn.close()
            return contributions
        except Exception as e:
            logger.error(f"Error getting contributions: {e}")
            return []
    
    def get_member_claims(self, member_id):
        """Get member claims"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT amount, status, description, type, hospital, priority, created_at 
                FROM claims 
                WHERE member_id = ? 
                ORDER BY created_at DESC
            ''', (member_id,))
            claims = cursor.fetchall()
            conn.close()
            return claims
        except Exception as e:
            logger.error(f"Error getting claims: {e}")
            return []
    
    def record_contribution(self, member_id, amount, reference_id, status='paid'):
        """Record contribution"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contributions (member_id, amount, payment_reference, status, paid_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (member_id, amount, reference_id, status))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error recording contribution: {e}")
            return False
    
    def create_claim(self, member_id, amount, description, claim_type='General', hospital=None, priority='normal'):
        """Submit new claim"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO claims (member_id, amount, description, type, hospital, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (member_id, amount, description, claim_type, hospital, priority))
            claim_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return claim_id
        except Exception as e:
            logger.error(f"Error submitting claim: {e}")
            return None
    
    def get_member_by_id(self, member_id):
        """Get member by ID"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone, email, monthly_amount, status
                FROM members WHERE id = ?
            ''', (member_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "phone": row[2],
                    "email": row[3],
                    "monthly_amount": float(row[4]),
                    "status": row[5]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting member: {e}")
            return None
    
    def update_member_phone(self, member_id, new_phone):
        """Update member phone number"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE members SET phone = ? WHERE id = ?
            ''', (new_phone, member_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating phone: {e}")
            return False 