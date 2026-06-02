import os

from dotenv import load_dotenv

load_dotenv()  # Charge les variables depuis .env (développement local)

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Form
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from sqlalchemy import inspect as sa_inspect, text
from fastapi.responses import RedirectResponse
from auth import get_current_user


# Creation of the tables Project, Skill, Experience and Portfolio
class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None
    link: str | None

    portfolio_id: int | None = Field(default=None, foreign_key="portfolio.id")

    portfolio: "Portfolio" = Relationship(back_populates="project")


class Skill(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    level: str

    portfolio_id: int | None = Field(default=None, foreign_key="portfolio.id")

    portfolio: "Portfolio" = Relationship(back_populates="skill")


class Experience(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    company: str
    role: str
    duration: str
    description: str | None
    # 1. La clé étrangère qui pointe vers l'id du portfolio
    portfolio_id: int | None = Field(default=None, foreign_key="portfolio.id")

    # 2. La relation retour vers le Portfolio
    portfolio: "Portfolio" = Relationship(back_populates="experience")


class Portfolio(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    formation: str
    # NOTE: Pour la future intégration de l'authentification, on pourra ajouter :
    # user_id: int | None = Field(default=None, foreign_key="user.id")
    # user: "User" = Relationship(back_populates="portfolios")

    experience: list["Experience"] = Relationship(
        back_populates="portfolio",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        },  # permet de supprimer les relations enfants quand le parent est supprimé
    )
    project: list["Project"] = Relationship(
        back_populates="portfolio",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    skill: list["Skill"] = Relationship(
        back_populates="portfolio",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    github: str | None
    linkedin: str | None
    firebase_uid: str | None = Field(
        default=None, index=True
    )  # ID utilisateur Firebase


# ---------- Connexion dynamique à la base de données ----------
# En production (Render) : DATABASE_URL est définie → PostgreSQL
# En local                : DATABASE_URL absente   → SQLite

print("=" * 60)
print("🔧 DIAGNOSTIC DE CONNEXION À LA BASE DE DONNÉES")
print("=" * 60)

DATABASE_URL = os.getenv("DATABASE_URL")
IS_RENDER = os.getenv("RENDER") is not None  # Render définit toujours cette variable

# --- Log 1 : Détection de DATABASE_URL ---
if DATABASE_URL:
    # Masquer le mot de passe pour la sécurité des logs
    masked_url = DATABASE_URL
    try:
        from urllib.parse import urlparse

        parsed = urlparse(DATABASE_URL)
        if parsed.password:
            masked_url = DATABASE_URL.replace(parsed.password, "****")
    except Exception:
        masked_url = DATABASE_URL[:25] + "****"
    print(f"✅ DATABASE_URL détectée : OUI")
    print(f"   URL (masquée) : {masked_url}")
else:
    print(f"❌ DATABASE_URL détectée : NON")

# --- Log 2 : Environnement ---
print(f"🌐 Environnement Render : {'OUI' if IS_RENDER else 'NON (local)'}")

# --- Log 3 : Sélection du moteur ---
if DATABASE_URL:
    # Render fournit parfois une URL commençant par "postgres://"
    # SQLAlchemy 1.4+ exige "postgresql://"
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        print("   ↳ URL corrigée : postgres:// → postgresql://")
    engine = create_engine(DATABASE_URL, echo=False)
    print("🚀 DÉMARRAGE : Connexion à PostgreSQL")
else:
    # 🛡️ SÉCURITÉ : Empêcher SQLite en production (Render)
    if IS_RENDER:
        print("🚨 ERREUR CRITIQUE : DATABASE_URL absente sur Render !")
        print("   → SQLite utilise le filesystem éphémère de Render.")
        print("   → Les données seront PERDUES à chaque redéploiement.")
        print("   → Ajoutez DATABASE_URL dans les variables d'environnement Render.")
        raise RuntimeError(
            "DATABASE_URL manquante en production. "
            "Configurez-la dans Render > Environment > Environment Variables."
        )
    sqlite_file_name = "database_portfolio.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)
    print("🚀 DÉMARRAGE : Connexion à SQLite (développement local)")

# --- Log 4 : Test de connexion ---
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Test de connexion : RÉUSSI")
except Exception as e:
    print(f"❌ Test de connexion : ÉCHOUÉ — {e}")
    raise

# --- Log 5 : Dialecte effectif ---
print(f"🗄️  Dialecte SQLAlchemy : {engine.dialect.name}")
print("=" * 60)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Création de la base de données au démarrage
    create_db_and_tables()

    # --- Diagnostic : tables existantes et nombre de lignes ---
    print("=" * 60)
    print("📊 ÉTAT DE LA BASE DE DONNÉES APRÈS DÉMARRAGE")
    print("=" * 60)
    try:
        inspector = sa_inspect(engine)
        tables = inspector.get_table_names()
        print(f"   Tables trouvées : {tables}")
        with Session(engine) as session:
            for table_name in tables:
                try:
                    count = session.execute(
                        text(f'SELECT COUNT(*) FROM "{table_name}"')
                    ).scalar()
                    print(f"   📋 {table_name} : {count} ligne(s)")
                except Exception as e:
                    print(f"   ⚠️ {table_name} : erreur de lecture — {e}")
    except Exception as e:
        print(f"   ⚠️ Impossible de lister les tables : {e}")
    print("=" * 60)

    # Migration portable (SQLite + PostgreSQL) : ajouter firebase_uid si absent
    try:
        inspector = sa_inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("portfolio")]
        if "firebase_uid" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE portfolio ADD COLUMN firebase_uid TEXT"))
            print(
                "✅ Migration : colonne 'firebase_uid' ajoutée à la table 'portfolio'"
            )
    except Exception as e:
        print(f"⚠️ Migration firebase_uid : {e}")
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")


# Will search my HTML files within the "Templates" file
templates = Jinja2Templates(directory="templates")


@app.post("/portfolios/")
def create_portfolio(
    session: SessionDep,
    name: str = Form(...),
    formation: str = Form(...),
    github: str | None = Form(None),
    linkedin: str | None = Form(None),
    user: dict = Depends(get_current_user),  # Token Firebase OBLIGATOIRE
):
    # Le portfolio est systématiquement lié au compte Firebase de l'utilisateur
    portfolio = Portfolio(
        name=name,
        formation=formation,
        github=github,
        linkedin=linkedin,
        firebase_uid=user["uid"],
    )
    session.add(portfolio)
    session.commit()
    session.refresh(portfolio)
    return RedirectResponse(url="/portfolios/", status_code=303)


@app.get("/portfolios/", response_class=HTMLResponse)
def read_portfolios_page(
    request: Request,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    portfolios = session.exec(select(Portfolio).offset(offset).limit(limit)).all()
    return templates.TemplateResponse(
        request=request, name="home.html", context={"db_portfolios": portfolios}
    )


@app.get("/portfolios/create", response_class=HTMLResponse)
def create_portfolio_page(request: Request):
    return templates.TemplateResponse(request=request, name="create_portfolio.html")


# Page pour éditer un portfolio


@app.get("/portfolios/{portfolio_id}/edit", response_class=HTMLResponse)
def edit_portfolio_page(
    request: Request,
    portfolio_id: int,
    session: SessionDep,
):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return templates.TemplateResponse(
        request=request, name="edit_portfolio.html", context={"portfolio": portfolio}
    )


@app.post("/portfolios/{portfolio_id}/edit")
def update_portfolio(
    portfolio_id: int,
    session: SessionDep,
    name: str = Form(...),
    formation: str = Form(...),
    github: str | None = Form(None),
    linkedin: str | None = Form(None),
    user: dict = Depends(get_current_user),
):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.firebase_uid and portfolio.firebase_uid != user["uid"]:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas le propriétaire.")
    portfolio.name = name
    portfolio.formation = formation
    portfolio.github = github
    portfolio.linkedin = linkedin
    session.commit()
    return RedirectResponse(url=f"/portfolios/{portfolio_id}", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


# ============================================================
# Route protégée de test — nécessite un token Firebase valide
# ============================================================
@app.get("/api/portfolio/prive")
def route_privee(user: dict = Depends(get_current_user)):
    return {
        "message": f"Bienvenue {user.get('email', 'utilisateur')} !",
        "uid": user["uid"],
        "email": user.get("email"),
    }


@app.get("/portfolios/{portfolio_id}", response_class=HTMLResponse)
def read_portfolio(request: Request, portfolio_id: int, session: SessionDep):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    # On passe firebase_uid au template pour que le JS compare avec l'UID connecté
    return templates.TemplateResponse(
        request=request,
        name="portfolio_detail.html",
        context={
            "portfolio": portfolio,
            "owner_uid": portfolio.firebase_uid or "",
        },
    )


@app.delete("/portfolios/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int,
    session: SessionDep,
    user: dict = Depends(get_current_user),
):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    # Vérifie que l'utilisateur est bien le propriétaire du portfolio
    if portfolio.firebase_uid and portfolio.firebase_uid != user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="Vous n'êtes pas le propriétaire de ce portfolio.",
        )
    session.delete(portfolio)
    session.commit()
    return {"ok": True}


# supprimer un portfolio


@app.post("/portfolios/{portfolio_id}/delete")
def delete_portfolio_post(
    portfolio_id: int,
    session: SessionDep,
    user: dict = Depends(get_current_user),
):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.firebase_uid and portfolio.firebase_uid != user["uid"]:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas le propriétaire.")
    session.delete(portfolio)
    session.commit()
    return {"ok": True}


# Ajouter une compétence à un portfolio (propriétaire uniquement)


@app.post("/portfolios/{portfolio_id}/skills/")
def create_skill(
    portfolio_id: int,
    session: SessionDep,
    name: str = Form(...),
    level: str = Form(...),
    user: dict = Depends(get_current_user),
):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    # Vérification de propriété : seul le propriétaire peut ajouter des compétences
    if portfolio.firebase_uid != user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="Vous n'êtes pas le propriétaire de ce portfolio.",
        )
    skill = Skill(name=name, level=level, portfolio_id=portfolio_id)
    session.add(skill)
    session.commit()
    return RedirectResponse(url=f"/portfolios/{portfolio_id}", status_code=303)


# Supprimer une compétence (propriétaire uniquement)
@app.post("/skills/{skill_id}/delete")
def delete_skill(
    skill_id: int,
    session: SessionDep,
    user: dict = Depends(get_current_user),
):
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    # Vérification de propriété via le portfolio parent
    portfolio = session.get(Portfolio, skill.portfolio_id)
    if not portfolio or portfolio.firebase_uid != user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="Vous n'êtes pas le propriétaire de ce portfolio.",
        )
    portfolio_id = skill.portfolio_id
    session.delete(skill)
    session.commit()
    return RedirectResponse(url=f"/portfolios/{portfolio_id}", status_code=303)


# Ajouter une expérience


@app.post("/portfolios/{portfolio_id}/experiences/")
def create_experience(
    portfolio_id: int,
    session: SessionDep,
    name: str = Form(...),
    company: str = Form(...),
    role: str = Form(...),
    duration: str = Form(...),
    description: str | None = Form(None),
):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    experience = Experience(
        name=name,
        company=company,
        role=role,
        duration=duration,
        description=description,
        portfolio_id=portfolio_id,
    )
    session.add(experience)
    session.commit()
    return RedirectResponse(url=f"/portfolios/{portfolio_id}", status_code=303)


# Supprimer une expérience
@app.post("/experiences/{experience_id}/delete")
def delete_experience(experience_id: int, session: SessionDep):
    experience = session.get(Experience, experience_id)
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    portfolio_id = experience.portfolio_id
    session.delete(experience)
    session.commit()
    return RedirectResponse(url=f"/portfolios/{portfolio_id}", status_code=303)


# Ajouter un projet
@app.post("/portfolios/{portfolio_id}/projects/")
def create_project(
    portfolio_id: int,
    session: SessionDep,
    name: str = Form(...),
    description: str | None = Form(None),
    link: str | None = Form(None),
):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    project = Project(
        name=name, description=description, link=link, portfolio_id=portfolio_id
    )
    session.add(project)
    session.commit()
    return RedirectResponse(url=f"/portfolios/{portfolio_id}", status_code=303)


# Supprimer un projet
@app.post("/projects/{project_id}/delete")
def delete_project(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    portfolio_id = project.portfolio_id
    session.delete(project)
    session.commit()
    return RedirectResponse(url=f"/portfolios/{portfolio_id}", status_code=303)
