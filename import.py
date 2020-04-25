import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

try:
    engine = create_engine(os.getenv("DATABASE_URL"))
except:
    engine = create_engine("postgres://nalggygsngwfom:17c7b5e6419ca113378e80048d2962f34f7d0baab5051359fae2f87083666608@ec2-50-17-90-177.compute-1.amazonaws.com:5432/d96kc5d408oo3k")
    
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)

    # This skips the first row of the CSV file
    next(reader)

    counter = 0 # Initialize a counter
    for isbn, title, author, year in reader:
        counter += 1
        sSQL = f"insert into books (isbn, title, author, year) values (:isbn, :title, :author, :year)"
        db.execute(sSQL, {"isbn":isbn, "title":title, "author":author, "year":year})
        print(f"Added book ISBN # {isbn} - {title} by {author}, published {year}.")

        # Commit the transaction every 1000 rows to ensure the DB doesn't get overloaded
        if counter % 1000 == 0:
            db.commit() 

if __name__ == "__main__":
    main()