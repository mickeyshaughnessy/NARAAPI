"""
API Server with Data Privacy Features
"""

import flask, os, json, time
from flask_cors import CORS
from functools import wraps
import secrets

# Import handlers
from handlers import (
    query_archives,
    apply_filters,
    redact_names,
    add_differential_privacy,
    combined_query_with_privacy
)

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

# Data privacy endpoints
@app.route('/api/query', methods=['POST'])
@token_required
def handle_query(current_user):
    """Endpoint for querying archives"""
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
            
        # Add user_id for auditing
        data['user_id'] = current_user
        
        response, status = query_archives(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/api/filter', methods=['POST'])
@token_required
def handle_filter(current_user):
    """Endpoint for filtering data"""
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
            
        # Add user_id for auditing
        data['user_id'] = current_user
        
        response, status = apply_filters(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/api/redact', methods=['POST'])
@token_required
def handle_redact(current_user):
    """Endpoint for redacting names"""
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
            
        # Add user_id for auditing
        data['user_id'] = current_user
        
        response, status = redact_names(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/api/privacy', methods=['POST'])
@token_required
def handle_privacy(current_user):
    """Endpoint for adding differential privacy"""
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
            
        # Add user_id for auditing
        data['user_id'] = current_user
        
        response, status = add_differential_privacy(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/api/secure-query', methods=['POST'])
@token_required
def handle_secure_query(current_user):
    """Combined endpoint for secure data querying with privacy protections"""
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
            
        # Add user_id for auditing
        data['user_id'] = current_user
        
        response, status = combined_query_with_privacy(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

# Add health check endpoint for privacy services
@app.route('/api/privacy-services/health', methods=['GET'])
def privacy_health():
    """Health check for privacy services"""
    return flask.jsonify({
        "status": "healthy",
        "services": {
            "query": "available",
            "filter": "available",
            "redact": "available", 
            "privacy": "available"
        }
    }), 200

# Add OpenAPI documentation for the API
@app.route('/api/docs', methods=['GET'])
def api_docs():
    docs = {
        "openapi": "3.0.0",
        "info": {
            "title": "Data Privacy API",
            "description": "API for querying archives with privacy protections",
            "version": "1.0.0"
        },
        "paths": {
            "/api/query": {
                "post": {
                    "summary": "Query archives",
                    "description": "Query data from archives based on provided parameters",
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query_type": {"type": "string"},
                                        "time_range": {"type": "object"},
                                        "filters": {"type": "object"},
                                        "limit": {"type": "integer"},
                                        "offset": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful query"
                        }
                    }
                }
            },
            "/api/filter": {
                "post": {
                    "summary": "Filter data",
                    "description": "Apply advanced filtering to data",
                    "security": [{"BearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Successful filtering"
                        }
                    }
                }
            },
            "/api/redact": {
                "post": {
                    "summary": "Redact names",
                    "description": "Redact personal names from data",
                    "security": [{"BearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Successful redaction"
                        }
                    }
                }
            },
            "/api/privacy": {
                "post": {
                    "summary": "Add differential privacy",
                    "description": "Add differential privacy noise to data",
                    "security": [{"BearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Successful privacy protection"
                        }
                    }
                }
            },
            "/api/secure-query": {
                "post": {
                    "summary": "Secure query with privacy protections",
                    "description": "Combined endpoint for secure data querying with filtering, redaction, and differential privacy",
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query_type": {"type": "string"},
                                        "time_range": {"type": "object"},
                                        "query_filters": {"type": "object"},
                                        "filters": {"type": "object"},
                                        "fields_to_redact": {"type": "array"},
                                        "numeric_fields": {"type": "array"},
                                        "epsilon": {"type": "number"},
                                        "sensitivity": {"type": "number"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful secure query"
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer"
                }
            }
        }
    }
    return flask.jsonify(docs), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT, debug=True)

application = app