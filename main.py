from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Skill(BaseModel):
    id : int
    name : str 
    level : str

class Project(BaseModel):
    id : int
    name : str 
    description : str
    link : str | None = None

class Experience(BaseModel):
    id : int
    company : str 
    role : str
    duration : str
    description : str

class Portfolio(BaseModel):
    id : int
    name : str 
    formation : str
    experience : list[Experience]
    projects : list[Project]
    skills : list[Skill]
    github : str
    linkedin : str




@app.get("/")
def read_root():
    return {"Title": "E-portfolio"}

# Create a portfolio endpoint that takes a portfolio_id as a path parameter and returns a JSON object with the portfolio details. For simplicity, you can return a hardcoded portfolio object.


@app.get("/portfolio/{portfolio_id}")
def read_portfolio(portfolio_id: int):
    portfolio = Portfolio(
        id=portfolio_id,
        name="Martin Demerdjiev",
        formation="EPF Ecole d'Ingénieurs",
        experience=[
            Experience(
                id=1,
                company="Stellantis",
                role="Operator",
                duration="1 month",
                description="Stage ouvrier dans une usine de production automobile."
            )
        ],
        projects=[
            Project(
                id=1,
                name="OceENS",
                description="Automatisation de la création et collecte de sondage réalisés par les professeurs de l'EPF à chaque fin de semestre.",
                link="https://github.com/iamjuli3n-cmd/OceENS"
            )
        ],
        skills=[
            Skill(
                id=1,
                name="Python",
                level="Advanced"
            )
        ],
        github="https://github.com/martindmv",
        linkedin="https://linkedin.com/in/martindemerdjiev"
    )
    return portfolio

