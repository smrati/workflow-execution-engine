"""Authentication routes for the API."""

from fastapi import APIRouter, HTTPException, status, Depends

from .models import User, UserRole
from .schemas import (
    UserCreate,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    AdminUserCreate,
    AdminUserUpdate,
    UserListResponse,
)
from .dependencies import (
    verify_password,
    get_password_hash,
    create_tokens,
    decode_token,
    get_current_user,
    get_current_admin_user,
)
from ..dependencies import get_database

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user. Only allowed if no users exist yet (first user becomes admin)."""
    db = get_database()
    
    existing_user = db.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user_count = db.get_user_count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled. Contact an administrator to create an account."
        )
    
    hashed_password = get_password_hash(user_data.password)
    role = UserRole.ADMIN.value
    user = db.create_user(user_data.username, hashed_password, role)
    
    return UserResponse(
        id=user.id if user.id else 0,
        username=user.username,
        role=user.role.value,
        created_at=user.created_at
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access token."""
    db = get_database()
    
    user = db.get_user_by_username(credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = create_tokens(user.id if user.id else 0, user.username, user.role.value)
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token using refresh token."""
    payload = decode_token(token_data.refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub", "")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = get_database()
    user = db.get_user_by_username(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = create_tokens(user.id if user.id else 0, user.username, user.role.value)
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id if current_user.id else 0,
        username=current_user.username,
        role=current_user.role.value,
        created_at=current_user.created_at
    )


# Admin-only endpoints

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    user_data: AdminUserCreate,
    admin_user: User = Depends(get_current_admin_user)
):
    """Create a new user (admin only)."""
    db = get_database()
    
    existing_user = db.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    user = db.create_user(user_data.username, hashed_password, user_data.role)
    
    return UserResponse(
        id=user.id if user.id else 0,
        username=user.username,
        role=user.role.value,
        created_at=user.created_at
    )


@router.get("/users", response_model=UserListResponse)
async def admin_list_users(admin_user: User = Depends(get_current_admin_user)):
    """List all users (admin only)."""
    db = get_database()
    users = db.get_all_users()
    
    return UserListResponse(
        users=[
            UserResponse(
                id=u.id if u.id else 0,
                username=u.username,
                role=u.role.value,
                created_at=u.created_at
            )
            for u in users
        ],
        total=len(users)
    )


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def admin_update_user_role(
    user_id: int,
    role_data: AdminUserUpdate,
    admin_user: User = Depends(get_current_admin_user)
):
    """Update a user's role (admin only)."""
    db = get_database()
    
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own role"
        )
    
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.update_user_role(user_id, role_data.role)
    updated_user = db.get_user_by_id(user_id)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated user"
        )
    
    return UserResponse(
        id=updated_user.id if updated_user.id else 0,
        username=updated_user.username,
        role=updated_user.role.value,
        created_at=updated_user.created_at
    )


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user)
):
    """Delete a user (admin only)."""
    db = get_database()
    
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete_user(user_id)
    
    return {"message": f"User '{user.username}' deleted successfully"}
