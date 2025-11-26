import json
from ollama import chat
from ollama import ChatResponse
from src.orchestration.orchestration import main as run_orchestration

#gets response from LLM
def get_response(prompt, model="llama3.1:8b"):
	response: ChatResponse = chat(
		model=model, 
		messages=[{'role': 'system', 'content': prompt}],
		format="json",
		options={"temperature":0.075}
	)
	return response.message.content

def generate_response(query, context):
    prompt = f"""
    You are part of an emergency response assistant. 

    
    You will be given this JSON structure:
    {{
    "query": "...",
    "shelter_results": {{ ... }},
    "routing_results": {{ ... }}
    }}

    Your job:
    - Read the JSON exactly as provided
    - Identify the THREE closest shelters based on straightline_distance_miles
    - For each shelter, summarize important information (name, address, distance, etc.)

    Only use the fields present in the JSON.
    Do not output JSON.
    DO not hallucinate or invent data.
    
    Full Context JSON:
    {json.dumps(context, indent=2)}
    """

    # Send prompt to LLM using the same get_response() pattern
    summary_text = get_response(prompt)

    return summary_text