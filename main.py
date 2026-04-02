# ============================================================
#  main.py — The entire backend in ONE simple file
#  Run it with:  uvicorn main:app --reload
# ============================================================

# Step 1: Import the tools we need
from fastapi import FastAPI                        # the web framework
from fastapi.middleware.cors import CORSMiddleware # lets browser talk to this server
from fastapi.responses import HTMLResponse         # lets us send HTML pages
from pydantic import BaseModel                     # checks that data is correct
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, DeclarativeBase  # database tools

import os


# ============================================================
# Step 2: Set up the Database
# ============================================================

# This creates a file called "todos.db" in the same folder
engine = create_engine("sqlite:///todos.db")

# A "session" is how we talk to the database (like opening a notebook)
Session = sessionmaker(bind=engine)

# Base is the starting point for all our database tables
class Base(DeclarativeBase):
    pass


# ============================================================
# Step 3: Create a Table (called a "Model")
# ============================================================

# This class = one table in the database called "todos"
class Todo(Base):
    __tablename__ = "todos"          # name of the table

    id    = Column(Integer, primary_key=True)  # auto-number: 1, 2, 3...
    task  = Column(String)                     # the todo text
    done  = Column(Boolean, default=False)     # is it finished? starts as False

# Create the table in the database (only runs if table doesn't exist yet)
Base.metadata.create_all(engine)


# ============================================================
# Step 4: Start the FastAPI app
# ============================================================

app = FastAPI()

# Allow the browser (frontend) to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow everyone (fine for learning)
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Step 5: Define what data looks like when sent from frontend
# ============================================================

# When the frontend sends a new todo, it must have a "task" field
class TodoInput(BaseModel):
    task: str


# ============================================================
# Step 6: Create the API Routes (the "doors" to our server)
# ============================================================

# --- GET all todos ---
# Browser visits: GET http://localhost:8000/todos
@app.get("/todos")
def get_todos():
    db = Session()                          # open connection to database
    todos = db.query(Todo).all()            # get ALL rows from the todos table
    db.close()                              # close connection

    # Convert each Todo object to a simple dictionary so it can be sent as JSON
    return [{"id": t.id, "task": t.task, "done": t.done} for t in todos]


# --- POST (create) a new todo ---
# Browser sends: POST http://localhost:8000/todos  with body: { "task": "Buy milk" }
@app.post("/todos")
def create_todo(data: TodoInput):           # data = the JSON the browser sent
    db = Session()
    new_todo = Todo(task=data.task)         # create a new row
    db.add(new_todo)                        # add it to the database
    db.commit()                             # save it permanently
    db.refresh(new_todo)                    # reload it to get the auto-generated id
    db.close()

    return {"id": new_todo.id, "task": new_todo.task, "done": new_todo.done}


# --- PATCH (update) a todo — mark as done or not done ---
# Browser sends: PATCH http://localhost:8000/todos/1  with body: { "done": true }
@app.patch("/todos/{todo_id}")
def update_todo(todo_id: int, data: dict): # todo_id comes from the URL
    db = Session()
    todo = db.query(Todo).filter(Todo.id == todo_id).first()  # find the row

    if todo is None:
        db.close()
        return {"error": "Todo not found"}

    todo.done = data["done"]               # update the done field
    db.commit()                            # save the change
    db.close()

    return {"id": todo.id, "task": todo.task, "done": todo.done}


# --- DELETE a todo ---
# Browser sends: DELETE http://localhost:8000/todos/1
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    db = Session()
    todo = db.query(Todo).filter(Todo.id == todo_id).first()  # find the row

    if todo is None:
        db.close()
        return {"error": "Todo not found"}

    db.delete(todo)                        # remove the row
    db.commit()                            # save the change
    db.close()

    return {"message": "Deleted successfully"}


# --- Serve the frontend HTML page ---
# When someone opens http://localhost:8000 in browser
@app.get("/", response_class=HTMLResponse)
def home():
    # Read and return the index.html file
    with open("templates/index.html") as f:
        return f.read()
