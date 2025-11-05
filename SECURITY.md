# QCA Security Configuration Guide

## Security Concerns and Recommendations

### Current Development Setup
The current setup is configured for **development only** and has several security considerations that must be addressed before production deployment.

### ⚠️ Critical Security Issues

#### 1. CORS Configuration
**Current**: Allows all origins (`*`)
**Issue**: Exposes API to all domains
**Fix**: Restrict to specific domains

```python
# In api/src/main.py - PRODUCTION CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourapp.com", "https://www.yourapp.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods only
    allow_headers=["*"],
)
```

#### 2. Database Credentials
**Current**: Hardcoded in docker-compose.yml
**Issue**: Credentials visible in code
**Fix**: Use environment variables and secrets

```yaml
# docker-compose.yml - PRODUCTION CONFIGURATION
environment:
  POSTGRES_USER: ${POSTGRES_USER}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  POSTGRES_DB: ${POSTGRES_DB}
```

#### 3. No Authentication/Authorization
**Current**: All endpoints publicly accessible
**Issue**: No access control
**Fix**: Implement authentication system

```python
# Example OAuth2/JWT implementation needed
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Implement token verification logic
    pass
```

#### 4. OpenAI API Key Exposure
**Current**: Set in environment
**Issue**: Potential exposure in logs/config
**Fix**: Use secure secret management

#### 5. No HTTPS/TLS
**Current**: HTTP only
**Issue**: Data transmitted in plain text
**Fix**: Implement reverse proxy with SSL

### Recommended Production Architecture

```
Internet → Load Balancer/Reverse Proxy (nginx + SSL) → Application → Database
                    ↓
            Rate Limiting, WAF, Security Headers
```

### Security Headers to Add

```python
# Add to api/src/main.py
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### Database Security

#### 1. Connection Security
- Use SSL/TLS for database connections
- Implement connection pooling with limits
- Use read-only users for read operations

#### 2. Data Protection
- Encrypt sensitive data at rest
- Implement field-level encryption for PII
- Regular security audits

### API Security

#### 1. Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/endpoint")
@limiter.limit("10/minute")
async def endpoint(request: Request):
    pass
```

#### 2. Input Validation
- Already implemented with Pydantic
- Add length limits to string fields
- Sanitize file uploads

#### 3. SQL Injection Prevention
- Already protected by SQLAlchemy ORM
- Avoid raw SQL queries
- Use parameterized queries when needed

### Environment Configuration

#### Production .env Template
```bash
# Database
DATABASE_URL=postgresql://user:password@db:5432/dbname
POSTGRES_USER=secure_user
POSTGRES_PASSWORD=complex_secure_password
POSTGRES_DB=qca_production

# API
API_SECRET_KEY=very_long_random_secret_key_256_bits
JWT_SECRET_KEY=another_long_random_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External Services
OPENAI_API_KEY=sk-...
ALLOWED_ORIGINS=https://app.company.com,https://admin.company.com

# Security
SECURITY_SALT=random_salt_for_hashing
MAX_REQUEST_SIZE=10MB
RATE_LIMIT_PER_MINUTE=100
```

### Monitoring and Logging

#### 1. Security Events to Log
- Authentication attempts
- Authorization failures
- API rate limit exceeded
- Unusual data access patterns
- System errors

#### 2. Log Management
- Centralized logging (ELK stack, Splunk)
- Log rotation and retention policies
- Security event alerts

### Deployment Security

#### 1. Container Security
```dockerfile
# Use specific versions, not 'latest'
FROM python:3.11.8-slim

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Set security-focused environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```

#### 2. Secrets Management
- Use Docker secrets or Kubernetes secrets
- Avoid environment variables for sensitive data
- Implement secret rotation

#### 3. Network Security
- Use private networks for internal communication
- Implement network segmentation
- Regular security scanning

### Compliance and Auditing

#### 1. Audit Trail
- Log all data modifications
- Track user actions
- Maintain data lineage

#### 2. Data Protection
- Implement GDPR/privacy controls
- Data retention policies
- Right to deletion capabilities

### Security Testing

#### 1. Automated Security Testing
```bash
# Add to CI/CD pipeline
safety check  # Python dependency security
bandit -r .   # Python security linting
semgrep --config=auto .  # Static analysis
```

#### 2. Penetration Testing
- Regular security assessments
- API security testing
- Infrastructure security review

### Incident Response

#### 1. Security Incident Plan
- Incident detection procedures
- Response team contacts
- Communication templates
- Recovery procedures

#### 2. Backup and Recovery
- Regular encrypted backups
- Disaster recovery testing
- Business continuity planning

## Implementation Priority

### High Priority (Before Production)
1. ✅ Fix CORS configuration
2. ✅ Implement authentication/authorization
3. ✅ Secure database credentials
4. ✅ Add HTTPS/TLS
5. ✅ Implement rate limiting

### Medium Priority
1. Add security headers
2. Implement comprehensive logging
3. Set up monitoring and alerting
4. Container security hardening

### Ongoing
1. Regular security audits
2. Dependency updates
3. Security training
4. Incident response drills

## Conclusion

The current QCA implementation provides a solid foundation but requires significant security enhancements before production deployment. Follow this guide systematically to implement appropriate security controls for your environment and compliance requirements.