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
        # 🌟 Adding buffered=True completely fixes the 'Unread result found' bug!
        local_cursor = db.cursor(buffered=True)
        
        sql = """
        INSERT INTO users (name, place, phone)
        VALUES (%s, %s, %s)
        """
        local_cursor.execute(sql, (name, place, phone))
        db.commit()
        
        # Now this second query can execute cleanly on the same connector!
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
    # 🔒 EMERGENCY SEARCH: Force clear any lingering user sessions to guarantee NO buttons show up
    session.pop('user_id', None)
    
    medicine_name = None
    pharmacies = []
    
    if request.method == "POST":
        medicine_name = request.form.get("medicine", "").strip()
    else:
        medicine_name = request.args.get("search", "").strip()
    
    if medicine_name:
        try:
            local_cursor = db.cursor(dictionary=True)
            # Make sure pharmacy_id is included in the SELECT statement
            query = """
                SELECT P.pharmacy_id, P.name AS pharmacy_name, P.address, I.quantity 
                FROM inventory I 
                JOIN pharmacy P ON I.pharmacy_id = P.pharmacy_id 
                JOIN medicine M ON I.medicine_id = M.medicine_id 
                WHERE M.medicine_name = %s AND I.quantity > 0
            """
            local_cursor.execute(query, (medicine_name,))
            pharmacies = local_cursor.fetchall()
            local_cursor.close()
        except Exception as e:
            print(f"Database Query Error: {e}")
            
    return render_template("results.html", medicine_name=medicine_name, pharmacies=pharmacies)


@app.route("/user_results", methods=["GET", "POST"])
def user_results():
    # 🔑 AUTHENTICATED SEARCH: Only allowed if explicitly logged in
    if 'user_id' not in session:
        return redirect("/login")
        
    medicine_name = None
    pharmacies = []
    
    if request.method == "POST":
        medicine_name = request.form.get("medicine", "").strip()
    else:
        medicine_name = request.args.get("search", "").strip()
        
    if medicine_name:
        try:
            local_cursor = db.cursor(dictionary=True)
            query = """
                SELECT P.pharmacy_id, P.name AS pharmacy_name, P.address, I.quantity 
                FROM inventory I 
                JOIN pharmacy P ON I.pharmacy_id = P.pharmacy_id 
                JOIN medicine M ON I.medicine_id = M.medicine_id 
                WHERE M.medicine_name = %s AND I.quantity > 0
            """
            local_cursor.execute(query, (medicine_name,))
            pharmacies = local_cursor.fetchall()
            local_cursor.close()
        except Exception as e:
            print(f"Database Query Error: {e}")
            
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

        # 📊 1. Count distinct medicine listings in inventory
        local_cursor.execute("SELECT COUNT(*) AS total FROM inventory WHERE pharmacy_id = %s", (pharmacy_id,))
        med_count = local_cursor.fetchone()['total']

        # 📊 2. Count real completed or active orders from the orders table
        local_cursor.execute("SELECT COUNT(*) AS total FROM orders WHERE pharmacy_id = %s", (pharmacy_id,))
        sales_count = local_cursor.fetchone()['total']

        # 📊 3. Count unique customers who have interacted with this shop
        local_cursor.execute("SELECT COUNT(DISTINCT user_id) AS total FROM orders WHERE pharmacy_id = %s", (pharmacy_id,))
        customer_count = local_cursor.fetchone()['total']

        # 📋 REAL DATA QUERY: Pull live rows from the orders table joined with user details!
        query = """
            SELECT O.order_id, O.medicine_name, O.booking_type, O.status, U.name AS customer_name 
            FROM orders O
            JOIN users U ON O.user_id = U.user_id
            WHERE O.pharmacy_id = %s
            ORDER BY O.created_at DESC
        """
        local_cursor.execute(query, (pharmacy_id,))
        recent_requests = local_cursor.fetchall()
        
        local_cursor.close()
        
        return render_template(
            "pharmacy_dashboard.html", 
            pharmacy_name=pharmacy_name, 
            med_count=med_count, 
            sales_count=sales_count, 
            customer_count=customer_count,
            recent_requests=recent_requests
        )
    except Exception as e:
        print(f"Dashboard Metrics Error: {e}")
        return f"An error occurred loading dashboard data: {e}"
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
@app.route("/add_medicine")
def add_medicine():
    if 'pharmacy_id' not in session:
        return redirect("/pharmacy_login")
    return render_template("add_medicine.html")


@app.route("/save_new_medicine", methods=["POST"])
def save_new_medicine():
    if 'pharmacy_id' not in session:
        return redirect("/pharmacy_login")
        
    pharmacy_id = session['pharmacy_id']
    med_name = request.form["medicine_name"].strip()
    gen_name = request.form["generic_name"].strip()
    qty = request.form["quantity"].strip()
    
    try:
        local_cursor = db.cursor(buffered=True)
        
        # 1. Check if this medicine exists globally in the master medicine catalog table
        local_cursor.execute("SELECT medicine_id FROM medicine WHERE medicine_name = %s", (med_name,))
        med_row = local_cursor.fetchone()
        
        if med_row:
            medicine_id = med_row[0]
        else:
            # If it's a completely new drug type, insert it into the master dictionary catalog first
            local_cursor.execute("INSERT INTO medicine (medicine_name, generic_name) VALUES (%s, %s)", (med_name, gen_name))
            db.commit()
            medicine_id = local_cursor.lastrowid
            
        # 2. Check if this shop already has a row tracking this item in their active inventory
        local_cursor.execute("SELECT inventory_id FROM inventory WHERE pharmacy_id = %s AND medicine_id = %s", (pharmacy_id, medicine_id))
        inv_row = local_cursor.fetchone()
        
        if inv_row:
            # If it already exists, increment the stock count values cleanly
            local_cursor.execute("UPDATE inventory SET quantity = quantity + %s WHERE inventory_id = %s", (qty, inv_row[0]))
        else:
            # If it is their first time storing this product, insert a new relational reference row
            local_cursor.execute("INSERT INTO inventory (pharmacy_id, medicine_id, quantity) VALUES (%s, %s, %s)", (pharmacy_id, medicine_id, qty))
            
        db.commit()
        local_cursor.close()
        return redirect("/pharmacy_dashboard")
        
    except Exception as e:
        print(f"Inventory Add Error: {e}")
        return f"Failed to log stock asset: {e}"    
@app.route("/view_inventory")
def view_inventory():
    if 'pharmacy_id' not in session:
        return redirect("/pharmacy_login")
        
    pharmacy_id = session['pharmacy_id']
    pharmacy_name = session['pharmacy_name']
    
    try:
        local_cursor = db.cursor(dictionary=True)
        
        # 🔍 Fetches all medicine items and stock numbers logged under this specific shop ID
        query = """
            SELECT M.medicine_name, M.generic_name, I.quantity 
            FROM inventory I 
            JOIN medicine M ON I.medicine_id = M.medicine_id 
            WHERE I.pharmacy_id = %s
            ORDER BY M.medicine_name ASC
        """
        local_cursor.execute(query, (pharmacy_id,))
        my_stock = local_cursor.fetchall()
        local_cursor.close()
        
        return render_template("view_inventory.html", pharmacy_name=pharmacy_name, inventory=my_stock)
        
    except Exception as e:
        print(f"Inventory View Error: {e}")
        return f"Failed to retrieve stock records: {e}"   
@app.route("/action_reserve", methods=["POST"])
def action_reserve():
    if 'user_id' not in session:
        return redirect("/login")
        
    user_id = session['user_id']
    medicine = request.form.get("medicine_name")
    pharmacy_id = request.form.get("pharmacy_id")
    
    try:
        local_cursor = db.cursor()
        sql = """
            INSERT INTO orders (user_id, pharmacy_id, medicine_name, booking_type, status) 
            VALUES (%s, %s, %s, 'Reserve', 'Awaiting Action')
        """
        local_cursor.execute(sql, (user_id, pharmacy_id, medicine))
        db.commit()
        local_cursor.close()
        
        # 🎨 Beautiful HTML Design Return Block
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="/static/style.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="dashboard-container" style="display: flex; align-items: center; justify-content: center; min-height: 100vh;">
                <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 20px; padding: 40px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); max-width: 500px; width: 100%; text-align: center; color: white; font-family: sans-serif;">
                    <div style="font-size: 65px; color: #4caf50; margin-bottom: 20px;">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <h2 style="margin-bottom: 10px; font-weight: bold; color: white;">Reservation Confirmed!</h2>
                    <p style="opacity: 0.9; font-size: 15px; margin-bottom: 25px; line-height: 1.6;">
                        Great news! <strong>{medicine}</strong> has been successfully reserved under your name for local counter pickup. The pharmacy storefront has been instantly alerted to lock down your stock.
                    </p>
                    
                    <div style="background: rgba(0,0,0,0.15); padding: 15px; border-radius: 8px; margin-bottom: 30px; border: 1px solid rgba(255,255,255,0.1); text-align: left; font-size: 14px;">
                        <p style="margin: 0 0 8px 0;"><i class="fas fa-pills" style="color: #ffc107; margin-right: 8px;"></i> <strong>Item:</strong> {medicine}</p>
                        <p style="margin: 0;"><i class="fas fa-hand-holding-medical" style="color: #03a9f4; margin-right: 8px;"></i> <strong>Fulfillment:</strong> Walk-in Store Pickup</p>
                    </div>

                    <a href="/search" class="btn btn-primary" style="text-decoration: none; display: inline-block; width: 100%; padding: 12px; background: #1976d2; color: white; border-radius: 8px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 12px rgba(25,118,210,0.3);">
                        <i class="fas fa-arrow-left"></i> Back to Search Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        print(f"Reservation Error: {e}")
        return f"Failed to process reservation: {e}"


@app.route("/action_order", methods=["POST"])
def action_order():
    if 'user_id' not in session:
        return redirect("/login")
        
    user_id = session['user_id']
    medicine = request.form.get("medicine_name")
    pharmacy_id = request.form.get("pharmacy_id")
    
    try:
        local_cursor = db.cursor()
        sql = """
            INSERT INTO orders (user_id, pharmacy_id, medicine_name, booking_type, status) 
            VALUES (%s, %s, %s, 'Delivery', 'Awaiting Action')
        """
        local_cursor.execute(sql, (user_id, pharmacy_id, medicine))
        db.commit()
        local_cursor.close()
        
        # 🎨 Beautiful HTML Design Return Block
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="/static/style.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="dashboard-container" style="display: flex; align-items: center; justify-content: center; min-height: 100vh;">
                <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 20px; padding: 40px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); max-width: 500px; width: 100%; text-align: center; color: white; font-family: sans-serif;">
                    <div style="font-size: 65px; color: #2e7d32; margin-bottom: 20px;">
                        <i class="fas fa-shipping-fast"></i>
                    </div>
                    <h2 style="margin-bottom: 10px; font-weight: bold; color: white;">Order Dispatched!</h2>
                    <p style="opacity: 0.9; font-size: 15px; margin-bottom: 25px; line-height: 1.6;">
                        Success! Your order for <strong>{medicine}</strong> has been logged. The pharmacy team is currently preparing your package for Home Delivery, and an agent will move out shortly.
                    </p>
                    
                    <div style="background: rgba(0,0,0,0.15); padding: 15px; border-radius: 8px; margin-bottom: 30px; border: 1px solid rgba(255,255,255,0.1); text-align: left; font-size: 14px;">
                        <p style="margin: 0 0 8px 0;"><i class="fas fa-pills" style="color: #ffc107; margin-right: 8px;"></i> <strong>Item:</strong> {medicine}</p>
                        <p style="margin: 0;"><i class="fas fa-truck" style="color: #4caf50; margin-right: 8px;"></i> <strong>Fulfillment:</strong> Home Delivery Logistic</p>
                    </div>

                    <a href="/search" class="btn btn-primary" style="text-decoration: none; display: inline-block; width: 100%; padding: 12px; background: #2e7d32; color: white; border-radius: 8px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 12px rgba(46,125,50,0.3);">
                        <i class="fas fa-arrow-left"></i> Back to Search Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        print(f"Ordering Error: {e}")
        return f"Failed to process delivery order: {e}"  
@app.route("/confirm_dispatch", methods=["POST"])
def confirm_dispatch():
    if 'pharmacy_id' not in session:
        return redirect("/pharmacy_login")
        
    order_id = request.form.get("order_id")
    
    try:
        local_cursor = db.cursor()
        
        # 🔄 Update the status of this specific order entry in our database
        sql = "UPDATE orders SET status = 'Dispatched' WHERE order_id = %s"
        local_cursor.execute(sql, (order_id,))
        db.commit()
        
        local_cursor.close()
        # 🔄 Refresh the dashboard page instantly to show the updated state!
        return redirect("/pharmacy_dashboard")
        
    except Exception as e:
        print(f"Dispatch Error: {e}")
        return f"Failed to finalize dispatch operation: {e}"  

@app.route("/pharmacy_settings")
def pharmacy_settings():
    if 'pharmacy_id' not in session:
        return redirect("/pharmacy_login")
        
    pharmacy_id = session['pharmacy_id']
    
    try:
        local_cursor = db.cursor(dictionary=True)
        # 🌟 FIX: Changed pharmacy_name to name to match your MySQL structure!
        local_cursor.execute("SELECT name, location, phone FROM pharmacy WHERE pharmacy_id = %s", (pharmacy_id,))
        profile_data = local_cursor.fetchone()
        local_cursor.close()
        
        return render_template("pharmacy_settings.html", profile=profile_data)
    except Exception as e:
        print(f"Settings Load Error: {e}")
        return "Failed to load configuration settings."


@app.route("/save_pharmacy_settings", methods=["POST"])
def save_pharmacy_settings():
    if 'pharmacy_id' not in session:
        return redirect("/pharmacy_login")
        
    pharmacy_id = session['pharmacy_id']
    new_name = request.form.get("pharmacy_name").strip()
    new_location = request.form.get("location").strip()
    new_phone = request.form.get("phone").strip()
    
    try:
        local_cursor = db.cursor()
        # 🌟 FIX: Changed pharmacy_name = %s to name = %s here too!
        sql = """
            UPDATE pharmacy 
            SET name = %s, location = %s, phone = %s 
            WHERE pharmacy_id = %s
        """
        local_cursor.execute(sql, (new_name, new_location, new_phone, pharmacy_id))
        db.commit()
        local_cursor.close()
        
        # Update the session variable immediately so the header changes too!
        session['pharmacy_name'] = new_name
        
        return redirect("/pharmacy_dashboard")
    except Exception as e:
        print(f"Settings Save Error: {e}")
        return "Failed to update profile configurations."
if __name__=="__main__":
    app.run(debug=True)