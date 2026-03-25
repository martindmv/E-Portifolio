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
    Github : str
    Linkdin : str




@app.get("/")
def read_root():
    return {"Title": "E-portfolio"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.get("/portfolio/{portfolio_id}")