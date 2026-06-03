"""
Module d'authentification Firebase pour FastAPI.

Initialise Firebase Admin SDK et fournit les dépendances d'injection
pour vérifier les tokens JWT envoyés par le front-end.

Usage:
    from auth import get_current_user, get_optional_user

    @app.get("/route-protegee")
    def ma_route(user: dict = Depends(get_current_user)):
        print(user["uid"], user["email"])
"""

import os

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Depends, HTTPException, Header, status


# ============================================================
# Initialisation de Firebase Admin SDK
# ============================================================
# 1. Va sur https://console.firebase.google.com/
# 2. Sélectionne ton projet → Paramètres (⚙️) → Comptes de service
# 3. Clique sur "Générer une nouvelle clé privée"
# 4. Enregistre le fichier sous "serviceAccountKey.json" à la racine du projet
# ⚠️ NE JAMAIS commit ce fichier ! (il est déjà dans .gitignore)
# ============================================================

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)


def verify_firebase_token(token: str) -> dict:
    """
    Vérifie un token JWT Firebase et retourne les informations décodées.

    Args:
        token: Le token JWT Firebase (ID Token)

    Returns:
        dict contenant au minimum 'uid' et 'email'

    Raises:
        HTTPException(401) si le token est invalide, expiré ou révoqué
    """
    try:
        # check_revoked=True vérifie aussi si le token a été révoqué
        decoded_token = firebase_auth.verify_id_token(token, check_revoked=True)
        return decoded_token
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide.",
        )
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré. Veuillez vous reconnecter.",
        )
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token révoqué. Veuillez vous reconnecter.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification échouée.",
        )


# ============================================================
# Dépendances FastAPI (Dependency Injection)
# ============================================================


async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
) -> dict:
    """
    Dépendance STRICTE : bloque la requête si le token est absent ou invalide.
    Utiliser sur les routes qui NÉCESSITENT une authentification.

    Extrait le token du header HTTP :
        Authorization: Bearer <token>

    Retourne le token décodé (dict) avec les clés : uid, email, etc.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format attendu : Authorization: Bearer <votre_token>",
        )

    token = authorization[7:]  # Enlève "Bearer "
    return verify_firebase_token(token)


async def get_optional_user(
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict | None:
    """
    Dépendance OPTIONNELLE : retourne None si pas de token, sans bloquer.
    Utiliser sur les routes qui ACCEPTENT une authentification optionnelle.

    Retourne le token décodé (dict) si authentifié, None sinon.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]
    try:
        return verify_firebase_token(token)
    except HTTPException:
        # Token invalide → on considère l'utilisateur comme non connecté
        return None


# ============================================================
# Dépendance Admin — vérifie le rôle administrateur
# ============================================================


async def get_current_admin(
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Dépendance ADMIN : vérifie que l'utilisateur authentifié est administrateur.

    Compare l'email du token Firebase avec la variable d'environnement ADMIN_EMAIL.
    Renvoie HTTP 403 si l'utilisateur n'est pas admin.

    Retourne le token décodé (dict) si l'utilisateur est admin.
    """
    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_EMAIL non configurée sur le serveur.",
        )

    user_email = user.get("email", "")
    if user_email.lower() != admin_email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé : droits administrateur requis.",
        )

    return user

