# AWS Security Best Practices

This context provides global security guidelines that apply to all AWS-related work across all profiles.

## Core Security Principles

### Identity and Access Management (IAM)
- Always follow the principle of least privilege
- Use IAM roles instead of long-term access keys when possible
- Enable MFA for all human users
- Regularly rotate access keys and credentials
- Use AWS IAM Access Analyzer to review permissions

### Data Protection
- Encrypt data at rest using AWS KMS or service-specific encryption
- Encrypt data in transit using TLS/SSL
- Use AWS Secrets Manager for storing sensitive information
- Never hardcode credentials in code or configuration files

### Network Security
- Use VPCs with proper subnet segmentation
- Implement security groups with minimal required access
- Use NACLs for additional network-level security
- Enable VPC Flow Logs for network monitoring

### Monitoring and Logging
- Enable AWS CloudTrail in all regions
- Use AWS Config for compliance monitoring
- Set up CloudWatch alarms for security events
- Enable GuardDuty for threat detection

### Compliance and Governance
- Tag all resources consistently for cost allocation and governance
- Use AWS Organizations for multi-account management
- Implement SCPs (Service Control Policies) for organizational controls
- Regular security assessments and penetration testing

## Security Checklist for All Implementations

- [ ] IAM policies follow least privilege principle
- [ ] All data encrypted at rest and in transit
- [ ] Security groups are restrictive
- [ ] CloudTrail is enabled
- [ ] Resources are properly tagged
- [ ] No hardcoded credentials
- [ ] MFA enabled where applicable
- [ ] Regular access reviews conducted

## Emergency Response

In case of security incidents:
1. Immediately revoke compromised credentials
2. Enable detailed logging if not already active
3. Document all actions taken
4. Follow incident response procedures
5. Conduct post-incident review

---
*This context is automatically applied to all profiles and should be considered in all AWS-related recommendations and implementations.*
