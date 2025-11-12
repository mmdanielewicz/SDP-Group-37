import sys
import json
from ollama import chat
from ollama import ChatResponse


def get_response(prompt, model="llama3.1:8b"):
    response: ChatResponse = chat(
        model=model, 
        messages=[{'role': 'system', 'content': prompt}],
        format="json",
        options={"temperature":0.075}
    )
    return response.message.content

def interpret_query(query):
    json_template={
        "Question":query,
        "Response":{
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
    except:
        return [False, False], response, "Missing data key(s)."
    try:
        need_shelter_data=need_shelter_data["value"]
        need_routing_data=need_routing_data["value"]
        if type(need_shelter_data) is str:
            need_shelter_data=need_shelter_data=="true"
        if type(need_routing_data) is str:
            need_routing_data=need_routing_data=="true"
    except:
        error="No value key"
        
    return [need_shelter_data, need_routing_data], response, error

def test_queries():
    tests=[
        #Asking for only shelter data
        {"query":"Where are the nearest disaster shelters?",
            "desired":[[True,False]],
            "acceptable":[[True,True]],
            "trials":10
        },
        #Asking for routing data
        {"query":"How do I get to the Storrs disaster shelter?",
            "desired":[[True, True]],
            "acceptable":[],
            "trials":10
        },
        #Random unrelated question
        {"query":"I really really like pigs. Do you like pigs?",
            "desired":[[False,False]],
            "acceptable":[],
            "trials":5
        },
    ]
        
    for test in tests:
        query=test["query"]
        desired_outputs=test["desired"]
        acceptable_outputs=test["acceptable"]
        trials=test["trials"]
        
        desired=0
        acceptable=0
        
        print(f"Query: {query}")
        print(f"{trials} trials")
        print("Desired output:")
        if desired_outputs[0][0]:
            print("Need data agent")
        else:
            print("Don't need data agent")
        if desired_outputs[0][1]:
            print("Need routing agent")
        else:
            print("Don't need routing agent")
        print("")
        
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
                print("Output:",output)
                acceptable+=1
            else:
                print(f"Trial {i+1} - undesired response.")
                print("Output:",output)
            if error!="":
                print("Error:",error)
                print("Response:",response)
            print("")
        
        print("Acceptable-inclusive accuracy:",str(acceptable/trials*100)+"%")
        print("True accuracy:",str(desired/trials*100)+"%\n")

if __name__=="__main__":
    test_queries()