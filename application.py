import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    # Default the database URL to a known-good
    databaseURL = "postgres://nalggygsngwfom:17c7b5e6419ca113378e80048d2962f34f7d0baab5051359fae2f87083666608@ec2-50-17-90-177.compute-1.amazonaws.com:5432/d96kc5d408oo3k"
    print("Warning: DATABASE_URL is not set!")
else:
    databaseURL = os.getenv("DATABASE_URL")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(databaseURL)
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return "Project 1: TODO"

if __name__=="__main__":
    app.run()