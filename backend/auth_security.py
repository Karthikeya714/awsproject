"""Simple in-memory user authentication (no AWS/Docker needed)."""
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class SimpleUserAuth:
    """Simple in-memory authentication for local testing."""
    
    def __init__(self):
        """Initialize in-memory storage."""
        self.users = {}  # {email: user_data}
        self.sessions = {}  # {session_id: user_data}
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt."""
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def _generate_salt(self) -> str:
        """Generate random salt."""
        return secrets.token_hex(16)
    
    def _generate_user_id(self) -> str:
        """Generate unique user ID."""
        return f"user_{secrets.token_urlsafe(16)}"
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return secrets.token_urlsafe(32)
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> tuple[bool, str]:
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, ""
    
    def signup(self, email: str, password: str, full_name: str) -> tuple[bool, str, Optional[str]]:
        """Create new user account."""
        try:
            # Validate email
            if not self._validate_email(email):
                return False, "Invalid email format", None
            
            # Validate password
            is_valid, error_msg = self._validate_password(password)
            if not is_valid:
                return False, error_msg, None
            
            # Check if email already exists
            if email.lower() in self.users:
                return False, "Email already registered", None
            
            # Create user
            user_id = self._generate_user_id()
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            
            self.users[email.lower()] = {
                'user_id': user_id,
                'email': email.lower(),
                'password_hash': password_hash,
                'salt': salt,
                'full_name': full_name,
                'created_at': datetime.utcnow().isoformat(),
                'last_login': None,
                'is_active': True,
                'role': 'user'
            }
            
            return True, "Account created successfully!", user_id
            
        except Exception as e:
            return False, f"Signup failed: {str(e)}", None
    
    def signin(self, email: str, password: str) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """Authenticate user and create session."""
        try:
            # Get user by email
            user = self.users.get(email.lower())
            
            if not user:
                return False, "Invalid email or password", None
            
            # Check if account is active
            if not user.get('is_active', True):
                return False, "Account is inactive", None
            
            # Verify password
            password_hash = self._hash_password(password, user['salt'])
            if password_hash != user['password_hash']:
                return False, "Invalid email or password", None
            
            # Update last login
            user['last_login'] = datetime.utcnow().isoformat()
            
            # Create session
            session_id = self._generate_session_id()
            self.sessions[session_id] = {
                'session_id': session_id,
                'user_id': user['user_id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                'role': user.get('role', 'user')
            }
            
            return True, "Login successful!", {
                'session_id': session_id,
                'user_id': user['user_id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user.get('role', 'user')
            }
            
        except Exception as e:
            return False, f"Login failed: {str(e)}", None
    
    def validate_session(self, session_id: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Validate session."""
        try:
            session = self.sessions.get(session_id)
            
            if not session:
                return False, None
            
            # Check if session expired
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.utcnow() > expires_at:
                del self.sessions[session_id]
                return False, None
            
            return True, {
                'user_id': session['user_id'],
                'email': session['email'],
                'full_name': session['full_name'],
                'session_id': session_id
            }
            
        except Exception as e:
            print(f"Session validation error: {str(e)}")
            return False, None
    
    def logout(self, session_id: str) -> bool:
        """Logout user."""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
            return True
        except Exception as e:
            print(f"Logout error: {str(e)}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile."""
        try:
            for user in self.users.values():
                if user['user_id'] == user_id:
                    return {
                        'user_id': user['user_id'],
                        'email': user['email'],
                        'full_name': user['full_name'],
                        'created_at': user['created_at'],
                        'last_login': user.get('last_login'),
                        'role': user.get('role', 'user')
                    }
            return None
        except Exception as e:
            print(f"Get profile error: {str(e)}")
            return None
