"""
Utility functions for the API server
"""

import redis
import hashlib
import secrets
import bcrypt
import config
import time
import json
from typing import Dict, Any, Optional, Tuple

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=getattr(config, 'REDIS_HOST', 'localhost'),
        port=getattr(config, 'REDIS_PORT', 6379),
        db=getattr(config, 'REDIS_DB', 0),
        password=getattr(config, 'REDIS_PASSWORD', None),
        decode_responses=True
    )
    redis_client.ping()  # Test connection
except redis.ConnectionError as e:
    print(f"Warning: Redis connection failed: {e}")
    # Create a mock Redis client for development if needed
    class MockRedis:
        def __init__(self):
            self.data = {}
            
        def get(self, key):
            return self.data.get(key)
            
        def set(self, key, value, ex=None):
            self.data[key] = value
            return True
            
        def delete(self, key):
            if key in self.data:
                del self.data[key]
            return True
            
        def exists(self, key):
            return key in self.data
            
        def expire(self, key, time):
            return True
            
        def rpush(self, key, value):
            if key not in self.data:
                self.data[key] = []
            self.data[key].append(value)
            return len(self.data[key])
            
        def lrange(self, key, start, end):
            if key not in self.data:
                return []
            return self.data[key][start:end if end != -1 else None]
    
    print("Using mock Redis client for development")
    redis_client = MockRedis()

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Parameters:
    - password: Plain text password
    
    Returns:
    - Hashed password
    """
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verify a password against its hash
    
    Parameters:
    - stored_password: Hashed password from database
    - provided_password: Plain text password to check
    
    Returns:
    - True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(provided_password.encode(), stored_password.encode())
    except Exception:
        return False

def generate_token() -> str:
    """
    Generate a secure random token
    
    Returns:
    - Random token string
    """
    return secrets.token_hex(32)

def store_token(username: str, token: str, expires_in: int = 86400) -> bool:
    """
    Store a token in Redis with expiration
    
    Parameters:
    - username: Username associated with the token
    - token: The token to store
    - expires_in: Token expiration time in seconds (default: 24 hours)
    
    Returns:
    - True if successful, False otherwise
    """
    try:
        # Store token -> username mapping
        redis_client.set(f"auth_token:{token}", username, ex=expires_in)
        
        # Store username -> tokens mapping for potential revocation
        user_tokens_key = f"user_tokens:{username}"
        redis_client.rpush(user_tokens_key, token)
        redis_client.expire(user_tokens_key, expires_in * 2)  # Longer expiry for user tracking
        
        return True
    except Exception as e:
        print(f"Error storing token: {e}")
        return False

def revoke_token(token: str) -> bool:
    """
    Revoke a token
    
    Parameters:
    - token: The token to revoke
    
    Returns:
    - True if successful, False otherwise
    """
    try:
        # Get username associated with token
        username = redis_client.get(f"auth_token:{token}")
        if not username:
            return False
            
        # Delete token
        redis_client.delete(f"auth_token:{token}")
        
        return True
    except Exception as e:
        print(f"Error revoking token: {e}")
        return False

def revoke_all_user_tokens(username: str) -> bool:
    """
    Revoke all tokens for a user
    
    Parameters:
    - username: The username whose tokens should be revoked
    
    Returns:
    - True if successful, False otherwise
    """
    try:
        # Get all tokens for user
        user_tokens_key = f"user_tokens:{username}"
        tokens = redis_client.lrange(user_tokens_key, 0, -1)
        
        # Delete each token
        for token in tokens:
            redis_client.delete(f"auth_token:{token}")
            
        # Delete the user's token list
        redis_client.delete(user_tokens_key)
        
        return True
    except Exception as e:
        print(f"Error revoking user tokens: {e}")
        return False

def log_activity(username: str, action: str, details: Dict[str, Any] = None) -> bool:
    """
    Log user activity
    
    Parameters:
    - username: Username performing the action
    - action: Description of the action
    - details: Additional details about the action
    
    Returns:
    - True if successful, False otherwise
    """
    try:
        log_entry = {
            'timestamp': int(time.time()),
            'username': username,
            'action': action,
            'details': details or {}
        }
        
        # Store in Redis list with auto-expiry (30 days)
        key = f"activity_log:{username}:{time.strftime('%Y-%m')}"
        redis_client.rpush(key, json.dumps(log_entry))
        redis_client.expire(key, 30 * 24 * 60 * 60)  # 30 days in seconds
        
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False

def validate_data(data: Dict[str, Any], required_fields: list) -> Tuple[bool, Optional[str]]:
    """
    Validate that required fields are present in the data
    
    Parameters:
    - data: Data to validate
    - required_fields: List of required field names
    
    Returns:
    - Tuple of (is_valid, error_message)
    """
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing required field: {field}"
    return True, None