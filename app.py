from flask import Flask, render_template, request,redirect
import sqlite3
from datetime import datetime, timedelta
app = Flask(__name__)
def ai_eligibility(last_date, spo2, pulse):

    try:
        days = (datetime.now() - datetime.strptime(last_date, "%Y-%m-%d")).days
    except:
        return "⚠️ Unknown"

    if days < 90:
        return "🔴 Not Eligible (Cooling Period)"

    if spo2 < 95 or pulse > 100:
        return "🟡 Risky Health Condition"

    return "🟢 Safe to Donate"

@app.route("/")
def home():

    conn = sqlite3.connect("bloodbridge.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    donor_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM blood_requests")
    request_count = cursor.fetchone()[0]

    conn.close()

    hospital_count = 5

    return render_template(
        "home.html",
        donor_count=donor_count,
        request_count=request_count,
        hospital_count=hospital_count
    )


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        blood_group = request.form["blood_group"]
        city = request.form["city"]
        state = request.form["state"]
        availability = request.form["availability"]
        last_donation_date = request.form["last_donation_date"]
        gender = request.form["gender"]
        pulse = request.form["pulse"]
        spo2 = request.form["spo2"]
        bp = request.form["bp"]

        conn = sqlite3.connect("bloodbridge.db")
        cursor = conn.cursor()

        cursor.execute("""
       INSERT INTO users
(name, email,password, phone, blood_group, city, state, availability, last_donation_date, gender, contact_status, pulse, spo2, bp)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
(name, email, password, phone, blood_group, city, state, availability,
 last_donation_date, gender, "Available", pulse, spo2, bp)
)

        conn.commit()
        conn.close()

        return "Registration Successful"

    return render_template("register.html")

@app.route("/donors")
def donors():

    conn = sqlite3.connect("bloodbridge.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    conn.close()

    scored_donors = []

    for d in rows:

        reach_index = 0
        risk = "🟢 Low"

        if d[8] == "Yes":
            reach_index += 50

        reach_index += 20

        if d[6]:
            reach_index += 10

        if d[7]:
            reach_index += 10

        try:
            spo2 = int(d[13])
            pulse = int(d[12])

            if spo2 < 95 or pulse > 100:
                risk = "🔴 High"
            elif spo2 < 97:
                risk = "🟡 Medium"

        except:
            pass

        # AI eligibility (safe add)
        eligibility = ai_eligibility(d[9], int(d[13]), int(d[12]))

        scored_donors.append((d, reach_index, risk, eligibility))

    scored_donors.sort(key=lambda x: x[1], reverse=True)

    return render_template("donors.html", donors=scored_donors)

    


    
    
@app.route("/search", methods=["GET", "POST"])
def search():

    if request.method == "POST":

        blood_group = request.form["blood_group"]
        city = request.form["city"]

        conn = sqlite3.connect("bloodbridge.db")
        cursor = conn.cursor()

        cursor.execute(
    "SELECT * FROM users WHERE blood_group=? AND availability='Yes'",
    (blood_group,)
)
        

        donors = cursor.fetchall()

        conn.close()

        return render_template("donors.html", donors=donors)

    return render_template("search.html")
@app.route("/request", methods=["GET", "POST"])
def blood_request():

    if request.method == "POST":

        patient_name = request.form["patient_name"]
        blood_group = request.form["blood_group"]
        city = request.form["city"]

        conn = sqlite3.connect("bloodbridge.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO blood_requests
            (patient_name, blood_group, city)
            VALUES (?, ?, ?)
            """,
            (patient_name, blood_group, city)
        )

        conn.commit()
        conn.close()
        return redirect(f"/match/{blood_group}/{city}")

    return render_template("request.html")
@app.route("/eligibility", methods=["GET", "POST"])
def eligibility():

    result = ""

    if request.method == "POST":

        last_date = request.form["last_donation_date"]
        donation_date = datetime.strptime(last_date, "%Y-%m-%d")

        days = (datetime.now() - donation_date).days

        if days >= 90:
            result = "Eligible to Donate"
        else:
            result = f"Not Eligible Yet. Wait {90-days} more days."

    return render_template("eligibility.html", result=result)
@app.route("/hospitals")
def hospitals():
    return render_template("hospitals.html")
@app.route("/care")
def care():
    return render_template("care.html")
@app.route("/compatibility", methods=["GET", "POST"])
def compatibility():

    result = ""

    if request.method == "POST":

        blood_type = request.form["blood_type"]

        compatibility_map = {
            "O-": "Can donate to everyone",
            "O+": "O+, A+, B+, AB+",
            "A-": "A-, A+, AB-, AB+",
            "A+": "A+, AB+",
            "B-": "B-, B+, AB-, AB+",
            "B+": "B+, AB+",
            "AB-": "AB-, AB+",
            "AB+": "AB+ only (universal receiver)"
        }

        result = compatibility_map.get(blood_type, "Invalid blood group")

    return render_template("compatibility.html", result=result)
@app.route("/requests")
def view_requests():

    conn = sqlite3.connect("bloodbridge.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM blood_requests")
    requests = cursor.fetchall()

    conn.close()

    return render_template("requests.html", requests=requests)
@app.route("/match/<blood_group>/<city>")
def match_donors(blood_group, city):

    conn = sqlite3.connect("bloodbridge.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE blood_group=? AND availability='Yes'",
        (blood_group,)
    )

    donors = cursor.fetchall()

    conn.close()

    if len(donors) == 0:
        return render_template(
            "emergency.html",
            message="🚨 No donors found",
            city=city
        )

    return render_template(
        "matched.html",
        donors=donors,
        blood_group=blood_group,
        city=city
    )

        

@app.route("/delete/<int:id>")
def delete_donor(id):

    conn = sqlite3.connect("bloodbridge.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/donors")
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_donor(id):

    conn = sqlite3.connect("bloodbridge.db")
    cursor = conn.cursor()

    if request.method == "POST":

        city = request.form["city"]
        phone = request.form["phone"]
        availability = request.form["availability"]

        cursor.execute(
            "UPDATE users SET city=?, phone=?, availability=? WHERE id=?",
            (city, phone, availability, id)
        )

        conn.commit()
        conn.close()

        return redirect("/donors")

    cursor.execute("SELECT * FROM users WHERE id=?", (id,))
    donor = cursor.fetchone()

    conn.close()

    return render_template("edit.html", donor=donor)
@app.route("/wellness/<date>", methods=["GET","POST"])
def wellness(date):

    donation_date = datetime.strptime(date, "%Y-%m-%d")
    next_date = donation_date + timedelta(days=90)

    advice = ""
    score = ""

    if request.method == "POST":

        sleep = int(request.form["sleep"])
        water = float(request.form["water"])
        energy = int(request.form["energy"])
        dizzy = request.form["dizzy"]

        score = 50

        if sleep >= 7:
            score += 20

        if water >= 2:
            score += 20

        if energy >= 7:
            score += 10

        if dizzy == "Yes":
            score -= 30

        if score >= 80:
            advice = f"🟢 Excellent Recovery Score: {score}/100"
        elif score >= 60:
            advice = f"🟡 Recovery Score: {score}/100"
        else:
            advice = f"🔴 Recovery Score: {score}/100 - Focus on rest and hydration"

    return render_template(
        "wellness.html",
        next_date=f"Next Eligible Donation: {next_date.date()}",
        advice=advice,
        score=f"Recovery Score: {score}/100" if score != "" else ""
    )
@app.route("/contact/<int:id>")
def contact_donor(id):

    conn = sqlite3.connect("bloodbridge.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id=?", (id,))
    donor = cursor.fetchone()

    conn.close()

    return render_template("contact.html", donor=donor)
@app.route("/report")
def report():

    conn = sqlite3.connect("bloodbridge.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    donors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM blood_requests")
    requests = cursor.fetchone()[0]

    conn.close()

    return render_template("report.html",
        donors=donors,
        requests=requests
    )

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)