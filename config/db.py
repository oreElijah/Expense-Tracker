import pymongo
import os

client = pymongo.MongoClient(os.environ.get("MONGODB_URL"))


db = client["expense-tracker"]

dbs = db["users"]
expense_db = db["expenses"]

data = {
    "UserName": "admin",
    "Email": "ooooo",
    "Password": "admin"
}

expense_data = {
    "category": "Food",
    "Amount": 300,
    "Date": "2021-08-12"
}

dbs.insert_one(data)