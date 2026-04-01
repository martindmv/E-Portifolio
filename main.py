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

db_portfolios = [{
  "id": 1,
  "name": "Victor Eymard",
  "formation": "Data",
  "experience": [
    {
      "id": 0,
      "company": "string",
      "role": "string",
      "duration": "string",
      "description": "string"
    }
  ],
  "projects": [
    {
      "id": 0,
      "name": "string",
      "description": "string",
      "link": "string"
    }
  ],
  "skills": [
    {
      "id": 0,
      "name": "string",
      "level": "string"
    }
  ],
  "github": "github.com/victor",
  "linkedin": "linkedin.com/victor"
}]


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
    return {"message": "Portfolio not found"}


# Create a post endpoint to add a new portfolio.
# Parameters should include name, formation, experience, projects, skills, github and linkedin.
# The portfolio needs to be added to a temporary list of portfolios
# id needs to be generated automatically --> use the length of the list + 1
@app.post("/portfolio")
def create_portfolio(name: str, 
                    formation: str,
                    experience: list[Experience],
                    projects: list[Project],
                    skills: list[Skill],
                    github: str,
                    linkedin: str):
    
    portfolio = Portfolio(
        id=len(db_portfolios) + 1,  # generating id automatically
        name=name,
        formation=formation,
        experience=experience,
        projects=projects,
        skills=skills,
        github=github,
        linkedin=linkedin
    )
    db_portfolios.append(portfolio)
    return {"message": "Portfolio created successfully!", "portfolios": db_portfolios}

# Welcome page with list of available portfolios
@app.get("/portfolio")
def list_portfolios():
    return {"message": "Welcome to the E-portfolio website! Use /portfolio/{portfolio_id} to view a specific portfolio.", "portfolios": db_portfolios}
