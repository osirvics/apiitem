from models import Base, User, Item
from flask import Flask, jsonify, request, url_for, abort, g, render_template
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import or_

from flask_httpauth import HTTPBasicAuth
import json

#NEW IMPORTS
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import requests

# from apiclient import discovery
# from oauth2client import client

auth = HTTPBasicAuth()


engine = create_engine('sqlite:///usersWithOAuth.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']



@auth.verify_password
def verify_password(username_or_token_or_email, password):
    #Try to see if it's a token first
    user_id = User.verify_auth_token(username_or_token_or_email)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        user = session.query(User).filter_by(username = username_or_token_or_email).first()
        if user is None:
             user = session.query(User).filter_by(email = username_or_token_or_email).first()
        print(user)
        print("Working")
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

@app.route('/')
def start():
    return render_template('clientOAuth.html')

@app.route('/api/oauth/<provider>', methods = ['POST'])
def login(provider):
    #STEP 1 - Parse the auth code
    auth_code = request.json.get('auth_code')
    ##auth_code = "4/CnMwENqsTrBG9vOnn3g0XCOWRF1-zOpfqPCyYqK11Q0"
    print ("Step 1 - Complete, received auth code %s" % auth_code)
    #print(auth_code)
    if provider == 'google':
        # CLIENT_SECRET_FILE = 'client_secret.json'
        # credentials = client.credentials_from_clientsecrets_and_code(
        # CLIENT_SECRET_FILE,
        # ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
        # auth_code)
        # user_id = credentials.id_token['sub']
        

        # email = credentials.id_token['email']
        # print(email)

        # #Get user info
        # h = httplib2.Http()
        # userinfo_url =  "https://www.googleapis.com/oauth2/v2/userinfo"
        # params = {'access_token': credentials.access_token, 'alt':'json'}
        # answer = requests.get(userinfo_url, params=params)

        # data = answer.json()
        # name = data['name']
        # picture = data['picture']
        # email = data['email']
        # user_id = data["id"]
        # print(name)
        # print(picture)
        # print(email)
        # print(id)


        # name = credentials.id_token['name']
        # picture = credentials.id_token['picture']
        # #email = credentials.id_token['email']
        # user_id = credentials.id_token["id"]
        

        # user = session.query(User).filter_by(email=email).first()
        # if not user:
        #     user = User(username = name, picture = picture, email = email, user_id = user_id)
        #     session.add(user)
        #     session.commit()
		
		
		
	    
    	
		










        #STEP 2 - Exchange for a token
        #try:
            # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'http://localhost:5000'
        credentials = oauth_flow.step2_exchange(auth_code)
        #except FlowExchangeError:
            #response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
            #response.headers['Content-Type'] = 'application/json'
            #return response
          
        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'
            
        # # Verify that the access token is used for the intended user.
        # gplus_id = credentials.id_token['sub']
        # if result['user_id'] != gplus_id:
        #     response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response

        # # Verify that the access token is valid for this app.
        # if result['issued_to'] != CLIENT_ID:
        #     response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response

        # stored_credentials = login_session.get('credentials')
        # stored_gplus_id = login_session.get('gplus_id')
        # if stored_credentials is not None and gplus_id == stored_gplus_id:
        #     response = make_response(json.dumps('Current user is already connected.'), 200)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response
        print ("Step 2 Complete! Access Token : %s " % credentials.access_token)

        #STEP 3 - Find User or make a new one
        
        #Get user info
        h = httplib2.Http()
        userinfo_url =  "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt':'json'}
        answer = requests.get(userinfo_url, params=params)
        
        data = answer.json()
        name = data['name']
        picture = data['picture']
        email = data['email']
        user_id = data["id"]
        
        # #see if user exists, if it doesn't make a new one
        user = session.query(User).filter_by(email=email).first()
        if not user:
            user = User(username = name, picture = picture, email = email, user_id = user_id)
            session.add(user)
            session.commit()



        #STEP 4 - Make token
        token = user.generate_auth_token(600)

        

        #STEP 5 - Send back token to the client 
        return jsonify({'token': token.decode('ascii')})
        #return jsonify({'token': token.decode('ascii'), 'duration': 600})
    else:
        return 'Unrecoginized Provider'

@app.route('/api/login')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})



@app.route('/api/users', methods = ['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    user_id = request.json.get('user_id')
    if username is None or password is None or email is None:
        print ("missing arguments")
        abort(400) 
        
    if session.query(User).filter_by(email = email).first() is not None or session.query(User).filter_by(username = username).first() is not None:
        print ("existing user")
        user = session.query(User).filter_by(username=username).first()
        return jsonify({'message':'user already exists'}), 200#, {'Location': url_for('get_user', id = user.id, _external = True)}
        
    user = User(username = username, email = email, user_id = user_id)
    user.hash_password(password)
    session.add(user)
    session.commit()
    return jsonify({ 'username': user.username }), 201#, {'Location': url_for('get_user', id = user.id, _external = True)}

@app.route('/api/users/<int:id>')
def get_user(id):
    user = session.query(User).filter_by(id=id).one()
    if not user:
        abort(400)
    return jsonify({'username': user.username})

@app.route('/api/resource')
@auth.login_required
def get_resource():
    return jsonify({ 'data': 'Hello, %s!' % g.user.username })


@app.route('/api/items', methods = ['GET','POST'])
#protect this route with a required login
@auth.login_required
def showAllItems():
    if request.method == 'GET':
        items = session.query(Item).all()
        return jsonify(items = [item.serialize for item in items])

    elif request.method == 'POST':
        name = request.json.get('name')
        description = request.json.get('description')
        picture = request.json.get('picture')
        price = request.json.get('price')
        newItem = Item(name = name, description = description, picture = picture, price = price)
        session.add(newItem)
        session.commit()
        return jsonify(newItem.serialize)

#Make another app.route() decorator here that takes in an integer id in the URI
@app.route("/api/items/<int:id>", methods = ['GET', 'PUT', 'DELETE'])
#Call the method to view a specific item
def getAnItem(id):
  if request.method == 'GET':
    return getItem(id)
    
#Call the method to edit a specific item
  elif request.method == 'PUT':
    name = request.args.get('name', '')
    description = request.args.get('description', '')
    picture = request.args.get('picture', '')
    price =  request.args.get('price', '')
    return updateItem(id,name, description, price, picture)
    
 #Call the method to remove a puppy 
  elif request.method == 'DELETE':
    return deleteItem(id)

def updateItem(id, name, description, picture, price):
    item = session.query(Item).filter_by(id = id).one()
    if not name:
        item.name = name
    if not description:
        item.description = description
    if not picture:
        item.picture = picture
    if not price:
        item.price = price
    session.add(item)
    session.commit()
    return "Succesfully updated item %s" % id

def deleteItem(id):
    item = session.query(Item).filter_by(id = id).one()
    name = item.name
    session.delete(item)
    session.commit()
    return "Succesfully removed %s" % name + "from database"

def getItem(id):
    item = session.query(Item).filter_by(id = id).one()
    return jsonify(item = item.serialize) 


if __name__ == '__main__':
    app.debug = False
    #app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    app.run(host='0.0.0.0')