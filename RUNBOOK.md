# Operations Runbook

## 📖 Overview

This runbook provides operational procedures for the Image Caption Generator application.

## 🚀 Deployment Procedures

### Standard Deployment

1. **Pre-deployment Checklist**:
   - [ ] All tests passing in CI
   - [ ] Code reviewed and approved
   - [ ] Terraform plan reviewed
   - [ ] Backup current state
   - [ ] Notify team of deployment window

2. **Deploy via CI/CD**:
   ```bash
   git tag -a v1.0.1 -m "Release v1.0.1"
   git push origin v1.0.1
   ```

3. **Manual Deployment**:
   ```bash
   # Build and push image
   ./scripts/deploy.sh prod
   
   # Or manually:
   cd infra/terraform
   terraform apply -var-file=prod.tfvars
   ```

4. **Post-deployment Verification**:
   - Check ECS service is stable
   - Verify health endpoint: `curl https://app-url.com/_stcore/health`
   - Monitor CloudWatch dashboard
   - Run smoke tests

### Rollback Procedure

**Automatic Rollback** (via CI/CD):
- Triggers automatically on deployment failure
- Reverts to previous task definition

**Manual Rollback**:

```bash
# List recent task definitions
aws ecs list-task-definitions \
  --family-prefix image-caption-gen-prod \
  --sort DESC \
  --max-results 5

# Update service to previous version
aws ecs update-service \
  --cluster image-caption-gen-cluster-prod \
  --service image-caption-gen-service-prod \
  --task-definition image-caption-gen-prod:PREVIOUS_REVISION \
  --force-new-deployment

# Wait for stability
aws ecs wait services-stable \
  --cluster image-caption-gen-cluster-prod \
  --services image-caption-gen-service-prod
```

## 🔐 Security Operations

### Rotate Secrets

**1. HuggingFace API Key**:
```bash
# Update secret in Secrets Manager
aws secretsmanager update-secret \
  --secret-id image-caption-gen-secrets-prod \
  --secret-string '{"hf_api_key":"NEW_KEY"}'

# Force ECS deployment to pick up new secret
aws ecs update-service \
  --cluster image-caption-gen-cluster-prod \
  --service image-caption-gen-service-prod \
  --force-new-deployment
```

**2. Cognito Client Secret**:
```bash
# Regenerate via Console or:
aws cognito-idp update-user-pool-client \
  --user-pool-id YOUR_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --generate-secret
```

**3. IAM Role Credentials**:
- Roles use temporary credentials (no rotation needed)
- For access keys (not recommended): rotate via IAM console

### Security Incident Response

**1. Suspected Unauthorized Access**:
```bash
# Check CloudTrail logs
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=image-caption-gen-prod \
  --start-time "2025-01-01T00:00:00Z" \
  --max-results 50

# Review CloudWatch logs
aws logs filter-log-events \
  --log-group-name /ecs/image-caption-gen-prod \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

**2. Block Suspicious IP**:
```bash
# Update WAF rule
aws wafv2 update-ip-set \
  --name blocked-ips \
  --scope CLOUDFRONT \
  --id YOUR_IP_SET_ID \
  --addresses "SUSPICIOUS_IP/32"
```

**3. Disable Compromised User**:
```bash
aws cognito-idp admin-disable-user \
  --user-pool-id YOUR_POOL_ID \
  --username COMPROMISED_USER
```

## 📊 Scaling Operations

### Scale ECS Service

**Scale Up**:
```bash
aws ecs update-service \
  --cluster image-caption-gen-cluster-prod \
  --service image-caption-gen-service-prod \
  --desired-count 5
```

**Scale Down**:
```bash
aws ecs update-service \
  --cluster image-caption-gen-cluster-prod \
  --service image-caption-gen-service-prod \
  --desired-count 2
```

**Update Task Size**:
```bash
cd infra/terraform

# Edit terraform.tfvars
terraform apply -var="ecs_task_cpu=1024" -var="ecs_task_memory=2048"
```

### Auto-scaling Adjustments

**Modify CPU Target**:
```bash
aws application-autoscaling put-scaling-policy \
  --policy-name image-caption-gen-cpu-autoscaling-prod \
  --service-namespace ecs \
  --resource-id service/image-caption-gen-cluster-prod/image-caption-gen-service-prod \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 60.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

## 🗄️ Data Management

### Delete User Data

**Via Application**:
- User logs in and uses "Delete Data" tab

**Manual Deletion**:
```bash
# Delete from S3
aws s3 rm s3://your-bucket/images/USER_ID/ --recursive

# Delete from DynamoDB
aws dynamodb query \
  --table-name image_captions \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values '{":pk":{"S":"USER#USER_ID"}}' \
  --output json | \
jq -r '.Items[] | "{\\"PK\\": {\\"S\\": \\"" + .PK.S + "\\"}, \\"SK\\": {\\"S\\": \\"" + .SK.S + "\\"}}"' | \
while read item; do
  aws dynamodb delete-item --table-name image_captions --key "$item"
done
```

### Backup and Restore

**S3 Backup**:
```bash
# Enable versioning (already done via Terraform)
# Point-in-time restore:
aws s3 sync s3://your-bucket s3://backup-bucket --include "*"
```

**DynamoDB Backup**:
```bash
# On-demand backup
aws dynamodb create-backup \
  --table-name image_captions \
  --backup-name "backup-$(date +%Y%m%d-%H%M%S)"

# List backups
aws dynamodb list-backups --table-name image_captions

# Restore
aws dynamodb restore-table-from-backup \
  --target-table-name image_captions_restored \
  --backup-arn arn:aws:dynamodb:region:account:table/image_captions/backup/xxxxx
```

## 🔍 Monitoring & Alerting

### Check Service Health

```bash
# ECS service status
aws ecs describe-services \
  --cluster image-caption-gen-cluster-prod \
  --services image-caption-gen-service-prod

# Task health
aws ecs list-tasks \
  --cluster image-caption-gen-cluster-prod \
  --service-name image-caption-gen-service-prod

# Application health endpoint
curl -f https://your-app-url.com/_stcore/health
```

### View Logs

**Real-time**:
```bash
aws logs tail /ecs/image-caption-gen-prod --follow
```

**Search for Errors**:
```bash
aws logs filter-log-events \
  --log-group-name /ecs/image-caption-gen-prod \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --output table
```

**CloudWatch Insights Query**:
```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

### Alarm Management

**List Active Alarms**:
```bash
aws cloudwatch describe-alarms \
  --alarm-name-prefix "image-caption-gen-prod" \
  --state-value ALARM
```

**Silence Alarm** (temporarily):
```bash
aws cloudwatch disable-alarm-actions \
  --alarm-names "image-caption-gen-high-error-rate-prod"

# Re-enable
aws cloudwatch enable-alarm-actions \
  --alarm-names "image-caption-gen-high-error-rate-prod"
```

## 🐛 Troubleshooting

### Issue: High Error Rate

**Diagnosis**:
```bash
# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn YOUR_TG_ARN

# Check ECS task status
aws ecs describe-tasks \
  --cluster image-caption-gen-cluster-prod \
  --tasks $(aws ecs list-tasks --cluster image-caption-gen-cluster-prod --service-name image-caption-gen-service-prod --query 'taskArns[*]' --output text)
```

**Resolution**:
- Check CloudWatch logs for specific errors
- Verify IAM permissions
- Check Bedrock/SageMaker endpoint status
- Scale up if capacity issue

### Issue: High Latency

**Diagnosis**:
```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=YOUR_ALB_ARN_SUFFIX \
  --start-time $(date -u -d '1 hour ago' --iso-8601=seconds) \
  --end-time $(date -u --iso-8601=seconds) \
  --period 300 \
  --statistics Average
```

**Resolution**:
- Scale up ECS tasks
- Optimize Bedrock prompts
- Implement caching
- Check network connectivity

### Issue: Authentication Failures

**Diagnosis**:
```bash
# Check Cognito user pool
aws cognito-idp describe-user-pool \
  --user-pool-id YOUR_POOL_ID

# Check user status
aws cognito-idp admin-get-user \
  --user-pool-id YOUR_POOL_ID \
  --username USERNAME
```

**Resolution**:
- Verify Cognito configuration
- Check callback URLs
- Verify client ID/secret
- Reset user password if needed

### Issue: DynamoDB Throttling

**Diagnosis**:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=image_captions \
  --start-time $(date -u -d '1 hour ago' --iso-8601=seconds) \
  --end-time $(date -u --iso-8601=seconds) \
  --period 300 \
  --statistics Sum
```

**Resolution**:
- Already using PAY_PER_REQUEST (on-demand) mode
- If needed, implement request batching
- Add caching layer

## 📞 Emergency Contacts

- **On-Call Engineer**: See PagerDuty rotation
- **AWS Support**: Use Support Center
- **Security Team**: security@example.com
- **DevOps Team**: devops@example.com

## 📋 Maintenance Windows

- **Regular Maintenance**: Sundays 02:00-04:00 UTC
- **Emergency Maintenance**: As needed, with 1-hour notice
- **Notification Channels**: Slack #engineering, email list

## 📚 Additional Resources

- CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/...
- Terraform State: s3://terraform-state-bucket/
- Runbook Updates: Update this file via PR
- Incident Reports: See `/docs/incidents/`

---

**Last Updated**: 2025-10-14  
**Version**: 1.0.0  
**Maintained By**: DevOps Team
