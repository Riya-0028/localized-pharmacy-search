from flask import *
import mysql.connector

app = Flask(__name__)
db = mysql.connector.connect(

host="localhost",

user="root",

password="riya*dbms39",

database="pharmacy_db"

)

cursor = db.cursor()

@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/login")
def login():
    return render_template("login.html")
@app.route("/save_user", methods=["POST"])
def save_user():

    name = request.form["name"]

    place = request.form["place"]

    phone = request.form["phone"]

    sql = """
    INSERT INTO users
    (name, place, phone)
    VALUES (%s,%s,%s)
    """

    cursor.execute(
        sql,
        (
            name,
            place,
            phone
        )
    )

    db.commit()

    return redirect("/search")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/results")
def results():
    return render_template("results.html")


if __name__=="__main__":
    app.run(debug=True)