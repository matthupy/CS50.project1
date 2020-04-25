# Project 1

Web Programming with Python and JavaScript

# Application Description

This application allows users query for books based on any combination ISBN, Title, Author or Published Year filters. On the book details screen, users can view additional data, such as the Number of Reviews and Average Star Rating out of 5 from GoodReads. Finally, users can add their own reviews and ratings as well as view the reviews and ratings from other users on this platform.

# File Descriptions

| File Name | Description |
| --- |--- |
|application.py | Main application file, handles database connection, Flask application setup, Route registration, and User sessions.
|books.csv | Provided CSV file of books
|import.py | Script to import the values from books.csv into the database table "books"
| Project1.md | Project definition
| README.md | This file
| requirements.txt | List of all required Python packages
| user.py | Class definition for applicaiton users
|/templates/base.css | CSS used globally by the application in conjunction with Bootstrap
|/templates/base.css.map | System-generated maping file
|/templates/base.scss | SASS programming interface used to generate base.css and base.css.map
|/templates/book.html | HTML file for the Book Details page
|/templates/create_account.html | HTML for the Create Account page
|/templates/error.html | HTML for the general Error page
|/templates/index.html | HTML for the applicaiton home page, which contains the search functionality when a user is logged in
|/templates/layout.html | Base HTML page that is imported by all other pages. Contains logic for error and alert messages, navigation bar logic, and references to all CSS used globally.
|/templates/login.html | HTML for the Login page
|/templates/results.html | HTML for the Search Results page