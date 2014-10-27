from kickstart import *
from flask import Flask, render_template, make_response, request, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import stripe, oauthlib, requests, psycopg2
from campModels import *
from userModels import *
from userForms import *
import sys
sys.path.append('/var/www/roverpass/roverpass/models')
sys.path.append('/var/www/roverpass/roverpass/forms')
sys.path.append('/var/www/roverpass/roverpass/')
import datetime
import json


"""
RoverPass is a simple aggregation site for RV campsites across the nation, offering a 40% discount on thousands.
"""

#for a user, use user_datastore.add_role_to_user
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
app_security = Security(app, user_datastore)

principals = Principal(app)

user_datastore.create_role(name='base_user', description='This user is allowed to leave a review and upload content.')
user_datastore.create_role(name='sales_user', description='Allows Sales team to access directory of campgrounds & verification codes')
user_datastore.create_role(name='campground_owner', description='This user can edit a campgrounds content, and opt-in to Roverpass')

#create permissions here:
edit_campground = Permission(RoleNeed('sales_user'), RoleNeed('campground_owner'))
upload_media = Permission(RoleNeed('sales_user'), RoleNeed('campground_owner'), RoleNeed('base_user'))
leave_review = Permission(RoleNeed('base_user'))

#db.session.add_all([base_user, sales_user, campground_owner])
#db.session.commit() 

@app_security.login_context_processor
def login_context_processor():
	form = LoginForm()
	return dict(form=form)

# LOGIN #
@login_manager.user_loader
def load_user(id):
	user = User.objects.filter_by(id=id).first()
	return user

@login_manager.request_loader
def load_user_from_request(request):
	#try to login with api (request.args.get('api_key'))
	#then try to login with normal email
	pass

@app.route('/')
def index():
	if current_user.is_authenticated():
		user = current_user
	else:
		user = None
	return render_template('splash.html', user=user)

@app.route('/map')
def map(request):
	pass

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
	form = UserForm(prefix="user")
	if request.method=='POST' and form.validate():
		print 'form validated'
		if User.query.filter_by(email = form.email.data).first() == None:
			print 'user is not None'
			user_datastore.create_user(email=form.email.data,
						password=encrypt_password(form.password.data),
						active=True, has_pass=False)
			print 'created user object'
			#user_datastore.activate_user(User.query.filter_by(email=form.email.data))
			print 'activated user'
			print 'adding user to db'
			db.session.commit()
			user_datastore.add_role_to_user(form.email.data, 'base_user')
			print "commited user"
			return redirect('/login')
		else:
			return render_template('userExists.html')
	else:
		print 'form validation failed'
		response = render_template('create_user.html', form=form)
		return render_template('create_user.html', form=form)

@app.route('/claim_campground')
def claim_campground(request):
	form = VerificationNumberForm()
	if form.validate_on_submit():
		if form.code.data == Campsite.query.filter_by(id=request.args['campsite_id']):
			user_datastore.add_role_to_user(current_user, 'can_edit_campground')
			user_datastore.add_role_to_user(current_user, 'can_upload_media')
			return render_template('campsite_edit.html', campsite=Campsite.query.filter_by(id=request.args['campsite_id']))
		else:
			return render_template('error.html', message='You have entered an incorrect verification code.')

@app.route('/campground/<slug>')
def profile(slug):
	"""
	Campsite profile view. Redirects to AngularJS powered inline editing page if user has the permissions required to edit a campground page.
	"""	
	campground = Campsite.query.filter_by(slug=slug).first()
	address = json.loads(campground.address)
	print address
	print slug

	print campground
	if current_user.has_role('can_edit_campground') and campground:
		return render_template('edit_campground.html', campground = campground, name=str(campground.name).replace('{','').replace('"','').replace('}','') , address=address['results'][0]['name'], lat=address['results'][0]['geometry']['location']['lat'], lng=address['results'][0]['geometry']['location']['lng'])
	elif campground:
		return render_template('campground.html', campground=campground, name=str(campground.name).replace('{','').replace('"','').replace('}',''), address=address['results'][0]['name'], lat=address['results'][0]['geometry']['location']['lat'], lng=address['results'][0]['geometry']['location']['lng'])
	return render_template('404.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	#wtform
	form = LoginForm()

	if form.validate_on_submit():
		username = request.form['username']
		password = request.form['password']
		registered_user = User.query.filter_by(username=username,password=password).first()
		if registered_user is None:
			flash('Username or Password is invalid' , 'error')
			return redirect(url_for('login'))
		login_user(registered_user)
		flash('Logged in successfully')
		return redirect(request.args.get('next') or url_for('index'))

	return render_template('login_user.html', form=form)

@app.route('/logout')
@login_required
def logout():
	# Remove the user information from the session
	logout_user()

	# Remove session keys set by Flask-Principal
	for key in ('identity.name', 'identity.auth_type'):
		session.pop(key, None)

	# Tell Flask-Principal the user is anonymous
	identity_changed.send(current_app._get_current_object(),
						  identity=AnonymousIdentity())

	return redirect(request.args.get('next') or '/')


###ERROR HANDLING###
@app.errorhandler(404)
def pageNotFound(error):
    return "page not found"

@app.errorhandler(500)
def server_error(error):
    return "something broke"
if __name__ == '__main__':
	app.run(debug=True)
