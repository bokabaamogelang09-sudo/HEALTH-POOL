from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import uuid
import os
import logging
from functools import wraps
import traceback
from datetime import datetime

from database_manager import CommunityPoolManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = False

# Initialize database
db = CommunityPoolManager()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('member_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('user_type') == 'admin':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('member_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('Username and password are required.', 'danger')
                return render_template('login.html')
            
            user = db.authenticate_user(username, password)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']
                session['member_id'] = user['member_id']
                session['name'] = user['name']
                session['phone'] = user['phone']
                session['email'] = user['email']
                
                flash(f'Welcome back, {user["name"]}!', 'success')
                
                if user['user_type'] == 'admin':
                    return redirect(url_for('dashboard'))
                else:
                    return redirect(url_for('member_dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Login error: {e}\n{traceback.format_exc()}")
        flash('An error occurred during login.', 'danger')
        return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')

            if not all([username, phone, email, password]):
                flash('All fields are required.', 'danger')
                return render_template('register.html')

            if not phone.replace(' ', '').replace('-', '').isdigit():
                flash('Please enter a valid phone number.', 'danger')
                return render_template('register.html')

            member_id = db.create_user(username, password, phone, email)
            if member_id:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Username, email or phone number already exists.', 'danger')
                return render_template('register.html')
        
        return render_template('register.html')
    except Exception as e:
        logger.error(f"Registration error: {e}\n{traceback.format_exc()}")
        flash('An error occurred during registration.', 'danger')
        return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    try:
        stats = db.get_pool_stats()
        pending_claims_list = db.get_pending_claims()
        recent_activity = db.get_recent_activity()
        all_members = db.get_all_members()
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             pending_claims_list=pending_claims_list,
                             recent_activity=recent_activity,
                             all_members=all_members)
    except Exception as e:
        logger.error(f"Dashboard error: {e}\n{traceback.format_exc()}")
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('index'))

@app.route('/admin/members')
@login_required
@admin_required
def admin_members():
    try:
        members = db.get_all_members()
        return render_template('admin_members.html', members=members)
    except Exception as e:
        logger.error(f"Admin members error: {e}\n{traceback.format_exc()}")
        flash('Error loading members.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/admin/claims')
@login_required
@admin_required
def admin_claims():
    try:
        claims = db.get_all_claims()
        return render_template('admin_claims.html', claims=claims)
    except Exception as e:
        logger.error(f"Admin claims error: {e}\n{traceback.format_exc()}")
        flash('Error loading claims.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/admin/approve_claim/<int:claim_id>', methods=['POST'])
@login_required
@admin_required
def approve_claim(claim_id):
    try:
        admin_notes = request.form.get('admin_notes', '').strip()
        admin_user_id = session['user_id']
        
        if db.update_claim_status(claim_id, 'approved', admin_user_id, admin_notes):
            flash('Claim approved successfully!', 'success')
        else:
            flash('Error approving claim.', 'danger')
    except Exception as e:
        logger.error(f"Approve claim error: {e}\n{traceback.format_exc()}")
        flash('Error approving claim.', 'danger')
    return redirect(url_for('admin_claims'))

@app.route('/admin/decline_claim/<int:claim_id>', methods=['POST'])
@login_required
@admin_required
def decline_claim(claim_id):
    try:
        admin_notes = request.form.get('admin_notes', '').strip()
        if not admin_notes:
            flash('Please provide a reason for declining the claim.', 'warning')
            return redirect(url_for('admin_claims'))
            
        admin_user_id = session['user_id']
            
        if db.update_claim_status(claim_id, 'declined', admin_user_id, admin_notes):
            flash('Claim declined successfully!', 'success')
        else:
            flash('Error declining claim.', 'danger')
    except Exception as e:
        logger.error(f"Decline claim error: {e}\n{traceback.format_exc()}")
        flash('Error declining claim.', 'danger')
    return redirect(url_for('admin_claims'))

@app.route('/member_dashboard')
@login_required
def member_dashboard():
    try:
        if session.get('user_type') == 'admin':
            return redirect(url_for('dashboard'))
        
        member = db.get_member_by_user_id(session['user_id'])
        if not member:
            flash('Member profile not found.', 'danger')
            return redirect(url_for('logout'))
        
        contributions = db.get_member_contributions(member['id'])
        claims = db.get_member_claims(member['id'])
        
        return render_template('member_dashboard.html', 
                             member=member, 
                             contributions=contributions,
                             claims=claims)
    except Exception as e:
        logger.error(f"Member dashboard error: {e}\n{traceback.format_exc()}")
        flash('Error loading your dashboard.', 'danger')
        return redirect(url_for('index'))

@app.route('/contribute', methods=['GET', 'POST'])
@login_required
def contribute():
    try:
        if session.get('user_type') == 'admin':
            flash('Admins cannot make contributions.', 'warning')
            return redirect(url_for('dashboard'))
        
        member = db.get_member_by_user_id(session['user_id'])
        if not member:
            flash('Member profile not found.', 'danger')
            return redirect(url_for('member_dashboard'))
        
        if request.method == 'POST':
            try:
                amount = float(request.form.get('amount', 0))
            except ValueError:
                flash('Please enter a valid amount.', 'danger')
                return redirect(url_for('contribute'))
            
            if amount <= 0:
                flash('Please enter a valid amount.', 'danger')
                return redirect(url_for('contribute'))
            
            reference_id = str(uuid.uuid4())
            
            if db.record_contribution(member['id'], amount, reference_id):
                flash(f'Contribution of R{amount:.2f} successful!', 'success')
                return redirect(url_for('member_dashboard'))
            else:
                flash('Error processing contribution.', 'danger')
        
        return render_template('contribute.html', member=member)
    except Exception as e:
        logger.error(f"Contribute error: {e}\n{traceback.format_exc()}")
        flash('An error occurred.', 'danger')
        return redirect(url_for('member_dashboard'))

@app.route('/submit_claim', methods=['GET', 'POST'])
@login_required
def submit_claim():
    try:
        if session.get('user_type') == 'admin':
            flash('Admins cannot submit claims.', 'warning')
            return redirect(url_for('dashboard'))
        
        member = db.get_member_by_user_id(session['user_id'])
        if not member:
            flash('Member profile not found.', 'danger')
            return redirect(url_for('member_dashboard'))
        
        if request.method == 'POST':
            description = request.form.get('description', '').strip()
            claim_type = request.form.get('type', 'General').strip()
            hospital = request.form.get('hospital', '').strip()
            priority = request.form.get('priority', 'normal')
            
            try:
                amount = float(request.form.get('amount', 0))
            except ValueError:
                flash('Please enter a valid amount.', 'danger')
                return redirect(url_for('submit_claim'))
            
            if not all([description]):
                flash('Description is required.', 'danger')
                return redirect(url_for('submit_claim'))
            
            if amount <= 0:
                flash('Please enter a valid amount.', 'danger')
                return redirect(url_for('submit_claim'))
            
            claim_id = db.create_claim(member['id'], amount, description, claim_type, hospital, priority)
            
            if claim_id:
                flash('Claim submitted successfully!', 'success')
                return redirect(url_for('member_dashboard'))
            else:
                flash('Error submitting claim.', 'danger')
        
        return render_template('submit_claim.html', member=member)
    except Exception as e:
        logger.error(f"Submit claim error: {e}\n{traceback.format_exc()}")
        flash('An error occurred.', 'danger')
        return redirect(url_for('member_dashboard'))

@app.route('/update_phone', methods=['GET', 'POST'])
@login_required
def update_phone():
    try:
        if session.get('user_type') == 'admin':
            flash('Admins cannot update phone numbers.', 'warning')
            return redirect(url_for('dashboard'))
        
        member = db.get_member_by_user_id(session['user_id'])
        if not member:
            flash('Member profile not found.', 'danger')
            return redirect(url_for('member_dashboard'))
        
        if request.method == 'POST':
            new_phone = request.form.get('phone', '').strip()
            
            if not new_phone:
                flash('Phone number is required.', 'danger')
                return redirect(url_for('update_phone'))
            
            if not new_phone.replace(' ', '').replace('-', '').isdigit():
                flash('Please enter a valid phone number.', 'danger')
                return redirect(url_for('update_phone'))
            
            if db.update_member_phone(member['id'], new_phone):
                session['phone'] = new_phone
                flash('Phone number updated successfully!', 'success')
                return redirect(url_for('member_dashboard'))
            else:
                flash('Error updating phone number.', 'danger')
        
        return render_template('update_phone.html', member=member)
    except Exception as e:
        logger.error(f"Update phone error: {e}\n{traceback.format_exc()}")
        flash('An error occurred.', 'danger')
        return redirect(url_for('member_dashboard'))

@app.route('/debug/admin')
@login_required
@admin_required
def debug_admin():
    """Debug admin functionality"""
    try:
        admin_id = session['user_id']
        pending_claims = db.get_pending_claims()
        stats = db.get_pool_stats()
        members = db.get_all_members()
        
        debug_info = {
            'admin_id': admin_id,
            'total_pending_claims': len(pending_claims),
            'pool_stats': stats,
            'total_members': len(members),
            'session_data': dict(session)
        }
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}\n{traceback.format_exc()}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("=" * 50)
    print("Community Health Pool Application - South Africa")
    print("=" * 50)
    print("Starting server...")
    print("Access at: http://localhost:5000")
    print("Admin login: admin / admin123")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=5000)