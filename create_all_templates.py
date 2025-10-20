import os

# Create templates directory
os.makedirs('templates', exist_ok=True)
print("✓ Templates directory created/verified")

# Template contents dictionary
templates = {}

# Base template - simplified version that will work
templates['base.html'] = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Community Health Pool{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .navbar { background: rgba(255,255,255,0.95)!important; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .content-wrapper { margin-top: 80px; margin-bottom: 40px; }
        .card { border: none; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .stat-card { background: white; border-radius: 15px; padding: 25px; margin-bottom: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); }
        .stat-icon { width: 60px; height: 60px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light fixed-top">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-heartbeat"></i> Health Pool</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto">
                    {% if session.user_id %}
                        <li class="nav-item"><a class="nav-link" href="/logout">Logout</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>
    <div class="container content-wrapper">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

templates['login.html'] = '''{% extends "base.html" %}
{% block title %}Login{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-5">
        <div class="card">
            <div class="card-body p-5">
                <h2 class="text-center mb-4">Login</h2>
                <form method="POST">
                    <div class="mb-3">
                        <label>Username</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label>Password</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Login</button>
                </form>
                <p class="text-center mt-3">
                    Don't have an account? <a href="/register">Register</a>
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

templates['register.html'] = '''{% extends "base.html" %}
{% block title %}Register{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-5">
        <div class="card">
            <div class="card-body p-5">
                <h2 class="text-center mb-4">Register</h2>
                <form method="POST">
                    <div class="mb-3">
                        <label>Username</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label>Password</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Register</button>
                </form>
                <p class="text-center mt-3">
                    Already have an account? <a href="/login">Login</a>
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

templates['dashboard.html'] = '''{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<h1 class="text-white mb-4">Admin Dashboard</h1>
<div class="row">
    <div class="col-md-3">
        <div class="stat-card">
            <h6>Current Balance</h6>
            <h3>${{ "%.2f"|format(stats.current_balance) }}</h3>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card">
            <h6>Total Contributions</h6>
            <h3>${{ "%.2f"|format(stats.total_contributions) }}</h3>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card">
            <h6>Total Payouts</h6>
            <h3>${{ "%.2f"|format(stats.total_payouts) }}</h3>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card">
            <h6>Active Members</h6>
            <h3>{{ stats.member_count }}</h3>
        </div>
    </div>
</div>
{% endblock %}'''

templates['member_dashboard.html'] = '''{% extends "base.html" %}
{% block title %}My Dashboard{% endblock %}
{% block content %}
<h1 class="text-white mb-4">Welcome, {{ member.name }}</h1>
<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-body">
                <h5>Profile</h5>
                <p><strong>Name:</strong> {{ member.name }}</p>
                <p><strong>Phone:</strong> {{ member.phone }}</p>
                <p><strong>Plan:</strong> {{ member.plan }}</p>
                <p><strong>Monthly:</strong> ${{ "%.2f"|format(member.monthly_amount) }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-body">
                <h5>Quick Actions</h5>
                <a href="/contribute" class="btn btn-primary w-100 mb-2">Make Contribution</a>
                <a href="/submit_claim" class="btn btn-success w-100">Submit Claim</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

templates['contribute.html'] = '''{% extends "base.html" %}
{% block title %}Contribute{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-body p-4">
                <h2 class="mb-4">Make Contribution</h2>
                <form method="POST">
                    <div class="mb-3">
                        <label>Amount</label>
                        <input type="number" class="form-control" name="amount" 
                               value="{{ member.monthly_amount }}" step="0.01" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Submit</button>
                    <a href="/member_dashboard" class="btn btn-outline-secondary w-100 mt-2">Back</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

templates['submit_claim.html'] = '''{% extends "base.html" %}
{% block title %}Submit Claim{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-body p-4">
                <h2 class="mb-4">Submit Medical Claim</h2>
                <form method="POST">
                    <div class="mb-3">
                        <label>Claim Type</label>
                        <select class="form-select" name="type" required>
                            <option value="">Select type...</option>
                            <option value="emergency">Emergency</option>
                            <option value="hospitalization">Hospitalization</option>
                            <option value="medication">Medication</option>
                            <option value="consultation">Consultation</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label>Amount</label>
                        <input type="number" class="form-control" name="amount" step="0.01" required>
                    </div>
                    <div class="mb-3">
                        <label>Hospital</label>
                        <input type="text" class="form-control" name="hospital" required>
                    </div>
                    <div class="mb-3">
                        <label>Description</label>
                        <textarea class="form-control" name="description" rows="4" required></textarea>
                    </div>
                    <div class="mb-3">
                        <label>Priority</label>
                        <select class="form-select" name="priority">
                            <option value="normal">Normal</option>
                            <option value="urgent">Urgent</option>
                            <option value="emergency">Emergency</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-success w-100">Submit Claim</button>
                    <a href="/member_dashboard" class="btn btn-outline-secondary w-100 mt-2">Back</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

templates['404.html'] = '''{% extends "base.html" %}
{% block title %}404 Not Found{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 text-center">
        <div class="card">
            <div class="card-body p-5">
                <h1 class="display-1">404</h1>
                <h3>Page Not Found</h3>
                <p class="text-muted">The page you're looking for doesn't exist.</p>
                <a href="/" class="btn btn-primary">Go Home</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

templates['500.html'] = '''{% extends "base.html" %}
{% block title %}500 Error{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 text-center">
        <div class="card">
            <div class="card-body p-5">
                <h1 class="display-1">500</h1>
                <h3>Server Error</h3>
                <p class="text-muted">Something went wrong. Please try again later.</p>
                <a href="/" class="btn btn-primary">Go Home</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

# Write all templates
for filename, content in templates.items():
    filepath = os.path.join('templates', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Created {filename}")

print(f"\n✓ Successfully created {len(templates)} template files!")
print("\nYou can now run: python app.py")