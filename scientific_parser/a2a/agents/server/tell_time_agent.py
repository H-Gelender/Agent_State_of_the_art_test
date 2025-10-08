from flask import Flask, request, jsonify

from datetime import datetime

app = Flask(__name__)

@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card():

    return jsonify({
        "name": "TellTimeAgent",
        "description": "An agent that tells the current time.",
        "url": "http://localhost:5000",
        "version": "1.0.0",
        "capabilities": {"tell_time": False,
                         "pushNotifications": False},
        "type": "time"
    })

@app.route("/task/send", methods=["POST"])
def handle_task():
    try:
        task = request.json
        task_id = task.get("id")
        user_message = task["message"]["parts"][0]["text"]

    except (KeyError,IndexError,TypeError) as e:
        return jsonify({"error": "Invalid task format", "details": str(e)}), 400

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reply_text = f"The current time is {current_time}."
    
    return jsonify({
        "id": task_id,
        "status": {"state":"completed"},
        "messages":[
            task["message"],  # Echo the original message for context
            {
                "role": "agent",
                "parts": [{"text": reply_text}]
            }
        ]
    })

if __name__ == "__main__":
    app.run(port=5000)