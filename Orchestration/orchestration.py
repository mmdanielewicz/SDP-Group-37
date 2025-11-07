from ollama import chat
from ollama import ChatResponse

def get_response(prompt):
    response: ChatResponse = chat(
        model="llama3.1:8b", 
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.message.content
    
def test():
    print(get_response("In a short sentence, tell me what color the sky usually is."))
    

if __name__=="__main__":
    test()