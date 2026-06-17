
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travelmate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = os.environ.get("SECRET_KEY", "travel_secret_key")

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.String(50), unique=True)

    name = db.Column(db.String(100))

    email = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(200), nullable=True)

    role = db.Column(db.String(20))

    activated = db.Column(db.Boolean, default=False)
    

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.String(50))

    origin = db.Column(db.String(100))
    destination = db.Column(db.String(100))

    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))

    purpose = db.Column(db.String(200))

    status = db.Column(db.String(20), default="pending")

class Checkpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    type = db.Column(db.String(100))   # flight_departure, arrival, hotel_checkin
    timestamp = db.Column(db.String(100))
    status = db.Column(db.String(50))  # completed / pending

class RiskEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)

    event_type = db.Column(db.String(100))   # flight_delay, missed_flight, hotel_cancel
    message = db.Column(db.String(300))
    suggestion = db.Column(db.String(300))

    status = db.Column(db.String(50), default="active")

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(100))
    message = db.Column(db.String(300))
    type = db.Column(db.String(50))  # approval / risk / compliance
    is_read = db.Column(db.Boolean, default=False)



def generate_itinerary(destination):
    flights = [
        f"Flight Option 1 → Economy to {destination} (10:00 AM)",
        f"Flight Option 2 → Business to {destination} (6:00 PM)",
        f"Flight Option 3 → Budget carrier to {destination} (2:00 PM)"
    ]

    hotels = [
        f"Hotel Option 1 → {destination} Grand Hotel (4★)",
        f"Hotel Option 2 → City Center Inn (3★)",
        f"Hotel Option 3 → Budget Stay {destination}"
    ]

    return flights, hotels

def generate_risk_response(event_type, destination):
    if event_type == "flight_delay":
        return (
            "Flight is delayed",
            "Check alternate flights or reschedule connection"
        )

    elif event_type == "missed_flight":
        return (
            "Flight missed",
            f"Suggest rebooking to next available flight to {destination}"
        )

    elif event_type == "hotel_cancel":
        return (
            "Hotel booking cancelled",
            f"Suggest alternative hotels in {destination}"
        )

    else:
        return ("Unknown risk", "Manual intervention required")

def create_notification(employee_id, message, type):
    notif = Notification(
        employee_id=employee_id,
        message=message,
        type=type
    )
    db.session.add(notif)
    db.session.commit()

@app.route("/")
def home():
    return redirect("/login")

@app.route("/activate", methods=["GET", "POST"])
def activate():

    if request.method == "POST":

        emp_id = request.form["employee_id"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            return "Passwords do not match"

        user = User.query.filter_by(employee_id=emp_id).first()

        if not user:
            return "Employee ID not found"

        if user.activated:
            return "Account already activated"

        user.password = generate_password_hash(password)
        user.activated = True

        db.session.commit()

        return redirect("/login")

    return render_template("activate.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        emp_id = request.form["employee_id"]
        password = request.form["password"]

        user = User.query.filter_by(employee_id=emp_id).first()

        if not user:
            return "Employee ID not found"

        if not user.activated:
            return redirect("/activate")

        if not user.password:
            return "Please activate your account first"

        if check_password_hash(user.password, password):
            session["user"] = emp_id
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user_id = session["user"]
    user = User.query.filter_by(employee_id=user_id).first()

    if not user:
        return redirect("/login")

    # -------------------------
    # EMPLOYEE VIEW
    # -------------------------
    if user.role != "manager":

        

        return render_template(
            "dashboard.html",
            user=user.name.split()[0])

    # -------------------------
    # MANAGER VIEW
    # -------------------------
    all_trips = Trip.query.all()

    total = len(all_trips)
    pending = len([t for t in all_trips if t.status == "pending"])
    approved = len([t for t in all_trips if t.status == "approved"])
    rejected = len([t for t in all_trips if t.status == "rejected"])

    return render_template(
        "dashboard_admin.html",
        user=user_id,
        trips=all_trips,
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected
    )

@app.route("/copilot", methods=["GET", "POST"])
def copilot():
    if "user" not in session:
        return redirect("/login")

    response = ""

    if request.method == "POST":
        query = request.form["query"].lower()

        # --- SIMPLE RULE-BASED AI LOGIC ---
        if "london" in query:
            response = "Suggested: 3-day London business trip with central hotel + evening flight options."

        elif "visa" in query:
            response = "Visa rules depend on destination. Check compliance module for details."

        elif "hotel" in query:
            response = "Recommended: 3-4 star hotels near city center for corporate stays."

        elif "plan" in query:
            response = "I can help plan your trip. Please provide destination and dates."

        else:
            response = "I am your travel assistant. Try asking about flights, hotels, visas, or trip planning."

    return render_template("copilot.html", response=response)

@app.route("/trip", methods=["GET", "POST"])
def trip():

    if "user" not in session:
        return redirect("/login")

    user_id = session["user"]

    if request.method == "POST":

        origin = request.form["origin"]
        destination = request.form["destination"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        purpose = request.form["purpose"]

        new_trip = Trip(
            employee_id=user_id,
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            purpose=purpose,
            status="pending"
        )

        db.session.add(new_trip)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("create_trip.html")

@app.route("/itinerary")
def itinerary():
    if "user" not in session:
        return redirect("/login")

    flights = session.get("flights", [])
    hotels = session.get("hotels", [])

    return render_template("itinerary.html", flights=flights, hotels=hotels)

@app.route("/approvals")
def approvals():
    if "user" not in session:
        return redirect("/login")

    user = User.query.filter_by(employee_id=session["user"]).first()

    if user.role != "manager":
        return "Access denied"

    trips = Trip.query.all()

    return render_template("approvals.html", trips=trips)


@app.route("/checkpoint/<int:trip_id>/<string:type>")
def add_checkpoint(trip_id, type):
    if "user" not in session:
        return redirect("/login")

    import datetime

    checkpoint = Checkpoint(
        trip_id=trip_id,
        type=type,
        timestamp=str(datetime.datetime.now()),
        status="completed"
    )

    db.session.add(checkpoint)
    db.session.commit()

    return redirect("/dashboard")

@app.route("/risk/<int:trip_id>/<string:event_type>")
def risk_event(trip_id, event_type):
    if "user" not in session:
        return redirect("/login")

    trip = Trip.query.get(trip_id)

    # ✅ SAFE CHECK (CRITICAL)
    if not trip:
        return "Trip not found", 404

    # ✅ SAFE RESPONSE GENERATION
    message, suggestion = generate_risk_response(event_type, trip.destination)

    risk = RiskEvent(
        trip_id=trip_id,
        event_type=event_type,
        message=message,
        suggestion=suggestion,
        status="active"
    )

    db.session.add(risk)

    # 🔔 NOTIFICATION SAFETY CHECK
    if trip.employee_id:
        create_notification(
            trip.employee_id,
            f"Risk Alert: {message}",
            "risk"
        )

    db.session.commit()

    return redirect("/dashboard")

@app.route("/simulate-risk/<int:trip_id>")
def simulate_risk(trip_id):
    return redirect(f"/risk/{trip_id}/missed_flight")

@app.route("/approve/<int:trip_id>")
def approve(trip_id):
    if "user" not in session:
        return redirect("/login")

    trip = Trip.query.get(trip_id)

    if not trip:
        return "Trip not found", 404

    trip.status = "approved"

    create_notification(
        trip.employee_id,
        "Your trip has been APPROVED",
        "approval"
    )

    db.session.commit()
    return redirect("/approvals")

@app.route("/reject/<int:trip_id>")
def reject(trip_id):
    if "user" not in session:
        return redirect("/login")

    trip = Trip.query.get(trip_id)

    if not trip:
        return "Trip not found", 404

    trip.status = "rejected"

    create_notification(
        trip.employee_id,
        "Your trip has been REJECTED",
        "approval"
    )

    db.session.commit()
    return redirect("/approvals")

@app.route("/notifications")
def notifications():
    if "user" not in session:
        return redirect("/login")

    user_id = session.get("user")

    if not user_id:
        return redirect("/login")

    notifs = Notification.query.filter_by(employee_id=user_id).all()

    return render_template("notifications.html", notifs=notifs)



@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

with app.app_context():
    db.create_all()

    employees = [
        ("EMP1001","John Smith","john.smith@company.com","employee"),
        ("EMP1002","Sarah Johnson","sarah.johnson@company.com","employee"),
        ("EMP1003","Michael Brown","michael.brown@company.com","employee"),
        ("EMP1004","Emily Davis","emily.davis@company.com","employee"),
        ("EMP1005","David Wilson","david.wilson@company.com","employee"),
        ("EMP1006","Jessica Moore","jessica.moore@company.com","employee"),
        ("EMP1007","Daniel Taylor","daniel.taylor@company.com","employee"),
        ("EMP1008","Olivia Martinez","olivia.martinez@company.com","employee"),
        ("EMP1009","James Anderson","james.anderson@company.com","employee"),
        ("EMP1010","Sophia Thomas","sophia.thomas@company.com","manager")
    ]

    for emp_id, name, email, role in employees:
        existing = User.query.filter_by(employee_id=emp_id).first()

        if not existing:
            db.session.add(
                User(
                    employee_id=emp_id,
                    name=name,
                    email=email,
                    password=None,
                    role=role,
                    activated=False
                )
            )

    db.session.commit()

if __name__ == "__main__":
    app.run()
