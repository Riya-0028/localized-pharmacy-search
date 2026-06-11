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

@app.route("/save_pharmacy", methods=["POST"])
def save_pharmacy():

    sql = """
    INSERT INTO pharmacy
    (
    name,
    address,
    place,
    contact,
    license_number,
    username,
    password,
    approval_status,
    registered_date
    )
    VALUES
    (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """

    values = (
        request.form["name"],
        request.form["address"],
        request.form["place"],
        request.form["contact"],
        request.form["license"],
        request.form["username"],
        request.form["password"],
        "pending"  # Status is set to pending until admin approves
    )

    cursor.execute(sql, values)
    db.commit()

    # Redirect to a confirmation page
    return redirect("/pharmacy_registration_pending")


@app.route("/search")
def search():
    return render_template("search.html")




@app.route("/results", methods=["GET", "POST"])
def results():
    medicine_name = None
    pharmacies = []
    
    if request.method == "POST":
        medicine_name = request.form.get("medicine", "").strip()
    else:
        medicine_name = request.args.get("search", "").strip()
    
    if medicine_name:
        try:
            print("=== DATABASE STRUCTURE ===")
            
            # Show all tables in database
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("All tables in database:", tables)
            
            # Describe each table
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                print(f"\n{table_name} columns: {columns}")
                
                # Show sample data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                data = cursor.fetchall()
                print(f"{table_name} sample data: {data}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    return render_template("results.html", medicine_name=medicine_name, pharmacies=pharmacies)

@app.route("/pharmacy_register")
def pharmacy_register():

    return render_template(
        "pharmacy_register.html"
    )


@app.route("/pharmacy_login")
def pharmacy_login():

    return render_template(
        "pharmacy_login.html"
    )


@app.route("/pharmacy_registration_pending")
def pharmacy_registration_pending():
    return render_template("pharmacy_registration_pending.html")


@app.route("/verify_pharmacy_login", methods=["POST"])
def verify_pharmacy_login():
    username = request.form["username"]
    password = request.form["password"]
    
    try:
        sql = "SELECT id, name, username, password, approval_status FROM pharmacy WHERE username = %s AND password = %s"
        cursor.execute(sql, (username, password))
        result = cursor.fetchone()
        
        if result:
            # result[4] is approval_status (id, name, username, password, approval_status)
            approval_status = result[4]
            
            if approval_status == "approved":
                # Login successful
                return redirect("/pharmacy_dashboard")
            elif approval_status == "pending":
                # Pharmacy registration is pending approval
                return render_template("pharmacy_login.html", message="Your pharmacy registration is pending admin approval. Please wait for verification.", error=True)
            else:
                # Pharmacy is rejected
                return render_template("pharmacy_login.html", message="Your pharmacy registration has been rejected. Please contact support.", error=True)
        else:
            return render_template("pharmacy_login.html", message="Invalid username or password.", error=True)
    except Exception as e:
        print(f"Login error: {e}")
        return render_template("pharmacy_login.html", message="An error occurred during login. Please try again.", error=True)


@app.route("/pharmacy_dashboard")
def pharmacy_dashboard():
    return render_template("pharmacy_dashboard.html")


if __name__=="__main__":
    app.run(debug=True)