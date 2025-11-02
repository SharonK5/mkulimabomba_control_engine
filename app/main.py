from fastapi import FastAPI, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db, init_db
from typing import Optional
import time
import jwt
from datetime import datetime, timedelta
import secrets
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
import os
from pydantic import BaseModel

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="MkulimaBomba Control Engine",
    description="AI-powered agricultural decision support system",
    version="2.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Redis for rate limiting and token blacklist (optional but recommended)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class TokenData(BaseModel):
    username: str
    role: str
    exp: datetime

class User(BaseModel):
    username: str
    role: str
    disabled: bool = False

# Mock user database - replace with real database in production
users_db = {
    "admin": User(username="admin", role="leadership"),
    "manager": User(username="manager", role="management"),
    "analyst": User(username="analyst", role="analytics"),
    "viewer": User(username="viewer", role="public")
}

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("MkulimaBomba Control Engine started with enhanced security")

# JWT Token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            return None
        return TokenData(username=username, role=role, exp=payload.get("exp"))
    except jwt.JWTError:
        return None

def is_token_revoked(token: str) -> bool:
    """Check if token is in blacklist"""
    return redis_client.exists(f"blacklist:{token}")

# Enhanced role-based access control with JWT
def require_role(required_role: str):
    async def role_checker(
        request: Request,
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        # Rate limiting by user/endpoint
        user_identifier = get_remote_address(request)
        rate_limit_key = f"rate_limit:{user_identifier}:{request.url.path}"
        
        current = int(redis_client.get(rate_limit_key) or 0)
        if current >= 100:  # 100 requests per minute per endpoint
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        redis_client.incr(rate_limit_key)
        redis_client.expire(rate_limit_key, 60)
        
        # JWT Authentication
        if not authorization.startswith("Bearer "):
            logger.warning(f"Invalid authorization header from {user_identifier}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = authorization[7:]
        
        # Check if token is revoked
        if is_token_revoked(token):
            logger.warning(f"Revoked token attempt from {user_identifier}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked"
            )
        
        payload = verify_token(token)
        if not payload:
            logger.warning(f"Invalid token from {user_identifier}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check token expiration
        if datetime.utcnow() > payload.exp:
            logger.warning(f"Expired token from {user_identifier}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        
        # Role authorization
        if payload.role != required_role:
            logger.warning(f"User {payload.username} with role {payload.role} attempted to access {required_role} endpoint")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Log successful access
        logger.info(f"User {payload.username} with role {payload.role} accessed {request.url.path}")
        
        return payload
    
    return Depends(role_checker)

# Authentication endpoints
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    # In production, use proper password hashing (bcrypt) and database lookup
    user = users_db.get(login_data.username)
    
    if not user or login_data.password != "secure_password":  # Replace with real auth
        logger.warning(f"Failed login attempt for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account disabled"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login for user: {user.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/auth/logout")
async def logout(authorization: str = Header(..., alias="Authorization")):
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        # Add token to blacklist with expiration
        payload = verify_token(token)
        if payload:
            expires_in = payload.exp - datetime.utcnow().timestamp()
            if expires_in > 0:
                redis_client.setex(
                    f"blacklist:{token}", 
                    int(expires_in), 
                    "revoked"
                )
    
    return {"message": "Successfully logged out"}

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Remove server info
    if "server" in response.headers:
        del response.headers["server"]
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {process_time:.3f}s"
    )
    
    return response

# Public endpoints
@app.get("/")
async def root():
    return {"message": "MkulimaBomba Control Engine API - Healthy"}

@app.get("/health")
async def health_check():
    # Add database health check
    try:
        redis_client.ping()
        redis_health = "healthy"
    except:
        redis_health = "unhealthy"
    
    return {
        "status": "healthy", 
        "service": "control_engine",
        "redis": redis_health,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/analytics/popular-queries")
async def get_popular_queries(db: Session = Depends(get_db)):
    return {"popular_queries": ["fertilizer for maize", "pest control", "planting season"]}

# Role-protected endpoints
@app.get("/analytics/management/diagnostics")
@limiter.limit("30/minute")
async def management_diagnostics(
    request: Request,
    db: Session = Depends(get_db), 
    _: TokenData = require_role("management")
):
    results = db.execute(text("""
        SELECT
            region,
            people_capacity,
            COUNT(*) as unsafe_count
        FROM audit_logs
        WHERE safe_label = 'Unsafe'
        GROUP BY region, people_capacity
        ORDER BY unsafe_count DESC
        LIMIT 10
    """)).fetchall()

    return {
        "risk_by_capacity_and_region": [
            {"region": r.region, "capacity": r.people_capacity, "unsafe_cases": r.unsafe_count} for r in results
        ]
    }

@app.get("/analytics/leadership/policy-insights")
@limiter.limit("20/minute")
async def leadership_policy_insights(
    request: Request,
    db: Session = Depends(get_db), 
    _: TokenData = require_role("leadership")
):
    problematic_rules = db.execute(text("""
        SELECT 
            rule_triggered,
            AVG(CAST(human_review_required AS INT)) as review_rate,
            COUNT(*) as total_cases
        FROM audit_logs
        WHERE rule_triggered IS NOT NULL
        GROUP BY rule_triggered
        HAVING review_rate > 0.5 AND total_cases >= 10
        ORDER BY review_rate DESC
    """)).fetchall()

    recommendations = []
    for rule in problematic_rules:
        recommendations.append({
            "rule": rule.rule_triggered,
            "human_review_rate": round(rule.review_rate, 2),
            "total_cases": rule.total_cases,
            "recommendation": f"Review '{rule.rule_triggered}' policy for flexibility or farmer education.",
            "suggested_action": "Update policy YAML + launch targeted training"
        })

    return {"strategic_policy_recommendations": recommendations}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        ssl_keyfile=os.getenv("SSL_KEYFILE", None),
        ssl_certfile=os.getenv("SSL_CERTFILE", None)
    )
