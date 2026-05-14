"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Database setup
Base = declarative_base()

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    schedule = Column(String)
    max_participants = Column(Integer)

class Signup(Base):
    __tablename__ = 'signups'
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'))
    email = Column(String)

engine = create_engine('sqlite:///activities.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Initial activities data
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# Populate database with initial data if empty
session = Session()
if not session.query(Activity).first():
    for name, details in initial_activities.items():
        act = Activity(
            name=name,
            description=details['description'],
            schedule=details['schedule'],
            max_participants=details['max_participants']
        )
        session.add(act)
        session.flush()  # To get id
        for email in details['participants']:
            signup = Signup(activity_id=act.id, email=email)
            session.add(signup)
    session.commit()
session.close()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    session = Session()
    acts = session.query(Activity).all()
    result = {}
    for act in acts:
        signups = session.query(Signup).filter_by(activity_id=act.id).all()
        participants = [s.email for s in signups]
        result[act.name] = {
            'description': act.description,
            'schedule': act.schedule,
            'max_participants': act.max_participants,
            'participants': participants
        }
    session.close()
    return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    session = Session()
    act = session.query(Activity).filter_by(name=activity_name).first()
    if not act:
        session.close()
        raise HTTPException(status_code=404, detail="Activity not found")

    current_count = session.query(Signup).filter_by(activity_id=act.id).count()
    if current_count >= act.max_participants:
        session.close()
        raise HTTPException(status_code=400, detail="Activity is full")

    if session.query(Signup).filter_by(activity_id=act.id, email=email).first():
        session.close()
        raise HTTPException(status_code=400, detail="Student is already signed up")

    signup = Signup(activity_id=act.id, email=email)
    session.add(signup)
    session.commit()
    session.close()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    session = Session()
    act = session.query(Activity).filter_by(name=activity_name).first()
    if not act:
        session.close()
        raise HTTPException(status_code=404, detail="Activity not found")

    signup = session.query(Signup).filter_by(activity_id=act.id, email=email).first()
    if not signup:
        session.close()
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    session.delete(signup)
    session.commit()
    session.close()
    return {"message": f"Unregistered {email} from {activity_name}"}
