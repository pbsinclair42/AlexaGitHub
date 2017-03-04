import json
from env import requests
import secrets

def lambda_handler(event, context):
    if event['session']['application']['applicationId'] != secrets.APP_ID:
        raise ValueError("Invalid Application ID")
    
    template_response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": "INSERT TEXT HERE"
            },
            "card": {
                "content": "INSERT TEXT HERE",
                "title": "RESPONSE TITLE",
                "type": "Simple"
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": ""
                }
            },
            "shouldEndSession": False
          },
      "sessionAttributes": {}
    }
    if event['request']['intent']['name'] == 'GetTorvaldsIntent':
        torvalds_event = json.loads(requests.get('https://api.github.com/users/torvalds/events').content)[0]
        if torvalds_event['type']=='PushEvent':
            count = len(torvalds_event['payload']['commits'])
            repo = torvalds_event['repo']['name'].split('/')[1]
            template_response['response']['outputSpeech']['text'] = "Torvalds pushed "+str(count)+' commits to the '+repo+' repo'
            template_response['response']['card']['content'] = "Torvalds pushed "+str(count)+' commits to the '+repo+' repo'
            template_response['response']['card']['title'] = "Torvalds activity"
        else:
            template_response['response']['outputSpeech']['text'] = "Torvalds did some weird shit"
            template_response['response']['card']['content'] = "Torvalds did some weird shit"
            template_response['response']['card']['title'] = "Torvalds activity"
    else:
        template_response['response']['outputSpeech']['text'] = "//TODO"
        template_response['response']['card']['content'] = "//TODO"
        template_response['response']['card']['title'] = "//TODO"
        
    return template_response
