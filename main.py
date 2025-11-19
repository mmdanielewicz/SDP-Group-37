import sys
from src.orchestration import orchestration

if __name__=="__main__":
    #default query
    query="Where are the nearest disaster shelters?"
    
    #specify query from terminal in quotes 
    if len(sys.argv)==2:
        query=sys.argv[1]
    
    orchestration.main(query)