from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS  # Import CORS
from bson import ObjectId  
from bson.errors import InvalidId 
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB connection string
connection_string = "mongodb+srv://robinxavierdev:Robin2000@cluster0.jmp8x.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(connection_string)

# Database and collection
db = client.notes
usercollection = db.userDetails
notescollection = db.notes  # New collection for storing notes

@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        # Get data from the payload
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({"error": "Missing required fields"}), 400

        # Check if email is already present in the database
        existing_user = usercollection.find_one({"email": email})
        if existing_user:
            return jsonify({"message": "User already exists"}), 409

        # Save the new user details with timestamps
        new_user = {
            "username": username,
            "email": email,
            "password": password,
            "created_on": datetime.utcnow().isoformat(),  # Add created_on timestamp
            "last_update": datetime.utcnow().isoformat(),  # Add last_update timestamp
        }
        usercollection.insert_one(new_user)
        return jsonify({"message": "User added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/login_user', methods=['POST'])
def login_user():
    try:
        # Get data from the payload
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400

        # Check if the user exists in the database
        user = usercollection.find_one({"email": email})
        if not user:
            return jsonify({"message": "User does not exist"}), 404

        # Validate the password
        if user["password"] != password:
            return jsonify({"message": "Invalid password"}), 401

        # If email and password are correct, return success response
        return jsonify({"message": "Login successful", "username": user["username"]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_user_details', methods=['GET'])
def get_user_details():
    try:
        # Fetch all documents from the collection
        user_details = list(usercollection.find({}, {"_id": 0}))  # Exclude the '_id' field
        return jsonify(user_details), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New API endpoint to add notes
@app.route('/add_note', methods=['POST'])
def add_note():
    try:
        # Get data from the payload
        data = request.json
        username = data.get('username')
        heading = data.get('heading')
        message = data.get('message')

        if not username or not heading or not message:
            return jsonify({"error": "Missing required fields"}), 400

        # Save the new note to the database with timestamps
        new_note = {
            "username": username,
            "heading": heading,
            "message": message,
            "created_on": datetime.utcnow().isoformat(),  # Add created_on timestamp
            "last_update": datetime.utcnow().isoformat(),  # Add last_update timestamp
        }
        notescollection.insert_one(new_note)
        return jsonify({"message": "Note added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# New API endpoint to get all notes
@app.route('/get_notes', methods=['GET'])
def get_notes():
    try:
        # Get the username from the query parameters
        username = request.args.get('username')
        if not username:
            return jsonify({"error": "Username is required"}), 400

        # Fetch notes for the specific user and sort by created_on in ascending order
        notes = list(notescollection.find({"username": username}).sort("created_on", 1))
        
        # Convert ObjectId to string
        for note in notes:
            note["_id"] = str(note["_id"])  # Convert '_id' to string
        
        return jsonify(notes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@app.route('/update_note/<note_id>', methods=['PUT'])
def update_note(note_id):
    try:
        print("Received note_id:", note_id)  # Log the note_id
        # Validate note_id
        try:
            note_id_obj = ObjectId(note_id)  # Convert note_id to ObjectId
        except InvalidId:
            return jsonify({"error": "Invalid note ID format"}), 400

        # Get data from the payload
        data = request.json
        new_message = data.get('message')

        if not new_message:
            return jsonify({"error": "Message is required"}), 400

        # Update the note in the database
        result = notescollection.update_one(
            {"_id": note_id_obj},  # Use the validated ObjectId
            {"$set": {"message": new_message, "last_update": datetime.utcnow().isoformat()}}
        )

        if result.modified_count == 1:
            return jsonify({"message": "Note updated successfully"}), 200
        else:
            return jsonify({"error": "Note not found or not updated"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/delete_note/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    try:
        # Delete the note from the database
        result = notescollection.delete_one({"_id": ObjectId(note_id)})

        if result.deleted_count == 1:
            return jsonify({"message": "Note deleted successfully"}), 200
        else:
            return jsonify({"error": "Note not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)