from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Profile, UserRole
from app.schemas import UserCreate, UserResponse, UserLogin, Token, ResetPasswordRequest, UpdatePasswordRequest
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # Verificar se o email ja existe
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O e-mail informado já está cadastrado."
        )

    # Validar role
    if user_in.role not in ["citizen", "agent"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Papel de usuário inválido. Escolha 'citizen' ou 'agent'."
        )

    # Criar usuario
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Criar perfil
    db_profile = Profile(
        user_id=db_user.id,
        display_name=user_in.email.split("@")[0]
    )
    db.add(db_profile)

    # Criar role do usuario
    db_role = UserRole(
        user_id=db_user.id,
        role=user_in.role
    )
    db.add(db_role)

    db.commit()
    db.refresh(db_user)

    # Retornar dados com role formatada
    response_user = UserResponse(
        id=db_user.id,
        email=db_user.email,
        created_at=db_user.created_at,
        roles=[user_in.role],
        profile=db_profile
    )
    return response_user

@router.post("/signin", response_model=Token)
def signin(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos."
        )

    # Obter a role do usuario
    roles_db = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    roles = [r.role for r in roles_db]
    primary_role = roles[0] if roles else "citizen"

    # Criar token de acesso
    access_token = create_access_token(data={"sub": user.id, "email": user.email, "roles": roles})

    # Buscar perfil
    profile_db = db.query(Profile).filter(Profile.user_id == user.id).first()

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        roles=roles,
        profile=profile_db
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=primary_role,
        user=user_resp
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roles_db = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
    roles = [r.role for r in roles_db]
    
    profile_db = db.query(Profile).filter(Profile.user_id == current_user.id).first()

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
        roles=roles,
        profile=profile_db
    )

@router.get("/role")
def get_role(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roles_db = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
    roles = [r.role for r in roles_db]
    primary_role = roles[0] if roles else "citizen"
    return {"role": primary_role}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Por seguranca, nao revela se o email existe ou nao, mas retorna sucesso ficticio
        return {"message": "Se o e-mail estiver cadastrado, um link de recuperação foi enviado."}
    
    # Simula o envio do link exibindo no console do servidor para facilidade de desenvolvimento
    reset_token = create_access_token(data={"sub": user.id, "purpose": "reset-password"})
    reset_link = f"http://localhost:8080/reset-password#type=recovery&access_token={reset_token}"
    
    print("\n" + "="*80)
    print("MOCK E-MAIL DE RECUPERAÇÃO DE SENHA")
    print(f"Para: {user.email}")
    print(f"Link de Recuperação: {reset_link}")
    print("="*80 + "\n")
    
    return {"message": "Se o e-mail estiver cadastrado, um link de recuperação foi enviado."}

@router.post("/update-password")
def update_password(req: UpdatePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hashed_password = get_password_hash(req.password)
    current_user.password_hash = hashed_password
    db.commit()
    return {"message": "Senha atualizada com sucesso!"}

