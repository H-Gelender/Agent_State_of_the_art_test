import requests

import uuid # each A2A task needs to have a unique id

# Discover the agent's capabilities
base_url = "http://localhost:5000"

#Use http GET to fetch the agent's card from the well-known discovery endpoint
response = requests.get(f"{base_url}/.well-known/agent.json")

if response.status_code != 200:
    raise Exception(f"Failed to fetch agent card: {response.status_code} {response.text}")
###################################
######### STEP2: Prepare task######
###################################

task_id = str(uuid.uuid4())  # Generate a unique task ID
user_message = "What time is it?"

# According to A2A protocol, we need to include the id and a message with a list of parts.
# Prepare the task payload
task_payload = {
    "id": task_id,
    "message": {
        "role": "user",
        "parts": [
            {
                "text": user_message
            }
        ]
    }
}

####################################
######### STEP 3: Send task ########
####################################

response = requests.post(f"{base_url}/task/send", json=task_payload)

if response.status_code != 200:
    raise Exception(f"Failed to send task: {response.status_code} {response.text}")


###########################################
######### STEP 4: display response ########
###########################################

messages = response.json().get("messages", [])

if messages:
    final_reply = messages[-1]["parts"][0]["text"]
    print(f"Agent replied: {final_reply}")

else:
    print("No messages received from the agent.")