from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException

app = FastAPI()

# Va chercher mes fichiers HTML dans le dossier templates
templates = Jinja2Templates(directory="templates")


class Skill(BaseModel):
    id: int
    name: str
    level: str


class Project(BaseModel):
    id: int
    name: str
    description: str
    link: str | None = None


class Experience(BaseModel):
    id: int
    company: str
    role: str
    duration: str
    description: str


class Portfolio(BaseModel):
    id: int
    name: str
    formation: str
    experience: list[Experience]
    projects: list[Project]
    skills: list[Skill]
    github: str
    linkedin: str


db_portfolios = [
    {
        "id": 1,
        "name": "Victor Eymard",
        "formation": "Data",
        "experience": [
            {
                "id": 0,
                "company": "string",
                "role": "string",
                "duration": "string",
                "description": "string",
            }
        ],
        "projects": [
            {"id": 0, "name": "string", "description": "string", "link": "string"}
        ],
        "skills": [{"id": 0, "name": "string", "level": "string"}],
        "github": "github.com/victor",
        "linkedin": "linkedin.com/victor",
    }
]


@app.get("/")
def read_root():
    return {"Title": "E-portfolio"}


# Create a get portfolio endpoint that takes a portfolio_id as a path parameter
# and returns the portfolio with the corresponding id from a temporary list of portfolios.


@app.get("/portfolio/{portfolio_id}")
def read_portfolio(portfolio_id: int):
    for portfolio in db_portfolios:
        if portfolio["id"] == portfolio_id:
            return portfolio
    raise HTTPException(status_code=404, detail="Portfolio not found")


# Erreur : return afficher "Internal Server Error"
# en FAST API utiliser raise pour detecter une erreur


# Create a post endpoint to add a new portfolio.
# Parameters should include name, formation, experience, projects, skills, github and linkedin.
# The portfolio needs to be added to a temporary list of portfolios
# id needs to be generated automatically --> use the length of the list + 1
@app.post("/portfolio")
def create_portfolio(
    name: str,
    formation: str,
    experience: list[Experience],
    projects: list[Project],
    skills: list[Skill],
    github: str,
    linkedin: str,
):

    portfolio = Portfolio(
        id=len(db_portfolios) + 1,  # generating id automatically
        name=name,
        formation=formation,
        experience=experience,
        projects=projects,
        skills=skills,
        github=github,
        linkedin=linkedin,
    )
    db_portfolios.append(portfolio)
    return {"message": "Portfolio created successfully!", "portfolios": db_portfolios}


# Partie Frond End
# Welcome page with list of available portfolios
@app.get("/portfolio", response_class=HTMLResponse)
def list_portfolios(request: Request, test_str: str = "Test it's working"):
    context = {"test_str": test_str, "db_portfolios": db_portfolios}

    return templates.TemplateResponse(request, "home.html", context=context)
