from pymongo import MongoClient

MONGO_URI = "mongodb://logging-db:27017"


client = MongoClient(MONGO_URI)

db = client["logging-db"]

logs_collection = db["application_logs"]
