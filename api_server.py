"""
Generic API Server
"""

import flask, os, json, time
from flask_cors import CORS
from functools import wraps
import secrets

# Import handlers
# Add your handler imports here

# Import utilities
from utils import redis_client, verify_password
import config

app = flask.Flask(__name__, static_url_path='', static_folder='static')
CORS(app, resources={r"/*": {"origins": "*"}})

def log_request(request, response_code):
    """Log request details to Redis"""
    try:
        log_entry = {
            'timestamp': int(time.time()),
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'status': response_code,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Add username if authenticated
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(" ")[-1]
            username = redis_client.get(f"auth_token:{token}")
            if username:
                log_entry['username'] = username.decode()

        # Store in Redis list with auto-expiry (7 days)
        key = f"request_log:{time.strftime('%Y-%m-%d')}"
        redis_client.rpush(key, json.dumps(log_entry))
        redis_client.expire(key, 7 * 24 * 60 * 60)  # 7 days in seconds
        
    except Exception as e:
        print(f"Logging error: {str(e)}")

@app.after_request
def after_request(response):
    """Log after each request"""
    log_request(flask.request, response.status_code)
    return response

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = flask.request.headers.get('Authorization')
        if not auth_header:
            return flask.jsonify({'error': 'Token is missing'}), 401
        token = auth_header.split(" ")[-1]
        username = redis_client.get(f"auth_token:{token}")
        if not username:
            return flask.jsonify({'error': 'Token is invalid or expired'}), 401
        return f(username.decode(), *args, **kwargs)
    return decorated

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    frontend_dir = "static"
    
    if not path:
        path = 'index.html'
    
    path = os.path.normpath(path).lstrip('/')
    full_path = os.path.join(frontend_dir, path)
    
    if os.path.isfile(full_path):
        return flask.send_from_directory(frontend_dir, path)
    
    index_path = os.path.join(full_path, 'index.html')
    if os.path.isfile(index_path):
        return flask.send_from_directory(full_path, 'index.html')
    
    return flask.send_from_directory(frontend_dir, 'index.html')

@app.route('/ping', methods=['POST', 'GET'])
def ping():
    return flask.jsonify({"message": "ok"}), 200

@app.route('/auth/register', methods=['POST'])
def register():
    try:
        data = flask.request.get_json()
        # Replace with your registration handler
        # response, status = auth_register(data)
        response, status = {"message": "Registration endpoint"}, 200
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = flask.request.get_json()
        # Replace with your login handler
        # response, status = auth_login(data)
        response, status = {"message": "Login endpoint"}, 200
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/api/protected-resource', methods=['GET'])
@token_required
def protected_resource(current_user):
    try:
        # Get query parameters
        data = flask.request.args.to_dict()
        data['username'] = current_user
        # Replace with your handler
        # response, status = get_resource(data)
        response, status = {"message": "This is a protected resource", "user": current_user}, 200
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/api/public-resource', methods=['GET'])
def public_resource():
    try:
        # Get query parameters
        data = flask.request.args.to_dict()
        # Replace with your handler
        response, status = {"message": "This is a public resource"}, 200
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

# Example of a POST endpoint with authentication
@app.route('/api/user-data', methods=['POST'])
@token_required
def handle_user_data(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        # Replace with your handler
        # response, status = process_user_data(data)
        response, status = {"message": "User data received", "user": current_user}, 200
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT, debug=True)

application = app