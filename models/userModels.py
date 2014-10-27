from flask.ext.sqlalchemy import SQLAlchemy 
from flask.ext.security import SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user
from flask.ext.security.utils import *
from sqlalchemy.orm import mapper
#facebook login will be handled via a javascript ajax request to this app's endpoint
from kickstart import *
import random, hashlib
"""
For login/registration/permissions we will be using flask-security. This is a conglomeration of several independently powerful flask libraries. Flask-Login, Flask-Authentication, Flask-OAuthLib, WTF-Flask, etc.

It gives us some useful methods:
flask_security.utils.verify_password(password, hash_password) checks an entered password against a stored and hashed password
flask_security.utils.encrypt_password(plaintext_password)
flask_security.utils.login_user(user, remember=None)
*.logout_user() Cleans out session
user_datastore.add_role_to_user(user, role)
user_datastore.create_user(**kwargs)
user_datastore.get_user(id_or_email)

More can be found here: https://pythonhosted.org/Flask-Security/api.html#flask_security.datastore.SQLAlchemyUserDatastore.activate_user

"""
#map Users to Roles
roles_users = db.Table('roles_users',
		db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
		db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
	"""
	Roles for determining User permissions and access levels.
	Permission table:
	Purchase Roverpass - Upload images, Leave Review
	Claim campground - Edit page, Upload, Leave Review
	Opt-In - Forces Claim
	Sales - All + Access to hidden management auth-code table.
	"""

	#__tablename__ = 'roles'
	id = db.Column(db.Integer(), primary_key=True)
	name = db.Column(db.String(80), unique=True)
	description = db.Column(db.String(255))

class User(db.Model, UserMixin):
	"""
	A User of the system.
	In order to create a User, they MUST purchase a Roverpass.
	"""
	#methods required by flask-login:
	#is_authenticated()
	#is_active()
	#is_anonymous()
	#get_id()
	#it will inherit all of these from UserMixin

	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(255), unique=True)
	password = db.Column(db.String(120))
	active = db.Column(db.Boolean())
	pass_purchase_date = db.Column(db.DateTime())
	pass_expiration_date = db.Column(db.DateTime())
	pass_expired = db.Column(db.Boolean())
	auto_renew = db.Column(db.Boolean())
	roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
	camp_owned = db.Column(db.Integer, db.ForeignKey('campground.id'))
	address = db.Column(db.String())
	city = db.Column(db.String())
	zip_code = db.Column(db.String())
	state = db.Column(db.String())
	country = db.Column(db.String())
	#the following fields will only be used for campground owners that have opted in
	#(acquired via opt in form)
	phone_number = db.Column(db.String())
	contact_email = db.Column(db.String())
	first_name = db.Column(db.String())
	last_name = db.Column(db.String())

	def generate_new_password(self):
		return hashlib.sha224(str(random.randrange(1000000))).hexdigest()[:10]

"""#handles API connections (twitter, facebook)
class Connection(db.Model):
	__tablename__ = "connections"

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
	provider_id = db.Column(db.String(255))
	provider_user_id = db.Column(db.String(255))
	access_token = db.Column(db.String(255))
	secret = db.Column(db.String(255))
	display_name = db.Column(db.String(255))
	profile_url = db.Column(db.String(512))
	image_url = db.Column(db.String(512))
	rank = db.Column(db.Integer)
"""