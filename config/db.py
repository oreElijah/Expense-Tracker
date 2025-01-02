import pymongo
import os

client = pymongo.MongoClient(os.environ.get("MONGODB_URL"))


db = client["expense-tracker"]

dbs = db["users"]
expense_db = db["expenses"]
