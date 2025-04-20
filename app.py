from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "tolotro_secret"

# File paths
REGISTRATION_FILE = "registrations.csv"
RESERVATION_FILE = "reservations.csv"
VOTES_FILE = "votes.csv"

ROLES = [
    "Toastmaster", "Speaker 1", "Speaker 2", "Evaluator 1", "Evaluator 2",
    "Table Topics Evaluator", "Table Topics Master", "Timer", "Ah Counter",
    "Grammarian", "General Evaluator"
]
VOTE_CATEGORIES = ["Best Speaker", "Best Evaluator", "Best Impromptu Speaker"]

def load_csv(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        return pd.DataFrame(columns=columns)

def save_csv(df, file):
    df.to_csv(file, index=False)

@app.route("/", methods=["GET", "POST"])
def index():
    registrations = load_csv(REGISTRATION_FILE, ["Name", "Time"])
    reservations = load_csv(RESERVATION_FILE, ["Role", "User"])
    votes = load_csv(VOTES_FILE, ["Category", "Winner"])

    # Initialize reservations if empty
    if reservations.empty:
        reservations = pd.DataFrame({"Role": ROLES, "User": [None]*len(ROLES)})
        save_csv(reservations, RESERVATION_FILE)

    # Initialize votes if empty
    if votes.empty:
        votes = pd.DataFrame({"Category": VOTE_CATEGORIES, "Winner": [None]*len(VOTE_CATEGORIES)})
        save_csv(votes, VOTES_FILE)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "register":
            name = request.form.get("register_name", "").strip()
            if name and name not in registrations["Name"].values:
                new_row = pd.DataFrame([[name, datetime.now().isoformat()]], columns=["Name", "Time"])
                registrations = pd.concat([registrations, new_row], ignore_index=True)
                save_csv(registrations, REGISTRATION_FILE)
                flash(f"{name} registered!", "success")
            elif name in registrations["Name"].values:
                flash("You have already registered.", "warning")
            else:
                flash("Please enter a valid name.", "danger")

        elif action == "reserve":
            user = request.form.get("user")
            role = request.form.get("role")
            idx = reservations[reservations["Role"] == role].index
            if user and len(idx) == 1 and pd.isna(reservations.at[idx[0], "User"]):
                reservations.at[idx[0], "User"] = user
                save_csv(reservations, RESERVATION_FILE)
                flash(f"Reserved {role} for {user}.", "success")
            else:
                flash("Role already reserved or invalid selection.", "danger")

        elif action == "cancel":
            user = request.form.get("user")
            cancel_role = request.form.get("cancel_role")
            idx = reservations[(reservations["Role"] == cancel_role) & (reservations["User"] == user)].index
            if user and len(idx) == 1:
                reservations.at[idx[0], "User"] = None
                save_csv(reservations, RESERVATION_FILE)
                flash(f"Reservation for {cancel_role} canceled.", "success")
            else:
                flash("No reservation found to cancel.", "warning")

        elif action == "vote":
            vote_category = request.form.get("vote_category")
            vote_user = request.form.get("vote_user")
            idx = votes[votes["Category"] == vote_category].index
            if vote_user and len(idx) == 1:
                votes.at[idx[0], "Winner"] = vote_user
                save_csv(votes, VOTES_FILE)
                flash(f"Vote for {vote_user} in {vote_category} submitted.", "success")
            else:
                flash("Please select a user to vote for.", "danger")

        return redirect(url_for("index"))

    # For GET requests, reload data
    registrations = load_csv(REGISTRATION_FILE, ["Name", "Time"])
    reservations = load_csv(RESERVATION_FILE, ["Role", "User"])
    votes = load_csv(VOTES_FILE, ["Category", "Winner"])

    users = registrations["Name"].tolist()
    user_roles = {}
    for user in users:
        user_roles[user] = reservations[reservations["User"] == user]["Role"].tolist()

    return render_template(
        "index.html",
        registrations=registrations,
        reservations=reservations,
        votes=votes,
        roles=ROLES,
        vote_categories=VOTE_CATEGORIES,
        users=users,
        user_roles=user_roles
    )

if __name__ == "__main__":
    app.run(debug=True)