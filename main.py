from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Form
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
    experience: list["Experience"] = Relationship(back_populates="portfolio")
    project: list["Project"] = Relationship(back_populates="portfolio")
    skill: list["Skill"] = Relationship(back_populates="portfolio")
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

app = FastAPI()


# Will search my HTML files within the "Templates" file
templates = Jinja2Templates(directory="templates")

#Create the datebase 
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/portfolios/")
def create_portfolio(
    name: str = Form(...),
    formation: str = Form(...),
    github: str | None = Form(None),
    linkedin: str | None = Form(None),
    session: SessionDep = None
):
    portfolio = Portfolio(name=name, formation=formation, github=github, linkedin=linkedin)
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
    return templates.TemplateResponse("home.html", {"request": request, "db_portfolios": portfolios})


@app.get("/portfolios/create", response_class=HTMLResponse)
def create_portfolio_page(request: Request):
    return templates.TemplateResponse("create_portfolio.html", {"request": request})


@app.get("/portfolios/{portfolio_id}")
def read_portfolio(portfolio_id: int, session: SessionDep) -> Portfolio:
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@app.delete("/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: int, session: SessionDep):
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    session.delete(portfolio)
    session.commit()
    return {"ok": True}