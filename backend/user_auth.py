"""User authentication and management module with DynamoDB storage."""
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

from backend.config import config_manager


class UserAuthManager:
    """Manages user authentication with DynamoDB storage."""
    
    def __init__(self):
        """Initialize user authentication manager."""
        self.config = config_manager.config
        
        # Check if running locally
        import os
        self.is_local = os.getenv('ENVIRONMENT', 'local') == 'local'
        
        # Initialize DynamoDB
        if self.is_local:
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url='http://localhost:4566',
                region_name=self.config.aws_region,
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
        else:
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=self.config.aws_region
            )
        
        self.users_table_name = f"{self.config.dynamodb_table}-users"
        self.sessions_table_name = f"{self.config.dynamodb_table}-sessions"
        
        # Create tables if in local mode
        if self.is_local:
            self._create_tables_if_not_exist()
    
    def _create_tables_if_not_exist(self):
        """Create DynamoDB tables for local testing."""
        try:
            # Create users table
            try:
                self.dynamodb.create_table(
                    TableName=self.users_table_name,
                    KeySchema=[
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'user_id', 'AttributeType': 'S'},
                        {'AttributeName': 'email', 'AttributeType': 'S'},
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'email-index',
                            'KeySchema': [
                                {'AttributeName': 'email', 'KeyType': 'HASH'},
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ],
                    BillingMode='PROVISIONED',
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceInUseException':
                    raise
            
            # Create sessions table
            try:
                self.dynamodb.create_table(
                    TableName=self.sessions_table_name,
                    KeySchema=[
                        {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'session_id', 'AttributeType': 'S'},
                    ],
                    BillingMode='PROVISIONED',
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceInUseException':
                    raise
                    
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using SHA-256."""
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def _generate_salt(self) -> str:
        """Generate random salt for password hashing."""
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
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
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
        """
        Create new user account.
        
        Args:
            email: User email
            password: User password
            full_name: User's full name
        
        Returns:
            Tuple of (success, message, user_id)
        """
        try:
            # Validate email
            if not self._validate_email(email):
                return False, "Invalid email format", None
            
            # Validate password
            is_valid, error_msg = self._validate_password(password)
            if not is_valid:
                return False, error_msg, None
            
            # Check if email already exists
            table = self.dynamodb.Table(self.users_table_name)
            response = table.query(
                IndexName='email-index',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            
            if response.get('Items'):
                return False, "Email already registered", None
            
            # Create user
            user_id = self._generate_user_id()
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            
            table.put_item(
                Item={
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
            )
            
            return True, "Account created successfully!", user_id
            
        except Exception as e:
            return False, f"Signup failed: {str(e)}", None
    
    def signin(self, email: str, password: str) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate user and create session.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Get user by email
            table = self.dynamodb.Table(self.users_table_name)
            response = table.query(
                IndexName='email-index',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email.lower()}
            )
            
            if not response.get('Items'):
                return False, "Invalid email or password", None
            
            user = response['Items'][0]
            
            # Check if account is active
            if not user.get('is_active', True):
                return False, "Account is inactive. Please contact support.", None
            
            # Verify password
            password_hash = self._hash_password(password, user['salt'])
            if password_hash != user['password_hash']:
                return False, "Invalid email or password", None
            
            # Update last login
            table.update_item(
                Key={'user_id': user['user_id']},
                UpdateExpression='SET last_login = :now',
                ExpressionAttributeValues={':now': datetime.utcnow().isoformat()}
            )
            
            # Create session
            session_id = self._generate_session_id()
            sessions_table = self.dynamodb.Table(self.sessions_table_name)
            sessions_table.put_item(
                Item={
                    'session_id': session_id,
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'created_at': datetime.utcnow().isoformat(),
                    'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat()
                }
            )
            
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
        """
        Validate session and return user data.
        
        Args:
            session_id: Session ID to validate
        
        Returns:
            Tuple of (is_valid, user_data)
        """
        try:
            table = self.dynamodb.Table(self.sessions_table_name)
            response = table.get_item(Key={'session_id': session_id})
            
            if 'Item' not in response:
                return False, None
            
            session = response['Item']
            
            # Check if session expired
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.utcnow() > expires_at:
                # Delete expired session
                table.delete_item(Key={'session_id': session_id})
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
        """
        Logout user by deleting session.
        
        Args:
            session_id: Session ID to delete
        
        Returns:
            Success status
        """
        try:
            table = self.dynamodb.Table(self.sessions_table_name)
            table.delete_item(Key={'session_id': session_id})
            return True
        except Exception as e:
            print(f"Logout error: {str(e)}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile data.
        
        Args:
            user_id: User ID
        
        Returns:
            User profile data (excluding sensitive info)
        """
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                return None
            
            user = response['Item']
            return {
                'user_id': user['user_id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'created_at': user['created_at'],
                'last_login': user.get('last_login'),
                'role': user.get('role', 'user')
            }
            
        except Exception as e:
            print(f"Get profile error: {str(e)}")
            return None
