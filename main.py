import sys
from src.orchestration import orchestration
from src.response_agent.response_agent import generate_response

if __name__=="__main__":
    #default query
    query="What are the routes to the closest disaster shelters?"
    
    # allow user to pass query from terminal
    if len(sys.argv) == 2:
        query = sys.argv[1]

    # 1. run orchestration (collects shelter and routing data)
    # NOTE: orchestration.main() already prints context, so this keeps existing behavior
    context = orchestration.main(query)

    # 2. run the response agent to summarize the context
    output = generate_response(query, context)

    print("\n===== RESPONSE AGENT OUTPUT =====\n")
    print(output)
