"""DynamoDB database operations for captions and user history."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from backend.config import config_manager
from backend.models import CaptionResult, UserHistory


class DynamoDBManager:
    """Manages DynamoDB operations for storing captions and metadata."""
    
    def __init__(self):
        self.config = config_manager.config
        self.dynamodb = boto3.resource('dynamodb', region_name=self.config.aws_region)
        self.table = self.dynamodb.Table(self.config.dynamodb_table)
    
    def save_caption(self, caption_result: CaptionResult) -> bool:
        """
        Save caption result to DynamoDB.
        
        Args:
            caption_result: CaptionResult to save
            
        Returns:
            True if successful
        """
        try:
            item = {
                'PK': f"USER#{caption_result.user_id}",
                'SK': f"IMAGE#{caption_result.image_id}",
                'image_id': caption_result.image_id,
                'user_id': caption_result.user_id,
                'concise_caption': caption_result.concise_caption,
                'creative_caption': caption_result.creative_caption,
                'labels': caption_result.labels or [],
                'model': caption_result.model,
                'provider': caption_result.provider.value,
                'confidence': Decimal(str(caption_result.confidence)) if caption_result.confidence else None,
                'timestamp': caption_result.timestamp.isoformat(),
                's3_url': caption_result.s3_url,
                'thumbnail_url': caption_result.thumbnail_url,
                'GSI1PK': f"IMAGE#{caption_result.image_id}",  # For querying by image_id
                'GSI1SK': caption_result.timestamp.isoformat()
            }
            
            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            print(f"Error saving caption: {e}")
            return False
    
    def get_user_history(
        self,
        user_id: str,
        limit: int = 50,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> tuple[List[UserHistory], Optional[Dict[str, Any]]]:
        """
        Get user's caption history with pagination.
        
        Args:
            user_id: User ID
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token from previous query
            
        Returns:
            Tuple of (list of UserHistory, pagination token)
        """
        try:
            query_params = {
                'KeyConditionExpression': Key('PK').eq(f"USER#{user_id}") & Key('SK').begins_with('IMAGE#'),
                'Limit': limit,
                'ScanIndexForward': False  # Sort descending by SK (timestamp)
            }
            
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = last_evaluated_key
            
            response = self.table.query(**query_params)
            
            history = []
            for item in response.get('Items', []):
                history.append(UserHistory(
                    image_id=item['image_id'],
                    user_id=item['user_id'],
                    concise_caption=item['concise_caption'],
                    creative_caption=item['creative_caption'],
                    thumbnail_url=item['thumbnail_url'],
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    labels=item.get('labels')
                ))
            
            next_key = response.get('LastEvaluatedKey')
            return history, next_key
            
        except ClientError as e:
            print(f"Error getting user history: {e}")
            return [], None
    
    def get_caption_by_image_id(self, image_id: str) -> Optional[CaptionResult]:
        """
        Get caption by image ID.
        
        Args:
            image_id: Image ID
            
        Returns:
            CaptionResult if found, None otherwise
        """
        try:
            # Query using GSI1
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq(f"IMAGE#{image_id}"),
                Limit=1
            )
            
            items = response.get('Items', [])
            if not items:
                return None
            
            item = items[0]
            return CaptionResult(
                image_id=item['image_id'],
                user_id=item['user_id'],
                concise_caption=item['concise_caption'],
                creative_caption=item['creative_caption'],
                labels=item.get('labels'),
                model=item['model'],
                provider=item['provider'],
                confidence=float(item['confidence']) if item.get('confidence') else None,
                timestamp=datetime.fromisoformat(item['timestamp']),
                s3_url=item['s3_url'],
                thumbnail_url=item['thumbnail_url']
            )
        except ClientError as e:
            print(f"Error getting caption: {e}")
            return None
    
    def delete_user_data(self, user_id: str) -> int:
        """
        Delete all data for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of items deleted
        """
        try:
            # Query all items for user
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(f"USER#{user_id}")
            )
            
            items = response.get('Items', [])
            deleted = 0
            
            # Delete items in batches
            with self.table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(
                        Key={'PK': item['PK'], 'SK': item['SK']}
                    )
                    deleted += 1
            
            return deleted
        except ClientError as e:
            print(f"Error deleting user data: {e}")
            return 0
    
    def get_usage_metrics(self) -> Dict[str, Any]:
        """
        Get usage metrics for admin dashboard.
        
        Returns:
            Dictionary with usage metrics
        """
        try:
            # Scan table for metrics (not recommended for large tables - use CloudWatch instead)
            response = self.table.scan(
                Select='COUNT'
            )
            
            total_items = response.get('Count', 0)
            
            # Get unique users (simplified - in production, use a separate counter)
            users = set()
            response = self.table.scan(
                ProjectionExpression='user_id'
            )
            for item in response.get('Items', []):
                users.add(item.get('user_id'))
            
            return {
                'total_captions': total_items,
                'total_users': len(users),
                'timestamp': datetime.utcnow().isoformat()
            }
        except ClientError as e:
            print(f"Error getting usage metrics: {e}")
            return {}
