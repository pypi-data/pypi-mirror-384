"""Example Flask application with cynapse monitoring."""

try:
    from flask import Flask, jsonify, request
    from cynapse.integrations.flask import FlaskMonitor
    FLASK_AVAILABLE = True
except ImportError:
    print("Flask not installed. Install with: pip install flask")
    FLASK_AVAILABLE = False
    exit(1)

# create flask app
app = Flask(__name__)

# initialize cynapse monitor
monitor = FlaskMonitor(
    app, 
    interval=5.0,
    protect_routes=['admin', 'api/payment']
)

@app.route('/')
def index():
    """Public endpoint."""
    return jsonify({
        'message': 'Welcome to the secure Flask app!',
        'status': 'public'
    })

@app.route('/admin')
def admin():
    """Protected admin endpoint."""
    return jsonify({
        'message': 'Admin panel',
        'status': 'protected'
    })

@app.route('/api/payment', methods=['POST'])
def payment():
    """Protected payment endpoint."""
    data = request.get_json() or {}
    amount = data.get('amount', 0)
    
    return jsonify({
        'message': f'Processing payment of ${amount}',
        'status': 'protected'
    })

@app.route('/secure')
@monitor.protect_endpoint
def secure_endpoint():
    """Explicitly protected endpoint using decorator."""
    return jsonify({
        'message': 'This endpoint is explicitly protected',
        'status': 'protected'
    })

@app.route('/status')
def status():
    """Get monitor status."""
    mon_status = monitor.monitor.get_status()
    
    return jsonify({
        'running': mon_status.running,
        'checks_performed': mon_status.checks_performed,
        'tamper_events': mon_status.tamper_events,
        'protected_functions': mon_status.protected_functions
    })

if __name__ == '__main__':
    print("Starting Flask app with cynapse monitoring...")
    print("Visit http://localhost:5000 to test")
    print("Try these endpoints:")
    print("  - /")
    print("  - /admin (protected)")
    print("  - /secure (protected)")
    print("  - /status")
    
    app.run(debug=True, port=5000)
