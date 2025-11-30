import sys
import os
import json
from ollama import chat
from ollama import ChatResponse
from ..data_agent.data_agent import DataAgent
from ..routing_agent import RoutingAgent


#gets response from LLM
def get_response(prompt, model="llama3.1:8b"):
	response: ChatResponse = chat(
		model=model, 
		messages=[{'role': 'system', 'content': prompt}],
		format="json",
		options={"temperature":0.075}
	)
	return response.message.content

#returns required data for answering response
def interpret_query(query):
	json_template={
		"Question":query,
		"Response":{
			"need_shelter_data":{
				"Description":"To answer this question, we need data about disaster shelter locations or services.",
				"Value":"NULL"
			},
			"need_routing_data":{
				"Description":"To answer this question, we need to find directions to a location or set of locations.",
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
		{"query":"How do I get to the disaster shelter in Storrs?",
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
        
def main(query):
	#test_queries()
	#return
	
	print("Query:",query)
	context={
		"query":query,
		"shelter_results":None,
		"routing_results":None
	}
	
	output, response, error = interpret_query(query)
	if error!="":
		print("Error in interpret_query:",error)
		print("Response:",response)
		return
		
	shelter_data = None
	if output[0]:
		agent = DataAgent(base_path="src/data_agent/data")
		shelter_data = agent.handle_query(lat=41.2940, lon=-72.3768, state="CT")
	else:
		print("Data agent not necessary")

	if output[1] and shelter_data:
		print("Starting routing agent...")
		shelters_for_routing = {}
		for shelter in shelter_data["nearest_shelters"]:
			shelters_for_routing[shelter["name"]] = [shelter["lat"], shelter["lon"]]

		routing_result = RoutingAgent.get_routes(
			user_lat=41.2940, 
			user_lon=-72.3768, 
			shelters=shelters_for_routing
		)
		print(json.dumps(routing_result, indent=2))
	else:
		print(f"Routing not triggered. need_routing: {output[1]}, has_shelter_data: {shelter_data is not None}")