from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user, AnonymousUser, roles_required
from flask.ext.security.utils import *
from flask.ext.security.confirmable import *
from flask.ext.principal import Principal, Permission, RoleNeed
from flask.ext.login import LoginManager
from flask_mail import Mail, Message
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://roverpass:roverpass@localhost/roverpass'
db = SQLAlchemy(app)

BASE_URL = 'http://107.170.60.95'

app.jinja_options['extensions'].append('jinja2.ext.loopcontrols')
SQLALCHEMY_BINDS = {
    'user_db': app.config['SQLALCHEMY_DATABASE_URI'],
    'campground_db': 'postgres://postgres:postgres@localhost/campground'
}
app.secret_key = 'goforfun'

#google api info
GOOGLE_API_KEY='AIzaSyDqQU7ovrKcbjS13lifn83dG6FLmM71hFA'
GOOGLE_URL = 'https://www.googleapis.com/customsearch/v1'
GOOGLE_CX = '011939436523733206751:6hccyfxo7qc'

#flask-security
app.config['SECURITY_POST_LOGIN'] = '/'

#flask-social for facebook and twitter
app.config['SOCIAL_TWITTER'] = {
	'consumer_key': 'HXy7JHIBI5kIpfRRPnq0EWlYp',
	'consumer_secret': 'LAto3gGXRXwJzD4aKSbMVTs3LuI41GgKKcSIutSnZi5F7Uk4sn'
}

app.config['SOCIAL_FACEBOOK'] = {
	'consumer_key' : '1498934676996386',
	'consumer_secret' : '3b89f94bb85ae16093bcc550fc9e5b99'
}

#handle permissions via principal
#to restrict view to user type, add decorator:
# @permission_name.require()
#principals = Principal(app)

#flask-login prep
login_manager = LoginManager()
login_manager.login_view = 'login' #after login, there is a "next" variable in the query string that indicates where the user was trying to access
login_manager.login_message = "You must logged in to do that."
login_manager.init_app(app)

#flask-mail
#mail = Mail(app)

#define messages here
#welcome_to_roverpass = Message()
#thank_you_for_opting_in = Message()
#forgot_password = Message()
