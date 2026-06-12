from flask import *
import mysql.connector

app = Flask(__name__)
app.secret_key = "super_secret_key_for_pharmacy_session"
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

@app.route("/verify_user_login", methods=["POST"])
def verify_user_login():
    name = request.form["name"].strip()
    phone = request.form["phone"].strip()
    
    try:
        local_cursor = db.cursor()
        sql = "SELECT user_id, name, place FROM users WHERE name = %s AND phone = %s"
        local_cursor.execute(sql, (name, phone))
        result = local_cursor.fetchone()
        local_cursor.close()
        
        if result:
            session['user_id'] = result[0]
            session['user_name'] = result[1]
            session['user_place'] = result[2]
            return redirect("/search")
        else:
            return render_template("login.html", message="User account not found. Check details or sign in below.", error=True)
    except Exception as e:
        print(f"Customer Login Error: {e}")
        return render_template("login.html", message="An error occurred. Please try again.", error=True)


@app.route("/save_user", methods=["POST"])
def save_user():
    name = request.form["name"].strip()
    place = request.form["place"].strip()
    phone = request.form["phone"].strip()

    try:
        local_cursor = db.cursor()
        sql = """
        INSERT INTO users (name, place, phone)
        VALUES (%s, %s, %s)
        """
        local_cursor.execute(sql, (name, place, phone))
        db.commit()
        
        local_cursor.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
        user_row = local_cursor.fetchone()
        if user_row:
            session['user_id'] = user_row[0]
            session['user_name'] = name
            session['user_place'] = place
            
        local_cursor.close()
        return redirect("/search")
        
    except Exception as e:
        print(f"Database Save Error: {e}")
        return "Failed to register user. Check your database structure."

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
    
    # 1. Capture the searched medicine name from form or URL bar
    if request.method == "POST":
        medicine_name = request.form.get("medicine", "").strip()
    else:
        medicine_name = request.args.get("search", "").strip()
    
    if medicine_name:
        try:
            # Create a fresh cursor with dictionary=True so rows can be read by name in HTML
            local_cursor = db.cursor(dictionary=True)
            
            # 🌟 CORE OPERATIONAL JOIN QUERY 🌟
            # Uses your exact column names: medicine_name and quantity
            query = """
                SELECT P.name AS pharmacy_name, P.address, I.quantity 
                FROM inventory I 
                JOIN pharmacy P ON I.pharmacy_id = P.pharmacy_id 
                JOIN medicine M ON I.medicine_id = M.medicine_id 
                WHERE M.medicine_name = %s AND I.quantity > 0
            """
            
            local_cursor.execute(query, (medicine_name,))
            pharmacies = local_cursor.fetchall()  # This fills our list with actual pharmacies!
            
            local_cursor.close()  # Clean up cursor immediately
            
        except Exception as e:
            print(f"Database Query Error: {e}")
            pharmacies = []  # Fallback to empty list if database fails
            
    # 2. Pass both the medicine name AND the results list to your template
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


@app.route("/verify_pharmacy_login", methods=["POST"]) # This route remains unchanged
def verify_pharmacy_login():
    username = request.form["username"]
    password = request.form["password"]
    
    try:
        # Select pharmacy_id, name, and approval_status for verification and session
        sql = "SELECT pharmacy_id, name, approval_status FROM pharmacy WHERE username = %s AND password = %s"
        cursor.execute(sql, (username, password))
        result = cursor.fetchone()
        
        if result:
            pharmacy_id = result[0]
            pharmacy_name = result[1]
            approval_status = result[2] # approval_status is now at index 2
            
            # Treat NULL approval_status as approved for backward compatibility
            if approval_status is None or approval_status == "approved":
                session['pharmacy_id'] = pharmacy_id
                session['pharmacy_name'] = pharmacy_name
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
    if 'pharmacy_id' not in session:
        return redirect("/pharmacy_login")

    pharmacy_id = session['pharmacy_id']
    pharmacy_name = session['pharmacy_name']

    try:
        local_cursor = db.cursor(dictionary=True)

        # Fetch all inventory items for this specific pharmacy
        inventory_query = """
            SELECT M.medicine_name, M.generic_name, I.quantity 
            FROM inventory I 
            JOIN medicine M ON I.medicine_id = M.medicine_id 
            WHERE I.pharmacy_id = %s
        """
        local_cursor.execute(inventory_query, (pharmacy_id,))
        inventory = local_cursor.fetchall()

        # Fetch low stock alerts (items with quantity less than 5)
        alerts_query = """
            SELECT M.medicine_name, M.generic_name, I.quantity 
            FROM inventory I 
            JOIN medicine M ON I.medicine_id = M.medicine_id 
            WHERE I.pharmacy_id = %s AND I.quantity < 5
        """
        local_cursor.execute(alerts_query, (pharmacy_id,))
        alerts = local_cursor.fetchall()

        local_cursor.close()
        return render_template("pharmacy_dashboard.html", pharmacy_name=pharmacy_name, inventory=inventory, alerts=alerts)
    except Exception as e:
        print(f"Dashboard Error: {e}")
        return "An error occurred loading the dashboard."

@app.route("/admin_dashboard")
def admin_dashboard():
    try:
        local_cursor = db.cursor(dictionary=True)
        
        # 🔍 Make sure these column names match your database EXACTLY
        query = """
            SELECT pharmacy_id, name, license_number, place, contact 
            FROM pharmacy 
            WHERE approval_status = 'pending'
        """
        local_cursor.execute(query)
        pending_pharmacies = local_cursor.fetchall()
        local_cursor.close()
        
        return render_template("admin_dashboard.html", pharmacies=pending_pharmacies)
    except Exception as e:
        # 🌟 This print statement will tell us the EXACT error in your VS Code terminal!
        print(f"CRITICAL ADMIN ERROR: {e}")
        return f"Dashboard Error: {e}"

@app.route("/approve_pharmacy/<int:pharmacy_id>", methods=["POST"])
def approve_pharmacy(pharmacy_id):
    try:
        local_cursor = db.cursor()
        
        # 🔐 Update status from 'pending' to 'approved'
        query = "UPDATE pharmacy SET approval_status = 'approved' WHERE pharmacy_id = %s"
        local_cursor.execute(query, (pharmacy_id,))
        db.commit()
        local_cursor.close()
        
        # Refresh the dashboard to show they are gone from the pending list
        return redirect("/admin_dashboard")
    except Exception as e:
        print(f"Approval Error: {e}")
        return "Failed to approve pharmacy."


if __name__=="__main__":
    app.run(debug=True)