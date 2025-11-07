import sys
from ollama import chat
from ollama import ChatResponse


def get_response(prompt, model="llama3.1:8b"):
    response: ChatResponse = chat(
        model=model, 
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.message.content

def test():
    prompt="In a short sentence, tell me what color the sky usually is."
    if len(sys.argv)==2:
        prompt=sys.argv[1]
    print("Prompt:",prompt)
    print("Response:",get_response(prompt))

if __name__=="__main__":
    test()