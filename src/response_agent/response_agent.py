import json
from ollama import chat
from ollama import ChatResponse
from src.orchestration.orchestration import main as run_orchestration

#gets response from LLM
def get_response(prompt, model="llama3.1:8b"):
	response: ChatResponse = chat(
		model=model, 
		messages=[
            {"role": "system", "content": "You are an emergency response summarization assistant."},
            {"role": "user", "content": prompt}
        ],
		options={"temperature":0.075}
	)
	return response.message.content.strip()

def generate_response(query, context):
    prompt = f"""
    You are a calm, friendly emergency response assistant.

    Start your response with a short, warm introduction (2–3 sentences) that:
    - Acknowledges the user's request
    - Explains that you checked nearby shelters based on their location
    - Reassures them that the information is meant to help them make a decision

    Example opening tone (do not copy exactly):
    "I looked up shelters near your location to help you find the safest options.
     Here are the closest places you can access right now."

    Then present the shelter list.

    User question:
    "{query}"
    
    You will be given this JSON structure:
    {{
    "query": "...",
    "user_location": {{ ... }},
    "shelters": [
        {{
        "name": "...",
        "address": "...",
        "city": "...",
        "state": "...",
        "zip": "...",
        "status": "...",
        "handicap_accessible": "...",
        "location": {{ "lat": ..., "lon": ... }},
        "straightline_distance_miles": ...,
        "route": {{ ... }}   # may be null
            }}
          ]
        }}


    Your job:
    - Summarize EACH shelter listed
    - If route information is present, include brief directions or travel details for that shelter
    - Output one shelter per line in plain text
    - DO NOT output JSON and DO NOT add or invent any information
    
    Full Context JSON:
    {json.dumps(context, indent=2)}
    """

    # Send prompt to LLM using the same get_response() pattern

    summary_text = get_response(prompt)

    return summary_text