from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os
from typing import Optional, Dict, Any

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# User roles and permissions
ROLE_PERMISSIONS = {
    "admin": [
        "read_all", "write_all", "delete_all", "manage_users", 
        "configure_system", "execute_actions", "view_analytics"
    ],
    "staff": [
        "read_own", "write_own", "execute_actions", "view_reports"
    ],
    "read_only": [
        "read_own", "view_reports"
    ]
}

class AuthManager:
    def __init__(self):
        self.pwd_context = pwd_context
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

auth_manager = AuthManager()

# Odoo User Authentication Model
class AiUserAuth(models.Model):
    _name = 'ai.user.auth'
    _description = 'AI Copilot User Authentication'

    user_id = fields.Many2one('res.users', string='User', required=True)
    api_key = fields.Char(string='API Key', required=True)
    role = fields.Selection([
        ('admin', 'Administrator'),
        ('staff', 'Staff'),
        ('read_only', 'Read Only')
    ], string='Role', required=True, default='read_only')
    
    is_active = fields.Boolean(string='Active', default=True)
    last_login = fields.Datetime(string='Last Login')
    login_count = fields.Integer(string='Login Count', default=0)
    
    # Rate limiting
    requests_today = fields.Integer(string='Requests Today', default=0)
    last_request_date = fields.Date(string='Last Request Date')
    max_requests_per_day = fields.Integer(string='Max Requests Per Day', default=1000)
    
    # Security features
    allowed_ips = fields.Text(string='Allowed IP Addresses', help='Comma-separated list of allowed IPs')
    session_timeout = fields.Integer(string='Session Timeout (minutes)', default=30)

    @api.model
    def authenticate_user(self, api_key: str, ip_address: str = None) -> dict:
        """Authenticate user and return user info"""
        auth_record = self.search([
            ('api_key', '=', api_key),
            ('is_active', '=', True)
        ], limit=1)
        
        if not auth_record:
            return {'success': False, 'error': 'Invalid API key'}
        
        # Check IP restrictions
        if auth_record.allowed_ips and ip_address:
            allowed_ips = [ip.strip() for ip in auth_record.allowed_ips.split(',')]
            if ip_address not in allowed_ips:
                return {'success': False, 'error': 'IP address not allowed'}
        
        # Check rate limiting
        today = fields.Date.today()
        if auth_record.last_request_date != today:
            auth_record.requests_today = 0
            auth_record.last_request_date = today
        
        if auth_record.requests_today >= auth_record.max_requests_per_day:
            return {'success': False, 'error': 'Rate limit exceeded'}
        
        # Update counters
        auth_record.requests_today += 1
        auth_record.login_count += 1
        auth_record.last_login = fields.Datetime.now()
        
        return {
            'success': True,
            'user': {
                'id': auth_record.user_id.id,
                'name': auth_record.user_id.name,
                'email': auth_record.user_id.email,
                'role': auth_record.role,
                'permissions': ROLE_PERMISSIONS.get(auth_record.role, [])
            }
        }

# FastAPI Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    return payload

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Get current active user with additional checks"""
    # Additional checks can be added here
    return current_user

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: dict = Depends(get_current_active_user)):
        user_permissions = current_user.get('permissions', [])
        if permission not in user_permissions and 'read_all' not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker

# Rate Limiting Middleware
class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app
        self.requests = {}  # In production, use Redis
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            client_ip = request.client.host
            
            # Simple rate limiting (100 requests per minute)
            current_time = datetime.now()
            minute_key = f"{client_ip}:{current_time.strftime('%Y-%m-%d-%H-%M')}"
            
            if minute_key in self.requests:
                self.requests[minute_key] += 1
                if self.requests[minute_key] > 100:
                    response = JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"}
                    )
                    await response(scope, receive, send)
                    return
            else:
                self.requests[minute_key] = 1
        
        await self.app(scope, receive, send)

# Authentication endpoints
@router.post("/auth/login")
async def login(credentials: dict, request: Request):
    """Authenticate user and return tokens"""
    api_key = credentials.get('api_key')
    if not api_key:
        raise HTTPException(status_code=400, detail="API key required")
    
    # Get client IP
    client_ip = request.client.host
    
    # Authenticate with Odoo
    odoo_env = get_odoo_env()
    AuthModel = odoo_env['ai.user.auth']
    auth_result = AuthModel.authenticate_user(api_key, client_ip)
    
    if not auth_result['success']:
        raise HTTPException(status_code=401, detail=auth_result['error'])
    
    user = auth_result['user']
    
    # Create tokens
    access_token = auth_manager.create_access_token(
        data={"sub": str(user['id']), "role": user['role'], "permissions": user['permissions']}
    )
    refresh_token = auth_manager.create_refresh_token(
        data={"sub": str(user['id'])}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        payload = auth_manager.verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = payload.get("sub")
        # Get fresh user data from Odoo
        # ... (implementation details)
        
        new_access_token = auth_manager.create_access_token(
            data={"sub": user_id, "role": "staff", "permissions": ["read_own"]}  # Get from DB
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# Secure endpoint examples
@router.get("/secure/profile")
async def get_profile(current_user: dict = Depends(get_current_active_user)):
    """Get current user profile"""
    return {"user": current_user}

@router.get("/secure/admin-only")
async def admin_only_endpoint(
    current_user: dict = Depends(require_permission("manage_users"))
):
    """Admin only endpoint"""
    return {"message": "This is admin-only content", "user": current_user}

# API Key Management
@router.post("/auth/generate-api-key")
async def generate_api_key(
    user_data: dict,
    current_user: dict = Depends(require_permission("manage_users"))
):
    """Generate new API key for user"""
    import secrets
    
    api_key = f"ai_copilot_{secrets.token_urlsafe(32)}"
    
    # Save to Odoo
    odoo_env = get_odoo_env()
    AuthModel = odoo_env['ai.user.auth']
    
    auth_record = AuthModel.create({
        'user_id': user_data['user_id'],
        'api_key': api_key,
        'role': user_data.get('role', 'read_only'),
        'max_requests_per_day': user_data.get('max_requests_per_day', 1000),
        'allowed_ips': user_data.get('allowed_ips', ''),
        'session_timeout': user_data.get('session_timeout', 30)
    })
    
    return {
        "api_key": api_key,
        "user_id": user_data['user_id'],
        "role": user_data.get('role', 'read_only'),
        "created_at": auth_record.create_date.isoformat()
    }
