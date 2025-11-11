import sys
import json
from ollama import chat
from ollama import ChatResponse


def get_response(prompt, model="llama3.1:8b"):
    response: ChatResponse = chat(
        model=model, 
        messages=[{'role': 'system', 'content': prompt}],
        format="json"
    )
    return response.message.content

def interpret_query(query):
    json_template={
        "Question":query,
        "Response":{
            "need_shelter_data":{
                "Description":"To answer this question, we need data about disaster shelter locations or services",
                "Value":"NULL"
            },
            "need_routing_data":{
                "Description":"To answer this question, we need directions or routing to a place, such as a disaster shelter.",
                "Value":"NULL"
            }
        }
    }
    
    prompt=f"""
    <role>
    Your job is to fill in a JSON template meticulously, matching the format EXACTLY, based on a question's required information.
    To do this, replace any "NULL" values with "True" or "False"
    Do not edit any other fields in the response.
    </role>
    <json_template>
    {json_template}
    </json_template>
    """
    
    response=json.loads(get_response(prompt).lower())
    need_shelter_data=False
    need_routing_data=False
    try:
        response=response["response"]
    except:
        print("no response key")
    try:
        need_shelter_data=response["need_shelter_data"]
        need_routing_data=response["need_routing_data"]
    except:
        print("no need_data keys")
    try:
        need_shelter_data=need_shelter_data["value"]
        need_routing_data=need_routing_data["value"]
        if type(need_shelter_data) is str:
            need_shelter_data=need_shelter_data=="true"
        if type(need_routing_data) is str:
            need_routing_data=need_routing_data=="true"
    except:
        print("no value key")
        
    return need_shelter_data, need_routing_data

def test():
    query="Where are the nearest disaster shelters to me?"
    if len(sys.argv)==2:
        query=sys.argv[1]
    
    need_shelter_data, need_routing_data = interpret_query(query)
    
    if not need_shelter_data or need_routing_data:
        print("Failure")
        print("Response:",response,"\n")
    else:
        print("Success\n")

if __name__=="__main__":
    test()