from flask import Flask, request, jsonify
from pymongo import MongoClient
from vertexai.preview.language_models import TextGenerationModel
from google.auth import load_credentials_from_file
import os
import vertexai
from bson.objectid import ObjectId
from constants import CONTEXT

# Load credentials and initialize model
key_file_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
credentials, project_id = load_credentials_from_file(key_file_path)
vertexai.init(project=project_id, location="us-central1", credentials=credentials)
model = TextGenerationModel.from_pretrained("text-bison@001")

# MongoDB client
mongo_connection = os.getenv("MONGODB_URL")

client = MongoClient(mongo_connection)
db = client.rajesh_ai
collection = db.messages

app = Flask(__name__)


@app.route("/conversations", methods=["POST"])
def start_conversation():
    messages = [
        {
            "role": "assistant",
            "content": "Hi welcome, I am Rajesh, you can ask me anything about my skills, projects, portfolio or anything else.",
        }
    ]

    conversation_id = ObjectId()
    collection.insert_one({"_id": conversation_id, "messages": messages})

    return jsonify({"conversation_id": str(conversation_id), "messages": messages})

@app.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    # Convert string to ObjectId
    conversation_id = ObjectId(conversation_id)

    # Find the conversation
    conversation = collection.find_one({"_id": conversation_id})

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    # Return the messages
    return jsonify({"messages": conversation["messages"]})

@app.route("/continue-conversation", methods=["POST"])
def continue_conversation():
    data = request.get_json(force=True)
    conversation_id = ObjectId(data["conversation_id"])
    user_message = data["message"]

    conversation = collection.find_one({"_id": conversation_id})

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    conversation["messages"].append({"role": "user", "content": user_message})

    # Generate the model input from conversation history
    model_input = "".join(
        ("input: " if message["role"] == "user" else "output: ")
        + message["content"]
        + "\n"
        for message in conversation["messages"]
    )
    print(CONTEXT + model_input + "output:")
    # Generate the model response
    response = model.predict(
        CONTEXT + model_input + "output:",
        temperature=1,
        max_output_tokens=256,
        top_k=40,
        top_p=0.8,
    )
    message = {"role": "assistant", "content": response.text};

    # Add the assistant's response to the conversation
    conversation["messages"].append(message)

    # Save the updated conversation back to MongoDB
    collection.replace_one({"_id": conversation_id}, conversation)

    # Send the model response back to the client
    return jsonify({"message": message})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
