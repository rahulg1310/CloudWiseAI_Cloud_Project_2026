from fastapi import APIRouter, Depends, HTTPException
from psycopg2.errors import UniqueViolation

from app.database import get_db
from app.schemas import SignupRequest, LoginRequest
from app.security import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(body: SignupRequest, conn=Depends(get_db)):
    email = body.email.lower()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id, username, email",
                (body.username, email, hash_password(body.password)),
            )
            user = cur.fetchone()
    except UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    return {"user": user, "token": create_token(user["id"])}


@router.post("/login")
def login(body: LoginRequest, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, email, password_hash FROM users WHERE email = %s",
            (body.email.lower(),),
        )
        row = cur.fetchone()

    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user = {"id": row["id"], "username": row["username"], "email": row["email"]}
    return {"user": user, "token": create_token(user["id"])}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user
