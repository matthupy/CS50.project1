import os, requests, flask_login, datetime

# Flask imports
from flask import flash, Flask, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session

# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Werkzeug imports
from werkzeug.security import generate_password_hash, check_password_hash

# Internal imports
from user import *

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

login_manager = flask_login.LoginManager(app)
login_manager.init_app(app)

# Set up database
engine = create_engine(databaseURL)
db = scoped_session(sessionmaker(bind=engine))

# Goodreads API
goodreads_key = "Y1JjJVXjS3RRo5tGbrnOjQ"

# Flask Login Configuraiton
@login_manager.user_loader
def load_user(username):
    curr_user = User()
    curr_user.id = username
    return curr_user


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    sSQL = "select * from users where username = :username"
    user_exists = db.execute(sSQL, {"username": username}).fetchone()
    if user_exists is None:
        return

    user = User()
    user.id = username

    try:
        if check_password_hash(user_exists.password, request.form.get("password")):
            return user
        else:
            return
    except:
        return


@login_manager.unauthorized_handler
def unauthorized():
    flash("You must be logged in to view that page")
    return render_template("login.html")

# Application Routes
@app.route("/")
@flask_login.login_required
def index():
    return render_template("index.html", user=flask_login.current_user)


@app.route("/results", methods=["POST"])
@flask_login.login_required
def search_results():
    """ Display a list of search results """

    isbn = request.form.get("isbn")
    title = request.form.get("title")
    author = request.form.get("author")
    year = request.form.get("year")

    # Initialize filter list
    filters = []
    separator = " AND "

    # Create filters
    if (isbn is not None) and (len(isbn) != 0):
        filters.append(f"isbn like :isbn")
    if (title is not None) and (len(title) != 0):
        filters.append(f"upper(title) like upper(:title)")
    if (author is not None) and (len(author) != 0):
        filters.append(f"upper(author) like upper(\'%{author}%\')")
    if (year is not None) and (len(year) != 0):
        try:
            year = int(year)
        except:
            flash("Error: Please enter a valid year!", category="error")
            return redirect(url_for('index'))
        filters.append(f"year = :year")

    # Build query
    sSQL = "select * from books "
    sWhere = separator.join(filters)
    sOrderBy = " order by title "
    sLimit = " limit 100 "

    if len(filters) > 0:
        sSQL = sSQL + " where " + sWhere + sOrderBy + sLimit

    print(f"Executing SQL \r\n {sSQL} \r\n Values \r\n isbn={isbn} \r\n title={title} \r\n author={author} \r\n year={year}")

    # Execute the query
    books = db.execute(
        sSQL, {"isbn": isbn, "title": title, "author": author, "year": year}
    ).fetchall()

    return render_template("results.html", books=books, user=flask_login.current_user)


@app.route("/book/<string:isbn>", methods=["GET"])
@flask_login.login_required
def book(isbn):
    """ Display Book details """

    # Make sure the book exists
    sSQL = f"select * from books where isbn = :isbn"
    book = db.execute(sSQL, {"isbn": isbn}).fetchone()
    if book is None:
        return render_template(
            "error.html",
            message="No such book with that ISBN!",
            user=flask_login.current_user,
        )

    # Get Goodreads reviews
    res = getGoodreadsData(isbn)
    reviews_count = res["books"][0]["reviews_count"]
    average_rating = res["books"][0]["average_rating"]

    # Get User Reviews
    sSQL = "select * from reviews where isbn = :isbn"
    reviews = db.execute(sSQL, {"isbn": isbn}).fetchall()

    return render_template(
        "book.html",
        book=book,
        reviews_count=reviews_count,
        average_rating=average_rating,
        user=flask_login.current_user,
        reviews=reviews,
    )


@app.route("/book/<string:isbn>/review_submit", methods=["POST"])
@flask_login.login_required
def book_review_submit(isbn):
    """ Submit a review of a book """

    # Make sure the book exists
    sSQL = f"select * from books where isbn = :isbn"
    book = db.execute(sSQL, {"isbn": isbn}).fetchone()
    if book is None:
        return render_template(
            "error.html",
            message="No such book with that ISBN!",
            user=flask_login.current_user,
        )

    # Users should only be able to submit one review per book
    sSQL = f"select * from reviews where isbn = '{isbn}' and username = '{flask_login.current_user.id}'"
    print(f"executing SQL: \r\n {sSQL}")
    review = db.execute(sSQL).fetchone()
    # review = db.execute(sSQL, {"isbn":isbn, "username":flask_login.current_user.id})

    if review is not None:
        flash(
            "Error: You've already submitted a review for this book!", category="error"
        )
        return redirect(url_for("book", isbn=isbn))

    errors = []
    messages = []

    # Get the review info
    rating = request.form.get("rating")
    review = request.form.get("review-text")

    # Make sure the rating is a number
    try:
        rating = round(float(rating), 1)
    except ValueError:
        flash("Please submit a rating from 1 to 5", category="error")
        return redirect(url_for("book", isbn=isbn))

    if (rating < 1) or (rating > 5):
        flash("Please submit a rating from 1 to 5", category="error")
        return redirect(url_for("book", isbn=isbn))

    # Add the review
    sSQL = "insert into reviews (isbn, username, rating, review_text, update_date) values (:isbn, :username, :rating, :review_text, :update_date)"

    try:
        db.execute(
            sSQL,
            {
                "isbn": isbn,
                "username": flask_login.current_user.id,
                "rating": rating,
                "review_text": review,
                "update_date": datetime.datetime.now(),
            },
        )
        db.commit()
        flash("Review successfully submitted!", category="info")
    except Exception as e:
        errors.append(str(e))

    return redirect(url_for("book", isbn=isbn))


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Attempt to log a user in """

    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Make sure that the username exists
        sSQL = f"select * from users where username = :username"
        user = db.execute(sSQL, {"username": username}).fetchone()

        if (user is None) or (not check_password_hash(user.password, password)):
            flash("Invalid credentials. Please try again.", category="error")

        else:
            user = User()
            user.id = username
            flask_login.login_user(user)
            print("logged in with Flask")
            return redirect(url_for("index"))

    return render_template("login.html", error=error, user=None)


@app.route("/logout")
@flask_login.login_required
def logout():
    """ Attempt to log a user out """
    flask_login.logout_user()
    flash("Logged out successfully", category="info")
    return redirect(url_for('login'))

@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    """ Attempt to create a new user account """

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password2 = request.form.get("password2")

        # Make sure the passwords match
        if not (password == password2):
            flash("Passwords do not match!", category="error")
            return render_template("create_account.html", user=None)

        if (
            (username is None)
            or (len(username) == 0)
            or (password is None)
            or (len(password) == 0)
        ):
            flash(
                "Invalid username/password entered. Please enter both a username and a password.",
                category="error",
            )
            return render_template("create_account.html", user=None)

        # make sure that the username doesn't already exist
        sSQL = f"select * from users where username = :username"
        user = db.execute(sSQL, {"username": username}).fetchone()

        if user is not None:
            flash("Username is taken. Please enter a new username.", category="error")
            return render_template("create_account.html", user=None)

        # If we've gotten to this point, the username exists and there is a password. Create the account.
        hashed_password = generate_password_hash(password, method="sha256")
        sSQL = f"insert into users (username, password) values (:username, :hashed_password)"
        db.execute(sSQL, {"username": username, "hashed_password": hashed_password})
        db.commit()

        flash(f"User {username} created! Please log in.", "info")
    elif request.method == "GET":
        return render_template("create_account.html", user=None)

    return render_template("login.html", user=None)


@app.route("/api/book/<string:isbn>", methods=["GET"])
def book_api(isbn):
    """ Book API Endpoint, displays book details and stored reviews """

    # Make sure the book exists
    sSQL = f"select * from books where isbn = :isbn"
    book = db.execute(sSQL, {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Invalid ISBN"}), 422

    # Get GoodReads data
    res = getGoodreadsData(isbn)

    # Get all reviews
    sSQL = f"select * from reviews where isbn = :isbn"
    reviews = db.execute(sSQL, {"isbn": isbn}).fetchall()

    reviews_json = {}

    for review in reviews:

        reviews_json[review.id] = {
            "username": review.username,
            "rating": review.rating,
            "review_text": review.review_text,
            "timestamp": review.update_date,
        }

    print(reviews_json)

    return jsonify(
        {
            "isbn": book.isbn,
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "goodreads_reviews": res["books"][0]["reviews_count"],
            "goodreads_rating": res["books"][0]["average_rating"],
            "reviews": reviews_json,
        }
    )


def getGoodreadsData(list_isbn):
    """ Helper method to get GoodReads data on a specific book """

    res = requests.get(
        "https://www.goodreads.com/book/review_counts.json",
        params={"key": goodreads_key, "isbns": list_isbn},
    )
    return res.json()


if __name__ == "__main__":
    app.run()
