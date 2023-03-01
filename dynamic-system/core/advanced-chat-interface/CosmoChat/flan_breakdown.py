import requests

flan_url = "https://flan.faqx.com/flant5"


def flan_breakdown(query):
    detection = '''Detect if the user message is a question or a conversational statement.
    If the user message is a question, the model will return "question".
    If the user message is a conversational statement, the model will return "statement".
    
    Message: {user_message}
    Detection:'''.format(user_message=query)
    response = requests.post(flan_url, json={"text": detection})
    return response.json()
