from collections import defaultdict
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash , check_password_hash
import os
from config.db import dbs, expense_db
from models.model import User
from dotenv import load_dotenv
from bson.objectid import ObjectId
import matplotlib.pyplot as plt
import io
import base64

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key_for_dev")

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    user_data = dbs.find_one({"_id" : ObjectId(user_id)})
    if user_data:
        return User(id = str(user_data["_id"]), name = user_data["UserName"],email = user_data["Email"],  password=user_data["Password"])
    return None


@app.route("/signup",  methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get("name")
        mail = request.form.get("email")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        if not name or not mail or not password:
            flash("All fields are required.", category="error")
        elif dbs.find_one({"Email":mail}):
            flash("Email is in use", category="error")
            return redirect(url_for("signup"))    
        elif dbs.find_one({"UserName":name}):
            flash("Username is in use", category="error")
            return redirect(url_for("signup"))
        elif len(mail) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(name)<2:
            flash('First name must be at least 2 characters.', category='error')
        elif len(password)<7:
            flash("Password must be at least 7 characters.", category='error')
        else:
            user = {
            "UserName": name,
            "Email": mail,
            "Password": hashed_password
            }
            dbs.insert_one(user)      
            flash("Account created successfully", category="success")
            return redirect(url_for('login'))
    return render_template(template_name_or_list="signup.html")

@app.route("/login",  methods=['GET', 'POST'])
def login():
    if request.method=="POST":
        name = request.form.get("name")
        password = request.form.get("password")
        user = dbs.find_one({"UserName":name})

        if user and check_password_hash(user["Password"], password):
            login_user(User(id = str(user["_id"]), name = user["UserName"],email = user["Email"],  password=user["Password"]))
            flash("Login successful", category="success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials", category="error")
        
    return render_template(template_name_or_list="login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", category="success")
    return redirect(url_for("login"))

@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    if request.method == "POST":
        category = request.form.get("category")
        amount = request.form.get("amount")
        date = request.form.get("date")
        if not category or not amount or not date:
            flash("All fields are required.", category="error")
        else:
            expense = {
                "category": category,
                "amount": amount,
                "date": date,
                "UserId": ObjectId(current_user.id)
            }
            expense_db.insert_one(expense)
            flash("Expense added successfully", category="success")
    expenses = list(expense_db.find({"UserId": current_user.id}))
    return render_template(template_name_or_list="home.html", tasks=expenses )

@app.route("/view_expense", methods=['GET', 'POST'])
@login_required
def view_expense():
    expenses = list(expense_db.find({"UserId": ObjectId(current_user.id)}))
    print("Expenses:", expenses)  #
    expense_list = [
        {
            "id": str(expense["_id"]),
            "Category": expense["category"],
            "Amount": float(expense["amount"]),
            "Date": expense["date"]
        }
        for expense in expenses
    ]
    print("Expense List:", expense_list) 
    category_totals = defaultdict(float)
    for expense in expenses:
        category_totals[expense["category"]] += float(expense["amount"])
    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    print("Category Totals:", category_totals) 
    bar_chart_data = ""
    if categories and amounts:
        plt.figure(figsize=(8, 6))
        plt.bar(categories, amounts, color='skyblue')
        plt.title("Expense Breakdown by Category")
        plt.xlabel("Categories")
        plt.ylabel("Amount")
        plt.tight_layout()
        bar_chart = io.BytesIO()
        plt.savefig(bar_chart, format="png")
        plt.close()
        bar_chart.seek(0)
        bar_chart_data = base64.b64encode(bar_chart.getvalue()).decode()
        print("Bar Chart Generated")  # Debug: Confirm chart generation
    else:
        print("No data for Bar Chart")  # Debug: No data for chart

    # Generate Pie Chart
    pie_chart_data = ""
    if categories and amounts:
        plt.figure(figsize=(6, 6))
        plt.pie(amounts, labels=categories, autopct="%1.1f%%", startangle=140)
        plt.title("Expense Distribution by Category")
        plt.tight_layout()
        pie_chart = io.BytesIO()
        plt.savefig(pie_chart, format="png")
        plt.close()
        pie_chart.seek(0)
        pie_chart_data = base64.b64encode(pie_chart.getvalue()).decode()
        print("Pie Chart Generated")  # Debug: Confirm chart generation
    else:
        print("No data for Pie Chart")  # Debug: No data for chart

    return render_template(
        "home.html",
        task_list=expense_list,
        bar_chart=bar_chart_data,
        pie_chart=pie_chart_data,
    )


@app.route('/delete_task/<expense_id>', methods=["GET",'POST'])
@login_required
def delete_task(expense_id):
    result = expense_db.delete_one({"_id": ObjectId(expense_id), "UserId": ObjectId(current_user.id)})
    if result.deleted_count == 0:
        flash("Expense not found or unauthorized access.", "danger")
    else:
        flash("Expense deleted successfully.", "success")
    return redirect(url_for('home'))

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__=="__main__":
    app.run(debug=True, port=5000)