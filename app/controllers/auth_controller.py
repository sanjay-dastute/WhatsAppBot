# Author: SANJAY KR
from jose import JWTError, jwt
from datetime import datetime, timedelta
from flask import current_app
from passlib.context import CryptContext
import os
from typing import Optional, Dict

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        
        secret_key = os.environ.get("JWT_SECRET_KEY", current_app.config.get("JWT_SECRET_KEY"))
        algorithm = os.environ.get("JWT_ALGORITHM", current_app.config.get("JWT_ALGORITHM", "HS256"))
        
        current_app.logger.info(f"Using algorithm: {algorithm}")
        current_app.logger.info(f"Secret key is set: {bool(secret_key)}")
        
        if not secret_key:
            raise ValueError("JWT_SECRET_KEY must be set")
            
        encoded_jwt = jwt.encode(
            to_encode,
            secret_key,
            algorithm=algorithm
        )
        return encoded_jwt
    except Exception as e:
        current_app.logger.error(f"Token creation error: {str(e)}")
        raise

def verify_token(token: str) -> Optional[str]:
    try:
        from flask import current_app
        import jwt
        
        secret_key = current_app.config.get("JWT_SECRET_KEY", "development-secret-key-do-not-use-in-production")
        algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")
        
        current_app.logger.info(f"Verifying token with algorithm: {algorithm}")
        
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm]
        )
        username = payload.get("sub")
        if not isinstance(username, str) or username is None:
            return None
        return username
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, str]]:
    current_app.logger.info(f"Authenticating user: {username}")
    
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin")
    
    current_app.logger.info(f"Using admin credentials - username: {admin_username}")
    current_app.logger.info(f"Received credentials - username: {username}, password: {'*' * len(password)}")
    
    current_app.logger.info("Checking credentials...")
    current_app.logger.info(f"Username match: {username == admin_username}")
    current_app.logger.info(f"Password match: {password == admin_password}")
    
    if username != admin_username or password != admin_password:
        current_app.logger.warning("Invalid credentials provided")
        return None
    
    try:
        expires_minutes = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        current_app.logger.info(f"Creating access token with expiry: {expires_minutes} minutes")
        
        access_token = create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=expires_minutes)
        )
        current_app.logger.info("Access token created successfully")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        current_app.logger.error(f"Error creating access token: {str(e)}")
        return None
