from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "travel_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20), default="employee")

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(100))
    origin = db.Column(db.String(100))
    destination = db.Column(db.String(100))
    start_date = db.Column(db.String(100))
    end_date = db.Column(db.String(100))
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(50), default="pending")
    risks = db.relationship('RiskEvent', backref='trip', lazy=True)

    checkpoints = db.relationship('Checkpoint', backref='trip', lazy=True)

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

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        emp_id = request.form["employee_id"]
        password = generate_password_hash(request.form["password"])

        user = User(employee_id=emp_id, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        emp_id = request.form["employee_id"]
        password = request.form["password"]

        user = User.query.filter_by(employee_id=emp_id).first()

        if user and check_password_hash(user.password, password):
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

    trips = Trip.query.filter_by(employee_id=user_id).all()

    # Admin view (manager)
    if user.role == "manager":
        all_trips = Trip.query.all()
        pending_trips = Trip.query.filter_by(status="pending").all()

        return render_template(
            "dashboard_admin.html",
            user=user_id,
            trips=all_trips,
            pending=pending_trips
        )

    # Employee view
    return render_template(
        "dashboard.html",
        user=user_id,
        trips=trips
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

    if request.method == "POST":
        destination = request.form["destination"]

        flights, hotels = generate_itinerary(destination)

        new_trip = Trip(
            employee_id=session["user"],
            origin=request.form["origin"],
            destination=destination,
            start_date=request.form["start_date"],
            end_date=request.form["end_date"],
            purpose=request.form["purpose"],
            status="pending"
        )

        db.session.add(new_trip)
        db.session.commit()

        session["flights"] = flights
        session["hotels"] = hotels

        return redirect("/itinerary")

    return render_template("trip.html")

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

    message, suggestion = generate_risk_response(event_type, trip.destination)

    risk = RiskEvent(
        trip_id=trip_id,
        event_type=event_type,
        message=message,
        suggestion=suggestion,
        status="active"
    )

    db.session.add(risk)

    # 🔔 ADD THIS LINE (NOTIFICATION)
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
    trip = Trip.query.get(trip_id)
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
    trip = Trip.query.get(trip_id)
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

    notifs = Notification.query.filter_by(
        employee_id=session["user"]
    ).all()

    return render_template("notifications.html", notifs=notifs)



@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)