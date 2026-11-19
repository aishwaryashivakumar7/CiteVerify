import os
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables from .env
load_dotenv()

# Get MongoDB connection details
MONGODB_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "citeverify")

# Connect to MongoDB
client = MongoClient(MONGODB_URI)

# Select CiteVerify database
db = client[DATABASE_NAME]

# Create collections
documents_collection = db["documents"]
papers_collection = db["papers"]
verification_collection = db["verification_results"]


# Test database connection
def test_connection():
    try:
        client.admin.command("ping")
        print("MongoDB connected successfully!")

    except Exception as error:
        print("MongoDB connection failed:", error)

def save_paper(paper):
    try:
        doi = paper.get("doi")

        if not doi:
            print("Cannot save paper: DOI is missing.")
            return

        papers_collection.update_one(
            {"doi": doi},
            {"$set": paper},
            upsert=True
        )

        print("Research paper saved successfully!")

    except Exception as error:
        print("Error saving paper:", error)
def get_saved_papers():
    try:
        papers = list(papers_collection.find({}, {"_id": 0}))
        return papers

    except Exception as error:
        print("Error retrieving papers:", error)
        return []
def save_document(document):
    try:
        result = documents_collection.insert_one(document)
        print("Document saved successfully!")
        return str(result.inserted_id)

    except Exception as error:
        print("Error saving document:", error)
        return None
def get_saved_documents():
    try:
        documents = list(documents_collection.find({}))

        for document in documents:
            document["_id"] = str(document["_id"])

        return documents

    except Exception as error:
        print("Error retrieving documents:", error)
        return []
def get_document_by_id(document_id):
    try:
        document = documents_collection.find_one(
            {"_id": ObjectId(document_id)}
        )

        if document:
            document["_id"] = str(document["_id"])
            return document

        return None

    except Exception as error:
        print("Error retrieving document:", error)
        return None
        
def update_document(document_id, update_data):
    try:
        result = documents_collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    except Exception as error:
        print("Error updating document:", error)
        return False