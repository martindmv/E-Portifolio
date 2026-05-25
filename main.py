from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Form
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from fastapi.responses import RedirectResponse


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
):
    portfolio = Portfolio(
        name=name, formation=formation, github=github, linkedin=linkedin
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


@app.get("/portfolios/{portfolio_id}", response_class=HTMLResponse)
def read_portfolio(request: Request, portfolio_id: int, session: SessionDep):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return templates.TemplateResponse(
        request=request, name="portfolio_detail.html", context={"portfolio": portfolio}
    )


@app.delete("/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: int, session: SessionDep):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    session.delete(portfolio)
    session.commit()
    return {"ok": True}


# Ajouter une compétence à un portfolio
@app.post("/portfolios/{portfolio_id}/skills/")
def create_skill(
    portfolio_id: int,
    session: SessionDep,
    name: str = Form(...),
    level: str = Form(...),
):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    skill = Skill(name=name, level=level, portfolio_id=portfolio_id)
    session.add(skill)
    session.commit()
    return RedirectResponse(url=f"/portfolios/{portfolio_id}", status_code=303)


# Supprimer une compétence
@app.post("/skills/{skill_id}/delete")
def delete_skill(skill_id: int, session: SessionDep):
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    portfolio_id = skill.portfolio_id
    session.delete(skill)
    session.commit()
    return RedirectResponse(url=f"/portfolios/{portfolio_id}", status_code=303)
