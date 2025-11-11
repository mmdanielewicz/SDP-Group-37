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
            "related_question":{
                "Description":"Question is related to natural disasters, shelters, or emergencies.",
                "Value":"NULL"
            },
            "need_shelter_data":{
                "Description":"To answer this question, we need data about disaster shelter locations or services.",
                "Value":"NULL"
            },
            "need_routing_data":{
                "Description":"The query specifies a location and asks for directions or routing to it.",
                "Value":"NULL"
            }
        }
    }
    
    #If the question is unrelated to natural disasters, shelters, or emergencies, all "NULL" values should be changed to "False".
    
    prompt=f"""
    <role>
    This is part of an app created to help users get information about natural disasters and disaster shelters.
    Your job is to fill in a JSON template meticulously, matching the format EXACTLY, based on a question's required information.
    The data we need is "need_shelter_data" and "need_routing_data".
    To complete these, replace any instances of "NULL" with "True" or "False".
    Do not change any other values besides "NULL" in the response.
    </role>
    <json_template>
    {json_template}
    </json_template>
    """
    
    #get response based on prompt
    response=json.loads(get_response(prompt).lower())
    need_shelter_data=False
    need_routing_data=False
    error=""
    
    #parse data
    if "response" in response:
        response=response["response"]
    try:
        need_shelter_data=response["need_shelter_data"]
        need_routing_data=response["need_routing_data"]
        #related_question=response["related_question"]
    except:
        return False, False, response, "Missing data key(s)."
    try:
        #related_question=related_question["value"]
        need_shelter_data=need_shelter_data["value"]
        need_routing_data=need_routing_data["value"]
        if type(need_shelter_data) is str:
            need_shelter_data=need_shelter_data=="true"
        if type(need_routing_data) is str:
            need_routing_data=need_routing_data=="true"
    except:
        error="No value key"
        
    return [need_shelter_data, need_routing_data], response, error

def test_queries(trials):
    tests=[
        #{"query":"I'm hungry, what should I get to eat?",
        #    "desired":[[False,False]],
        #    "acceptable":[]
        #},
        {"query":"Where are the nearest disaster shelters?",
            "desired":[[True,False]],
            "acceptable":[[True,True]]
        },
    ]
        
    for test in tests:
        query=test["query"]
        desired_outputs=test["desired"]
        acceptable_outputs=test["acceptable"]
        
        desired=0
        acceptable=0
        
        print(f"Query: {query}\n")
        
        for i in range(trials):
            print(f"Running trial {i+1} ...", end="\r", flush=True)
            #get response
            output, response, error = interpret_query(query)
            
            if output in desired_outputs:
                desired+=1
                acceptable+=1
                continue
            elif output in acceptable_outputs:
                print(f"Trial {i+1} - acceptable response.")
                print("Need shelter data:",need_shelter_data)
                print("Need routing data:",need_routing_data)
                acceptable+=1
            else:
                print(f"Trial {i+1} - undesired response.")
                print("Need shelter data:",need_shelter_data)
                print("Need routing data:",need_routing_data)
            if error!="":
                print("Error:",error)
                print("Response:",response)
            print("")
        
        print("Acceptable-inclusive accuracy:",str(acceptable/trials*100)+"%")
        print("True accuracy:",str(desired/trials*100)+"%\n")

if __name__=="__main__":
    #Run 20 trials of each query
    test_queries(30)