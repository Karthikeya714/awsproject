"""Authentication and authorization using AWS Cognito."""
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
from backend.config import config_manager


class AuthManager:
    """Manages authentication with AWS Cognito."""
    
    def __init__(self):
        self.config = config_manager.config
        self.cognito_client = None
    
    def _get_client(self):
        """Lazy initialization of Cognito client."""
        if not self.cognito_client:
            self.cognito_client = boto3.client(
                'cognito-idp',
                region_name=self.config.aws_region
            )
        return self.cognito_client
    
    def verify_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Cognito access token.
        
        Args:
            access_token: JWT access token from Cognito
            
        Returns:
            User info dict if valid, None otherwise
        """
        try:
            client = self._get_client()
            response = client.get_user(AccessToken=access_token)
            
            user_info = {
                'user_id': response['Username'],
                'attributes': {}
            }
            
            for attr in response.get('UserAttributes', []):
                user_info['attributes'][attr['Name']] = attr['Value']
            
            return user_info
        except ClientError as e:
            print(f"Error verifying token: {e}")
            return None
    
    def get_user_id_from_token(self, access_token: str) -> Optional[str]:
        """
        Extract user ID from token.
        
        Args:
            access_token: JWT access token
            
        Returns:
            User ID if valid, None otherwise
        """
        user_info = self.verify_token(access_token)
        return user_info['user_id'] if user_info else None
    
    def is_admin(self, access_token: str) -> bool:
        """
        Check if user has admin role.
        
        Args:
            access_token: JWT access token
            
        Returns:
            True if user is admin
        """
        user_info = self.verify_token(access_token)
        if not user_info:
            return False
        
        # Check for admin group membership
        try:
            client = self._get_client()
            response = client.admin_list_groups_for_user(
                Username=user_info['user_id'],
                UserPoolId=self.config.cognito_user_pool_id
            )
            
            groups = [g['GroupName'] for g in response.get('Groups', [])]
            return 'Admins' in groups
        except ClientError:
            return False
