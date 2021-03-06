import json
import decimal
import re
import dateutil.parser
from datetime import timedelta
from random import choice
import boto3
from botocore.exceptions import ClientError
from env import requests
import secrets

def lambda_handler(event, context):
    username = 'alexaAwakens' #TODO: somehow get them to enter their details

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
            "shouldEndSession": True
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
    elif event['request']['intent']['name'] == 'GetNumNotificationsIntent':
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table('users')
        try:
            response = table.get_item(
                    Key={
                        'username': username
                        }
                )
        except ClientError as e:
            return e.response
        else:
            item = response['Item']
            password = item['password']
            notifications = json.loads(requests.get('https://api.github.com/notifications', auth=(username, password)).content)
            outputSpeech = "You have "+str(len(notifications))+' new notifications.'
            template_response['response']['outputSpeech']['text'] = outputSpeech
            template_response['response']['card']['content'] = outputSpeech
            template_response['response']['card']['title'] = "Notifications for "+username

    elif event['request']['intent']['name'] == 'NextNotificationIntent':

        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table('users')
        try:
            response = table.get_item(
                    Key={
                        'username': username
                        }
                )
        except ClientError as e:
            return e.response
        else:
            item = response['Item']
            password = item['password']
            notifications = json.loads(requests.get('https://api.github.com/notifications', auth=(username, password)).content)
            if not event['session']['new']:
                t = notifications[-1]['updated_at']
                t = (dateutil.parser.parse(t)+timedelta(minutes=5)).isoformat()
                t = t[:-6]+'Z'
                data = json.dumps({'last_read_at':t})
                requests.put('https://api.github.com/notifications', data=data, auth=(username, password)) 
                notifications.pop()

            notification = 'New ' + notifications[-1]['subject']['type']
            try:
                notification += ' in ' + notifications[-1]['repository']['full_name']
            except:
                pass
            notification += ': ' + notifications[-1]['subject']['title']
            template_response['response']['outputSpeech']['text'] = notification
            template_response['response']['card']['content'] = notification
            template_response['response']['card']['title'] = "Newest notification for "+username
            template_response['response']['shouldEndSession'] = False

    elif event['request']['intent']['name'] == 'RepeatNotificationIntent':
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table('users')
        try:
            response = table.get_item(
                    Key={
                        'username': username
                        }
                )
        except ClientError as e:
            return e.response
        else:
            item = response['Item']
            password = item['password']
            notifications = json.loads(requests.get('https://api.github.com/notifications', auth=(username, password)).content)
            notification = 'New ' + notifications[-1]['subject']['type']
            try:
                notification += ' in ' + notifications[-1]['repository']['full_name']
            except:
                pass
            notification += ': ' + notifications[-1]['subject']['title']
            template_response['response']['outputSpeech']['text'] = notification
            template_response['response']['card']['content'] = notification
            template_response['response']['card']['title'] = "Newest notification for "+username
            template_response['response']['shouldEndSession'] = False

    elif event['request']['intent']['name'] == 'MyActivityIntent':
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table('users')
        try:
            response = table.get_item(
                    Key={
                        'username': username
                        }
                )
        except ClientError as e:
            return e.response
        else:
            item = response['Item']
            password = item['password']
            activity = json.loads(requests.get('https://api.github.com/users/'+username+'/events', auth=(username, password)).content)
            try:
                activity = activity[0]
            except IndexError:
                template_response['response']['outputSpeech']['text'] = "No activity"
                template_response['response']['card']['content'] = "No activity"
                template_response['response']['card']['title'] = "Your activity"
            else:
                activity_type = activity['type'][:-5]
                if activity_type=='Push':
                    repo = activity['repo']['name']
                    commits = map(lambda x : x['message'].split('\n\n')[0], activity['payload']['commits'])
                    if len(commits)==1:
                        response = "You pushed a commit with message; '"+commits[0].split('\n\n')[0]+"'; to the repository, "+repo
                    elif len(commits)>5:
                        response = "You pushed "+str(len(commits))+' commits to the repository, '+repo
                    else:
                        response = "You pushed "+str(len(commits))+' commits to the repository, '+repo+' . These were:\n'+';\n'.join(commits)
                    template_response['response']['outputSpeech']['text'] = response
                    template_response['response']['card']['content'] = response
                else:
                    template_response['response']['outputSpeech']['text'] = "You did some weird shit with "+activity_type+'s'
                    template_response['response']['card']['content'] = "You did some weird shit with "+activity_type+'s'
                template_response['response']['card']['title'] = "Your activity"

    elif event['request']['intent']['name'] == 'GetMyRepositoriesIntent':
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table('users')
        try:
            response = table.get_item(
                    Key={
                        'username': username
                        }
                )
        except ClientError as e:
            return e.response
        else:
            item = response['Item']
            password = item['password']
            repos = json.loads(requests.get('https://api.github.com/user/repos', auth=(username, password)).content)
            repos = map(lambda x: x['name'], repos)
            if len(repos)>0:
                response = "You have "+str(len(repos))+' repositories: \n' + ';\n'.join(repos)
                template_response['response']['outputSpeech']['text'] = response
                template_response['response']['card']['content'] = response
            else:
                template_response['response']['outputSpeech']['text'] = "You have no repositories"
                template_response['response']['card']['content'] = "You have no repositories"
            template_response['response']['card']['title'] = "Your repositories"

    elif event['request']['intent']['name'] == 'GetLastCommitsIntent':
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table('users')
        try:
            response = table.get_item(
                    Key={
                        'username': username
                        }
                )
        except ClientError as e:
            return e.response
        else:
            item = response['Item']
            password = item['password']
            repo_name = event['request']['intent']['slots']['repoName']['value'].split( )
            repo_name = map(lambda x: x.lower(), repo_name)
            for i in range(len(repo_name)):
                if repo_name[i]=='dash':
                    repo_name[i]='-'
                if repo_name[i]=='underscore':
                    repo_name[i]='_'
                if repo_name[i]=='plus':
                    repo_name[i]='+'
                if repo_name[i]=='slash':
                    repo_name[i]='/'
            repo_name = ''.join(repo_name)

            commits = json.loads(requests.get('https://api.github.com/repos/'+username+'/'+repo_name+'/commits', auth=(username, password)).content)
            try:
                commits['message']
                template_response['response']['outputSpeech']['text'] = "Unknown repository "+repo_name
                template_response['response']['card']['content'] = "Unknown repository "+repo_name
            except TypeError:
                if len(commits)>0:
                    message = commits[0]['commit']['message'].split('\n\n')[0]
                    response = "Latest commit to "+repo_name+": \n"+message
                    template_response['response']['outputSpeech']['text'] = response
                    template_response['response']['card']['content'] = response
                else:
                    template_response['response']['outputSpeech']['text'] = "No commits in repository "+repo_name
                    template_response['response']['card']['content'] = "No commits in repository "+repo_name
                template_response['response']['card']['title'] = "Latest commit in "+repo_name

    elif event['request']['intent']['name'] == 'GetLastActivityIntent':
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table('users')
        try:
            response = table.get_item(
                    Key={
                        'username': username
                        }
                )
        except ClientError as e:
            return e.response
        else:
            item = response['Item']
            password = item['password']
            repo_name = event['request']['intent']['slots']['repoName']['value'].split( )
            repo_name = map(lambda x: x.lower(), repo_name)
            for i in range(len(repo_name)):
                if repo_name[i]=='dash':
                    repo_name[i]='-'
                if repo_name[i]=='underscore':
                    repo_name[i]='_'
                if repo_name[i]=='plus':
                    repo_name[i]='+'
                if repo_name[i]=='slash':
                    repo_name[i]='/'
            repo_name = ''.join(repo_name)

            events = json.loads(requests.get('https://api.github.com/repos/'+username+'/'+repo_name+'/events', auth=(username, password)).content)
            try:
                events['message']
                template_response['response']['outputSpeech']['text'] = "Unknown repository "+repo_name
                template_response['response']['card']['content'] = "Unknown repository "+repo_name
            except TypeError:
                activity = events[0]
                activity_type = activity['type'][:-5]
                if activity_type=='Push':
                    repo = activity['repo']['name']
                    commits = map(lambda x : x['message'].split('\n\n')[0], activity['payload']['commits'])
                    if len(commits)==1:
                        response = "A commit with message; '"+commits[0]+"'; was pushed to the repository, "+repo+', by '+activity['actor']['display_login']
                    elif len(commits)>5:
                        response = str(len(commits))+' commits were pushed to the repository, '+repo+', by '+activity['actor']['display_login']
                    else:
                        response = str(len(commits))+' commits were pushed to the repository, '+repo+', by '+activity['actor']['display_login']+' . These were:\n'+';\n'.join(commits)
                    template_response['response']['outputSpeech']['text'] = response
                    template_response['response']['card']['content'] = response
                else:
                    template_response['response']['outputSpeech']['text'] = "Some weird shit to do with "+activity_type+'s stuff was done to the repo '+repo+', by '+activity['actor']['display_login']
                    template_response['response']['card']['content'] = "Some weird shit to do with "+activity_type+'s stuff was done to the repo '+repo+', by '+activity['actor']['display_login']

    elif event['request']['intent']['name'] == 'GetIssuesIntent':
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table('users')
        try:
            response = table.get_item(
                    Key={
                        'username': username
                        }
                )
        except ClientError as e:
            return e.response
        else:
            item = response['Item']
            password = item['password']
            repo_name = event['request']['intent']['slots']['repoName']['value'].split( )
            repo_name = map(lambda x: x.lower(), repo_name)
            for i in range(len(repo_name)):
                if repo_name[i]=='dash':
                    repo_name[i]='-'
                if repo_name[i]=='underscore':
                    repo_name[i]='_'
                if repo_name[i]=='plus':
                    repo_name[i]='+'
                if repo_name[i]=='slash':
                    repo_name[i]='/'
            repo_name = ''.join(repo_name)

            issues = json.loads(requests.get('https://api.github.com/repos/'+username+'/'+repo_name+'/issues', auth=(username, password)).content)
            try:
                issues['message']
                template_response['response']['outputSpeech']['text'] = "Unknown repository "+repo_name
                template_response['response']['card']['content'] = "Unknown repository "+repo_name
            except TypeError:
                if len(issues)>0:
                    response = str(len(issues))+' open issues in '+repo_name+':\n'
                    response += ';\n'.join(["Issue "+str(i+1)+' from '+issue['user']['login']+': '+issue['title']+';' for i, issue in enumerate(issues)])
                    template_response['response']['outputSpeech']['text'] = response
                    template_response['response']['card']['content'] = response
                else:
                    template_response['response']['outputSpeech']['text'] = "No open issues in repository "+repo_name
                    template_response['response']['card']['content'] = "No open issues in repository "+repo_name
                template_response['response']['card']['title'] = "Issues in "+repo_name

    elif event['request']['intent']['name'] == 'GetPullsIntent':
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table('users')
        try:
            response = table.get_item(
                    Key={
                        'username': username
                        }
                )
        except ClientError as e:
            return e.response
        else:
            item = response['Item']
            password = item['password']
            repo_name = event['request']['intent']['slots']['repoName']['value'].split( )
            repo_name = map(lambda x: x.lower(), repo_name)
            for i in range(len(repo_name)):
                if repo_name[i]=='dash':
                    repo_name[i]='-'
                if repo_name[i]=='underscore':
                    repo_name[i]='_'
                if repo_name[i]=='plus':
                    repo_name[i]='+'
                if repo_name[i]=='slash':
                    repo_name[i]='/'
            repo_name = ''.join(repo_name)

            pulls = json.loads(requests.get('https://api.github.com/repos/'+username+'/'+repo_name+'/pulls', auth=(username, password)).content)
            try:
                pulls['message']
                template_response['response']['outputSpeech']['text'] = "Unknown repository "+repo_name
                template_response['response']['card']['content'] = "Unknown repository "+repo_name
            except TypeError:
                if len(pulls)>0:
                    response = str(len(pulls))+' open pull requests in '+repo_name+':\n'
                    response += ';\n'.join(["Pull Request "+str(i+1)+' from '+pull['user']['login']+': '+pull['title']+';' for i, pull in enumerate(pulls)])
                    template_response['response']['outputSpeech']['text'] = response
                    template_response['response']['card']['content'] = response
                else:
                    template_response['response']['outputSpeech']['text'] = "No open pull requests in repository "+repo_name
                    template_response['response']['card']['content'] = "No open pull requests in repository "+repo_name
                template_response['response']['card']['title'] = "Open pull Requests in "+repo_name

    elif event['request']['intent']['name'] == 'StalkIntent':
        user_name = event['request']['intent']['slots']['username']['value'].split( )
        user_name = map(lambda x: x.lower(), user_name)
        mapping = {
            'dash':'-',
            'underscore':'_',
            'plus':'+',
            'slash':'/',
            'one':'1',
            'two':'2',
            'three':'3',
            'four':'4',
            'five':'5',
            'six':'6',
            'seven':'7',
            'eight':'8',
            'nine':'9',
            'zero':'0'
        }
        for i in range(len(user_name)):
            if user_name[i] in mapping.keys():
                user_name[i] = mapping[user_name[i]]
        user_name = ''.join(user_name)

        events = json.loads(requests.get('https://api.github.com/users/'+user_name+'/events').content)
        try:
            events['message']
            template_response['response']['outputSpeech']['text'] = "Unknown user "+user_name
            template_response['response']['card']['content'] = "Unknown user "+user_name
        except TypeError:
            if len(events)>0:
                activity = events[0]
                activity_type = activity['type'][:-5]
                if activity_type=='Push':
                    repo = activity['repo']['name']
                    commits = map(lambda x : x['message'].split('\n\n')[0], activity['payload']['commits'])
                    if len(commits)==1:
                        response = user_name+" pushed a commit with message; '"+commits[0]+"'; to the repository, "+repo
                    elif len(commits)>5:
                        response = user_name+" pushed "+str(len(commits))+' commits to the repository, '+repo
                    else:
                        response = user_name+" pushed "+str(len(commits))+' commits to the repository, '+repo+' . These were:\n'+';\n'.join(commits)
                    template_response['response']['outputSpeech']['text'] = response
                    template_response['response']['card']['content'] = response
                else:
                    template_response['response']['outputSpeech']['text'] = user_name+" did some weird shit with "+activity_type+'s'
                    template_response['response']['card']['content'] = user_name + " did some weird shit with "+activity_type+'s'
            else:
                template_response['response']['outputSpeech']['text'] = user_name+"hasn't done anything yet"
                template_response['response']['card']['content'] = user_name+"hasn't done anything yet"
            template_response['response']['card']['title'] = user_name + "'s latest activity"

    elif event['request']['intent']['name'] == 'ProfanityIntent':

        profanity = ['\barse\b', 'bastard', 'bitch', 'bloody', 'bollocks', '\bcock', '\bcunt\b', '\bdamn\b', 
                     '\bdick\b', '\bfml\b', 'fuck', '\bnaff\b', '\bpiss', '\bpoo\b', 'shit', '\btits\b', 
                     '\btosser\b', '\btwat', '\bwank', '\bwhore', '\bwtf\b', '\btifu\b']

        for i in range(1,4):
            events = json.loads(requests.get('https://api.github.com/events?page='+str(i)+'&per_page=100&access_token='+secrets.TOKEN).content)
            try:
                commits = [event['payload']['commits'] for event in events if event['type']=='PushEvent']
            except TypeError:
                return events
            messages = [item['message'].split('\n\n')[0] for sublist in commits for item in sublist]
            for message in messages:
                if re.match(r".*(" + '|'.join(profanity) + ").*", message, re.IGNORECASE):
                    if not re.match(r"^Merge", message, re.IGNORECASE):
                        template_response['response']['outputSpeech']['text'] = "Found an angry programmer!  They say: \n"+message
                        template_response['response']['card']['content'] = "Found an angry programmer!  They say: \n"+message
                        template_response['response']['card']['title'] = "Profanity detected!"
                        template_response['response']['outputSpeech']['text'] = ''.join([a for a in template_response['response']['outputSpeech']['text'] if a not in '<>[]{}'])
                        return template_response
        message = choice([ "Shit code is shit, but shit code is doin' what shit code is supposed to do, so i dont give a shit",
            "Fuck Windows.",
            "added some shit file to git ignore",
            "Shitty message because Ive made a ton of changes",
            "git fucking work",
            "Shit works yo",
            "fix: fix regexp again, fuck fucking windows fuck fucking fuck",
            "trying to fucking merge again",
            "New shit, Signed-off-by: Dudley <dudleydawes@hotmail.co.uk>",
            "Fucklord McPenisPumpe",
            "WE CAN FUCKING SEND EVERYTHING FUCK YEAH",
            "holy fucking shit gui so hard",
            "holy shit i'm bad at literally everything",
            "fixed my monumental fuckup",
            "Added checkup table to new SQL script, in case shit...",
            "Yay, I can invent bicycles! Fuck!",
            "After 3 hours of suffer, I finally reazlied that I have an online JSON on Firebase, so there is no need to implement own server...fuck me",
            "RE-ADDED ALL MY APIS, THE NEXT DUDE THAT REMOVES MY SHIT I WILL REPORT YOU TO THE POLICE",
            "improved error handling when connecting/disconnecting, improved youtube duration parsing, more penis shit",
            "senpai better be fucking pleased",
            "I CANT FUCKING DEAL WITH GIT",
            "git fuck it",
            "fuck it ship it",
            "FUCKING WORKING SEARCH FUNCTIONALITY PUSHING INTO MAIN PAGE WOOOOOOO",
            "Shitty respawn changes that mostly don't work",
            "Fixed Jospeh's Fuck up",
            "How the fuck does REDIS work?",
            "A FRONTEND DEV MUST FIX A BACKEND DEVS NOOBY SHIT",
            "Mike fucks everything up",
            "If we don't deploy, the investors walk. Hurry. The. Fuck. Up.",
            'Revert "Shit the bed if this works!"',
            "holy fuck i do not know shit about objective-c",
            "ramen is fucking hot yo"
            ])
        template_response['response']['outputSpeech']['text'] = "No one's angry just now, so here's one from the archive: \n"+message
        template_response['response']['card']['content'] = "No one's angry just now, so here's one from the archive: \n"+message
        template_response['response']['card']['title'] = "No profanity detected"

    elif event['request']['intent']['name'] == 'AMAZON.StopIntent':
        responses = ['See ya', 'Bye', 'Cheerio', "Don't leave me!", "Come back any time"]
        response = choice(responses)
        template_response['response']['outputSpeech']['text'] = response
        template_response['response']['card']['content'] = response
        template_response['response']['card']['title'] = "Exit Message"

    else:
        template_response['response']['outputSpeech']['text'] = "//TODO"
        template_response['response']['card']['content'] = "//TODO"
        template_response['response']['card']['title'] = "//TODO"
    
    template_response['response']['outputSpeech']['text'] = ''.join([a for a in template_response['response']['outputSpeech']['text'] if a not in '<>[]{}'])
    return template_response
