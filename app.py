from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/results")
def results():
    return render_template("results.html")


if __name__=="__main__":
    app.run(debug=True)