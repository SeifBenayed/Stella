from pymongo import MongoClient
from dotenv import load_dotenv
import os
# Load environment variables
load_dotenv()

client = MongoClient(os.environ["mongo_db_uri"])  # defaults to port 27017
db = client['stella_main']


def persona(persona_id):

    collection = db['personas']
    return collection.find_one({"_id": persona_id})


def template(template_id):
    collection = db['templates']
    return collection.find_one({"_id": template_id})