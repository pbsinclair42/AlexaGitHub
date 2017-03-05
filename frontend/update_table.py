from flask import Flask, redirect, url_for, request
import boto3
import json
app = Flask(__name__)

@app.route('/success/<name>')
def success(name):
   return '%s\'s password received' % name

def send(username, password):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('users')
    response = table.put_item(
       Item={
            'username': username,
            'password': password
        }
    )
    print("PutItem succeeded")

@app.route('/login',methods = ['POST', 'GET'])
def login():
   if request.method == 'POST':
      user = request.form['nm']
      pwd = request.form['pass']
      send(user, pwd)
      return redirect(url_for('success',name = user))
   else:
      user = request.args.get('nm')
      pwd = request.args.get('pass')
      send(user, pwd)
      return redirect(url_for('success',name = user))

"""@app.route("/")
def hello():
    return "Hello World!" """

if __name__ == "__main__":
    app.run(debug = True)
