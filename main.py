from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from typing import Annotated
from contextlib import asynccontextmanager
import sqlite3
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Form
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
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
    firebase_uid: str | None = Field(default=None, index=True)  # ID utilisateur Firebase


sqlite_file_name = "database_portfolio.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


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
    # Migration : ajouter la colonne firebase_uid si elle n'existe pas encore
    try:
        conn = sqlite3.connect(sqlite_file_name)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(portfolio)")
        columns = [col[1] for col in cursor.fetchall()]
        if "firebase_uid" not in columns:
            cursor.execute("ALTER TABLE portfolio ADD COLUMN firebase_uid TEXT")
            conn.commit()
            print("✅ Migration : colonne 'firebase_uid' ajoutée à la table 'portfolio'")
        conn.close()
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
        name=name, formation=formation, github=github, linkedin=linkedin,
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
