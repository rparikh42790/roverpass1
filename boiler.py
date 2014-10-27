import stripe, oauthlib, requests, psycopg2, os, json, sys, urllib, slugify
from datetime import datetime, timedelta
from flask_oauth import OAuth
from flask import Flask, render_template, abort, make_response, request, redirect
from flask.ext.sqlalchemy import SQLAlchemy
#from flask.ext.social import social
#from flask.ext.social.datastore import SQLALChemyConnectionDatastore
from kickstart import *
from campModels import *
from userModels import *
from userForms import *
from flask.ext.uploads import *
from sqlalchemy_searchable import search as search_campgrounds
from flask.ext.mail import Mail, Message
from flaskext.uploads import (UploadSet, configure_uploads, IMAGES,
                              UploadNotAllowed)
"""
RoverPass is a simple aggregation site for RV campgrounds across the nation, offering a 40% discount on thousands.
"""
STATES = [('None', '---'), ('Alabama', 'AL'),('Alaska', 'AK'),('Arizona', 'AZ'),('Arkansas', 'AR'),('California', 'CA'),('Colorado', 'CO'),('Connecticut', 'CT'),('Delaware', 'DE'),
                    ('Florida', 'FL'),('Georgia', 'GA'),('Hawaii', 'HI'),('Idaho', 'ID'),('Illinois', 'IL'),('Indiana', 'IN'),('Iowa', 'IA'),
                    ('Kansas', 'KS'),('Kentucky', 'KY'),('Louisiana', 'LA'),('Maine', 'ME'),('Maryland', 'MD'),('Massachusetts', 'MA'),('Michigan', 'MI'),
                    ('Minnesota', 'MN'),('Mississippi', 'MS'),('Missouri', 'MO'),('Montana', 'MT'),('Nebraska', 'NE'),('Nevada', 'NV'),
                    ('New Hampshire', 'NH'),('New Jersey', 'NJ'),('New Mexico', 'NM'),('New York', 'NY'),('North Carolina', 'NC'),('North Dakota', 'ND'),
                    ('Ohio', 'OH'),('Oklahoma', 'OK'),('Oregon', 'OR'),('Pennsylvania', 'PA'),('Rhode Island', 'RI'),('South Carolina', 'SC'),
                    ('South Dakota', 'SD'),('Tennessee', 'TN'),('Texas', 'TX'),('Utah', 'UT'),('Vermont', 'VT'),('Virginia', 'VA'),
                    ('Washington', 'WA'),('West Virginia', 'WV'),('Wisconsin', 'WI'),('Wyoming', 'WY')]

### SECURITY ###
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
#user_datastore.create_role(name='base_user', description='This user is allowed to leave a review and upload content.')
#user_datastore.create_role(name='sales_user', description='Allows Sales team to access directory of campgrounds & verification codes')
#user_datastore.create_role(name='campground_owner', description='This user can edit a campgrounds content, and opt-in to Roverpass')
#db.session.commit()
app_security = Security(app, user_datastore)
principals = Principal(app)

#handle file uploads using flask-uploads
#http://pythonhosted.org/Flask-Uploads/
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = '/var/www/roverpass/roverpass/static/photos/'
configure_uploads(app, (photos))

#MAIL using flask-mail
#http://pythonhosted.org/flask-mail/
sys.stdout = sys.stderr
#info@roverpass.com
#suluwesi!123
app.config.update(
    #EMAIL SETTINGS
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME = 'info@roverpass.com',
    MAIL_PASSWORD = 'suluwesi!123',
    DEFAULT_MAIL_SENDER = 'info@roverpass.com',
    SECURITY_POST_LOGIN_VIEW='/login_success')
#patches requests to only allow 16Mb (for file uploads)
patch_request_class(app)

#configure Mail
mail = Mail(app)


#create_role commits automatically
#db.session.commit()

#create permissions here:
access_sales = Permission(RoleNeed('sales_user'))
edit_campground = Permission(RoleNeed('sales_user'), RoleNeed('campground_owner'))
upload_media = Permission(RoleNeed('sales_user'), RoleNeed('campground_owner'), RoleNeed('base_user'))
leave_review = Permission(RoleNeed('base_user'))

### SOCIAL ###
#Social(app, SQLALChemyConnectionDatastore(db, Connection))


### STRIPE ###
stripe_keys = {
    'secret_key': 'sk_test_ItmAZcNRVDbslaoTkeYkh3Sk',
    'publishable_key': 'pk_test_KAiF24eRh768FTHaTxAiQi3Y'
}

stripe.api_key = stripe_keys['secret_key']


@app_security.login_context_processor
def login_context_processor():
    form = LoginForm()
    return dict(form=form)

# LOGIN #
@login_manager.user_loader
def load_user(id):
    try:
        user = User.objects.filter_by(id=id).first()
        return user
    except:
        return AnonymousUser

@login_manager.request_loader
def load_user_from_request(request):
    #try to login with api (request.args.get('api_key'))
    #then try to login with normal email
    pass

@app.route('/') 
def index():
    """
    Displays the splash page, along with any messages passed along.
    If you are going to redirect to this page, you pass a message.
    """
    if current_user.is_authenticated():
        user = current_user
    else:
        user = None
    try:
        message = request.args['message']
    except:
        message = None

    return render_template('splash.html', message=message, key=stripe_keys['publishable_key'], user=user)
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login_success')
def login_success():
    return ''

@app.route('/logout')
def logout():
    # Remove the user information from the session
    logout_user()

    pop_login_session()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return redirect(request.args.get('next') or '/')

# USERS #

## Login is baked into flask-security. If you need to edit the template, find it in "templates/security/login_user.html".
## There is a full list of templates built into flask-security in their docs, but I do not use any of them.
@app.route('/resend_password', methods=['GET', 'POST'])
def resend_password():
    form = ResendPasswordForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
        except:
            user = None
        print user
        if user == None:
            return render_template('notification.html', notice='Sorry, a user was not found with that email. Please call sales if you have any more questions.')
        
        else:
            new_password= user.generate_new_password()
            user.password = encrypt_password(new_password)
            db.session.commit()
            print new_password
            print user.password

            msg = Message('Your new Roverpass password', sender='info@roverpass.com', recipients=[user.email], html=render_template('emails/resend_password.html', user=user, new_password=new_password))
            mail.send(msg)
            return render_template('notification.html', notice='We have emailed you a new password.')
    else:
        return render_template('resend_password.html', form=form)

@app.route('/profile/<id>')
def user_profile(id):
    try:
        user = User.query.filter_by(id=id).first()
    except:
        return redirect(url_for('index', message='That user was not found.'))

    if not current_user == user:
        return redirect(url_for('index', message='You do not have access to that page.'))

    if user == None:
        return redirect(url_for('index', message='That user was not found.'))

    try:
        slug = Campground.query.filter_by(id=user.camp_owned).first().slug
    except:
        slug = None

    return render_template('user_profile.html', user=user, slug=slug)

@app.route('/profile/<id>/change_password', methods=['GET', 'POST'])
def change_password(id):
    form = ChangePasswordForm()
    user = User.query.filter_by(id=id).first()
    
    if not current_user == user:
        return redirect(url_for('index', message='You do not have access to that page.'))
        
    if form.validate_on_submit():
        if verify_password(form.old_password.data, user.password):
            user.password = encrypt_password(form.new_password.data)
            db.session.commit()
            return render_template('notification.html', notice='Your password has been updated.')
        else:
            return render_template('change_password.html', form=form, user=user, message='Incorrect old password. Please try again.')

    else:
        return render_template('change_password.html', user=user, form=form)


@app.route('/campground/<slug>/create_owner', methods=['GET', 'POST'])
@app.route('/campground/<slug>/create_owner_opt', methods=['GET', 'POST'])
def create_owner(slug):
    form = UserForm()
    campground = Campground.query.filter_by(slug=slug).first()
    #if the user already owns the campground
    if current_user.has_role('campground_owner') and current_user.camp_owned == campground.id:
        return redirect('/campground/'+slug+'/opt_in')
    if form.validate_on_submit():
        print 'valid'
        if User.query.filter_by(email=form.email.data).first() == None:
            user = user_datastore.create_user(email=form.email.data,
                    password=encrypt_password(form.password.data),
                    active=True, first_name = form.full_name.data.split()[0],
                    last_name = form.full_name.data.split()[1])
            user.camp_owned = campground.id
            db.session.commit()
            user_datastore.add_role_to_user(user, Role.query.filter_by(name='base_user').first())
            user_datastore.add_role_to_user(user, Role.query.filter_by(name='campground_owner').first())
            db.session.commit()
            login_user(user)
            print request.url
            if 'create_owner_opt' in request.url:
                return redirect('/campground/'+slug+'/opt_in')
            else:
                return render_template('notification.html', user=user, notice='Thank you for creating an account. You may now edit your campgrounds information, or Opt-In to Roverpass!')
        else:
            return render_template('notification.html', notice='A user with that email already exists. Forgot your password? Click forgot password.')
    else:
        print form.errors
        if 'create_owner_opt' in request.url:
            return render_template('create_owner_to_opt.html', campground=campground, message='Thank you! Please create an account.', form=form)
        else:
            return render_template('create_owner.html', campground=campground, message="Thank you! Please create an account.", form=form)

@app.route('/campground/<slug>/delete_image/<number>', methods=['GET', 'POST'])
def delete_image(slug, number):
    #Deletes an image, given a campground slug and image number
    campground = Campground.query.filter_by(slug=slug).first()
    campground.media.remove(campground.media[int(number)])
    db.session.commit()
    return render_template('notification.html', extra_class='delete_image', notice='This image has been removed.')

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    print 'called!'
    form = UserForm()
    if request.method=='POST' and form.validate():
        print request.form['stripeToken']
        if User.query.filter_by(email = form.email.data).first() == None:
            print 'creating user'
            #try charging first.
            renew = False
            expiration_date = ''
            amount = 4995
            print form.roverpass_selection.data
            if form.roverpass_selection.data == '1yr':
                amount = 4995
                expiration_date = datetime.today() + timedelta(days=365)
            if form.roverpass_selection.data == '1yr-R':
                amount = 4600
                expiration_date = datetime.today() + timedelta(days=365)
                renew = True
            if form.roverpass_selection.data == '2yr':
                expiration_date = datetime.today() + timedelta(days=730)
                amount = 8900
            if form.roverpass_selection.data == '3yr':
                amount = 13200
                expiration_date = datetime.today() + timedelta(days=1095)
            
            print request.form['stripeToken']
            customer = stripe.Customer.create(
                email=form.email.data,
                card=request.form['stripeToken']
            )
            print customer
            try :
                charge = stripe.Charge.create(
                    customer=customer.id,
                    amount=amount,
                    currency='usd',
                    description='Purchasing Roverpass Card',
                )
                print 'successfully charged'
                #create user object from user form data
                user = user_datastore.create_user(email=form.email.data,
                        password=encrypt_password(form.password.data),
                        active=True)
                print 'user created'
                #gather additional information from stripe portion of the user creation form
                user.address=form.address.data
                user.zip_code=form.zip_code.data
                user.city=form.city.data
                user.state=form.state.data
                user.renew = renew
                user.pass_expiration_date = expiration_date
                user.pass_purchase_date = datetime.today()
                print 'commited to db' 
                msg_to_info = Message(subject=str('ROVERPASS SHIPPING NOTICE'), sender='info@roverpass.com', html=render_template('emails/someone_bought_a_roverpass.html', today=datetime.today().strftime("%d %b, %Y"), email=user.email, address=user.address, roverpass_type=form.roverpass_selection.data, zip_code=user.zip_code, city=user.city, state=user.state, user=user), recipients=['info@roverpass.com'])
                msg_to_user = Message(subject=str('ROVERPASS SHIPPING NOTICE'), sender='info@roverpass.com', html=render_template('emails/user_activation.html', today=datetime.today().strftime("%d %b, %Y"), email=user.email, address=user.address, zip_code=user.zip_code, city=user.city, state=user.state, user=user), recipients=[user.email])
                mail.send(msg_to_info)
                mail.send(msg_to_user)
                print 'mail sent!'
                if not user.has_role('base_user'):
                    user_datastore.add_role_to_user(user, Role.query.filter_by(name='base_user').first())
                'about to commit'
                #commit everything
                db.session.commit()
                login_user(user)
                'commited!'
                return render_template('notification.html', notice='Thank you for creating an account, you have been logged in! A confirmation email has been sent to '+user.email+'.')
           
            except stripe.CardError, e:
                return redirect(url_for('index', message='Card information incorrect. Please try again.'))

        else:
            return render_template('notification.html', notice='A user with that email already exists. Have you forgotten your password? Click down below.')
    else:
        return render_template('create_user.html', user=None, form=form)

    return abort(500)

# SEARCH #
@app.route('/search/<state>', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search(state=None):
    """
    Performs a search using sqlalchemy-searchable. Allows for refinement via perk selection.
    """
    form = SearchForm()
    user = current_user
    if state is not None:
        for state_name, statecode in STATES:
            if statecode == state:
                state = state_name
        results = Campground.query.filter_by(state=state).all()
        pins = []
        sort_list = []
        final = []
        for camp in results:
            sort_list.append(camp.name)
        sort_list.sort()
        for name in sort_list:
            final.append(Campground.query.filter_by(name=name).first())
        return render_template('search.html', form=form, user=user, results=final)
    if request.method == 'POST' and form.validate():
        #gather the selected perks
        #due to wtforms not differentiating form fields (or at least providing a useful mechanism to do so),
        #i iterate through every instance of a form field and brutally determine its type.
        selected_perks = []
        for perk in form:
            #if it is not a boolean field, it is definitely not our guy,
            #also, those other guys? not our guy.
            if isinstance(perk.data, bool) and not perk.id == 'state' and not perk.id == 'roverpass_discount_only':
                if perk.data:
                    selected_perks.append(perk.id)
        #list comprehension to properly format each perk in the list (makes a new list of spaced-out perk names)
        selected_perks = [perk.replace('_', ' ').title() for perk in selected_perks]
        proper = []
        print selected_perks

        #query AND perk selection
        #remember, python defaults an empty list None->False
        #if it is this search, you must check and see that every perk of each campground is inside the list
        #of selected perks using python's set object
        if form.query.data and selected_perks:
            results = Campground.query.search(form.query.data).all()
            for campground in results:
                perks_list = []
                for perk in campground.perks:
                    perks_list.append(perk.perk_name)
                if set(selected_perks) <= set(perks_list):
                    proper.append(campground)

        #no query, only perks
        if not form.query.data and selected_perks:
            print 'refining by perk'
            results = Campground.query.all()[:1000]
            for campground in results:
                perks_list = []
                for perk in campground.perks:
                    perks_list.append(perk.perk_name)
                if  set(selected_perks) <= set(perks_list):
                    proper.append(campground)
            print proper

        #query only, no perk selection
        if form.query.data and not selected_perks:
            proper = Campground.query.search(form.query.data).all()
        
        #neither
        if not form.query.data and not selected_perks:
            proper = Campground.query.all()[:50]

        #if they selected a state
        states_filter = []
        if not form.state.data == 'None':
            for result in proper:
                if result.state == form.state.data:
                    states_filter.append(result)
        else:
            states_filter = proper

        #if they want only roverpass participants
        roverpass_discount_filter = []
        if form.roverpass_discount_only.data == True:
            for result in states_filter:
                if result.roverpass_member:
                    roverpass_discount_filter.append(result)
        else:
            roverpass_discount_filter = states_filter

        #due to SQLAlchemy storing tables as a proprietary data type, jinja cannot interpret the lists returned by, 
        #in this case, campground.media. therefore, create a list of display images with paralell indices to their campground
        media = [] #<-- URLs to the first image in campground.media
        sort_list = []
        final = []
        for camp in roverpass_discount_filter:
            sort_list.append(camp.name)
        sort_list.sort()
        for name in sort_list:
            final.append(Campground.query.filter_by(name=name).first())

        for camp in final:
            try:
                media.append(str(camp.media[0].url))
            except:
                media.append('/static/media/travco.jpg')
        return render_template('search.html', user=user, media=media, results=final, form=form)

    return render_template('search.html', user=user, form=form, results=None)


# CAMPGROUND & REVIEWS #

@app.route('/campground/<slug>', methods=['GET', 'POST'])
def view_campground(slug):
    """
    Campground profile view. Redirects to AngularJS powered inline editing page if user has the permissions required to edit a campground page.
    """

    campground = Campground.query.filter_by(slug=slug).first()
    if campground == None:
        abort(404)

    user = current_user
    if current_user.has_role('campground_owner') and current_user.camp_owned == campground.id:
        return redirect('/campground/'+slug+'/edit')
    try:
        address = json.loads(campground.address)['results'][0]['name']
    except:
        address = campground.address
    try:
        similar = Campground.query.filter_by(city=campground.city, state=campground.state).all()
        similar.remove(campground)
        if len(similar) == 0:
            similar = Campground.query.filter_by(state=campground.state).all()
            similar.remove(campground)
    except:
        similar = None
    if len(campground.reviews) != 0:
        total = 0
        review_average = 0
        for review in campground.reviews:
            total += review.stars
        review_average = total/(len(campground.reviews))
        review = campground.reviews[len(campground.reviews)-1]
    else:
        review_average = 0
        review = None

    message = None
    #calculate review average

    if current_user.has_role('campground_owner') and current_user.camp_owned == campground.id:
        return render_template('campground.html', key=stripe_keys['publishable_key'], user=user, campground=campground, 
                                media=list(Media.query.filter_by(camp_id=campground.id).all()), 
                                similar=similar, review=review, review_average=review_average, message=message, 
                                name=campground.name)
        #return redirect(url_for('edit_campground', slug=slug))
    elif campground:
        if request.args:
            message = request.args['message']
        else:
            message = None

        if user.is_anonymous():
            user = None
        return render_template('campground.html', user=user, campground=campground, 
                                media=Media.query.filter_by(camp_id=campground.id).all(), 
                                similar=similar, review=review, review_average=review_average, message=message, 
                                name=str(campground.name).replace('{','').replace('"','').replace('}',''), 
                                address=address)
    return render_template('404.html')

@app.route('/campground/<slug>/reviews')
def display_reviews(slug):
    """
    Displays a list of all reviews for a campground.
    """
    campground = Campground.query.filter_by(slug=slug).first()
    if campground:
        return render_template('review_list.html', campground=campground, user=current_user, reviews=campground.reviews)
    else:
        abort(404)

@app.route('/campground/<slug>/leave_review', methods=['GET', 'POST'])
@login_required
def leave_review(slug):
    form = ReviewForm()
    campground = Campground.query.filter_by(slug=slug).first()
    if campground and form.validate():
        campground.reviews.append(Review(stars=form.num_stars.data, review_text=form.review_text.data))
        db.session.commit()
        return render_template('notification.html', notice='Review posting a success! Thank you.')
    elif not campground:
        abort(404)
    return render_template('leave_review.html', campground=campground, form=form)

@app.route('/campground/<slug>/upload_background_image', methods=['GET', 'POST'])
@app.route('/campground/<slug>/upload_photo', methods=['GET', 'POST'])
def upload_photo(slug):
    #this functions DRYly handles both user media upload and background image upload by campground owners.
    try:
        campground = Campground.query.filter_by(slug=slug).first()
    except:
        return redirect(url_for('index', notice='Campground not found. Try our search!'))
    form = PhotoUploadForm()
    user = current_user
    if  not current_user.is_authenticated():
        return render_template('notification.html', notice='You must logged in to do that!')
    if form.validate_on_submit() and 'photo' in request.files:
        #if they are uploading a background image
        print request.path
        if 'upload_background_image' in request.path:
            print 'inside'
            try: 
                filename= photos.save(request.files['photo'], folder=slug, name=user.email+str(random.randrange(1000))+'.')
                print 'whoo it worked'
                print filename
            except UploadNotAllowed, e:
                return redirect(url_for('edit_campground', slug=slug, message='That kind of file is not allowed.'))

            if filename is None:
                abort(500)

            campground.background_image = photos.url(filename)
            db.session.commit()

        #otherwise...
        else:
            try:
                filename = photos.save(request.files['photo'], folder=slug, name=user.email+str(random.randrange(1000))+'.')
            except UploadNotAllowed, e:
                return redirect(url_for('view_campground', slug=slug, message='That kind of file is not allowed.'))
            if filename is None:
                abort(500)
            
            campground.media.append(Media(url=photos.url(filename)))
            db.session.commit()

        return redirect(url_for('view_campground', slug=slug, message='File uploaded successfully.'))
    elif form.errors:
        print form.errors
        return redirect(url_for('view_campground', slug=slug, message='Invalid file.'))

    elif 'upload_background_image' in request.path:
        return render_template('upload_background_image.html', campground=campground, user=user, form=form)

    else:
        return render_template('upload_photo.html', campground=campground, user=user, form=form)

# CLAIM & OPT IN #

@app.route('/campground/<slug>/request_code', methods=['GET', 'POST'])
def request_verification_code(slug):
    form = RequestVerificationCodeForm()
    campground = Campground.query.filter_by(slug=slug).first()
    if form.validate_on_submit():
        msg = Message(subject=str('Verification Code Requested!'), sender='info@roverpass.com', html=render_template('emails/verification_code_request.html', name=form.name.data, email=form.email.data, phone_number=form.phone_number.data, comments=form.additional_comments.data, campground=campground), recipients=['info@roverpass.com'])
        mail.send(msg)
        return render_template('notification.html', notice='Thank you for requesting your code! We will be in contact with you shortly.')
    elif form.errors:
        print form.errors
        return render_template('notification.html', notice=str('Sorry, something went wrong: '+form.errors.itervalues().next()[0]+' Please go back and try again.'))
    else:
        return render_template('request_verification_code.html', form=form, campground=campground)

@app.route('/campground/<slug>/claim-opt', methods=['GET', 'POST'])
@app.route('/campground/<slug>/claim', methods=['GET', 'POST'])
def claim_campground(slug):
    form = VerificationNumberForm()
    try:
        user = User.query.filter_by(id=current_user.id).first()
    except:
        user = None

    campground = Campground.query.filter_by(slug=slug).first()
    print request.url
    if form.validate_on_submit():
        #someone has already claimed the campground
        if form.code.data == campground.verification_code and len(User.query.filter_by(camp_owned=campground.id).all()) != 0:
            print User.query.filter_by(camp_owned=campground.id).all()
            print campground.id
            return render_template('notification.html', notice='Someone has already claimed this campground.')

        #no user
        if form.code.data == campground.verification_code and user == None:
            print 'redirecting to create owner'
            print request.url
            if 'claim-opt' in request.url:
                return redirect('/campground/'+slug+'/create_owner_opt')
            else:
                return redirect(url_for('create_owner', slug=slug))

        #user already logged in
        elif form.code.data == campground.verification_code:
            user_datastore.add_role_to_user(user, Role.query.filter_by(name='campground_owner').first())
            user.camp_owned = campground.id
            print request.url
            if 'claim-opt' in request.url:
                return redirect('/campground/'+slug+'/create_owner/opt')
            return render_template('notification.html', notice="Thank you for claiming this campground! You may now edit it, or opt in to the Roverpass program!")

        #incorrect verification code
        else:
            return render_template('notification.html', notice='You have entered an incorrect validation code.')
    else:
        print 'generic'
        if 'claim-opt' in request.url:
            return render_template('claim_campground_to_opt.html', form=form, user=user, campground=campground)
        return render_template('claim_campground.html', form=form, user=user, campground=campground)

@app.route('/campground/<slug>/opt_in', methods=['GET', 'POST'])
def opt_in(slug):
    """
    Form for opting into roverpass.
    Prompt for verification code, then redirect to create user.
    If user exists, add that campground to their campground owned column and go directly to opt in form.
    After full completion toggle campground.roverpass_member to true. This will update pricing info as well on the campgrounds view page.
    """
    form = OptInForm(request.form)
    print form.data
    print request.form

    try:
        user = User.query.filter_by(email= current_user.email).first()
    except:
        user = None

    campground = Campground.query.filter_by(slug=slug).first()

    if not campground:
        return redirect(url_for('index', user=user, message='Sorry, that campground was not found.'))

    if not user or user.camp_owned != campground.id:
        return redirect('/campground/'+slug+'/claim-opt')

    if request.method=='POST' and form.validate():
        if not form.agree_to_terms.data:
            return render_template('opt_in.html', user=current_user, campground=campground, form=form, message='You must agree to the terms.')
        #if not user.has_role('campground_owner') and form.validate():
        #    user_datastore.add_role_to_user(user, Role.query.filter_by(name='campground_owner'))
        #    user.camp_owned = campground.id
        #    db.session.commit()
        #    return render_template('opt_in.html', user=user, campground=campground, form=form)
        #perform relevant campground updates
        campground.name = form.campground_name.data
        campground.formatted_address = form.address.data + ', ' + form.city.data + ', ' + form.state.data
        campground.address = form.address.data
        campground.city = form.city.data
        campground.state = form.state.data
        campground.discount_percentage = form.discount_percentage.data
        campground.roverpass_member = True
        campground.description = form.description.data
	campground.opt_in_date = datetime.today()

        #add additional perks; since WTForms provides no useful way of distinguishing 
        #field types, I will simply use the fact that there are 11 preceding fields (including CSRF)
        for field in form.data.items()[12:len(form.data.items())-1]:
            if form.data[field[0]] == True:
                perk = Perk(perk_name=field[0].replace('_', ' ').title())
                campground.perks.append(perk)

        #perform relevant user updates
        user.signature = form.signature.data
        user.phone_number = form.contact_phone_number.data

        db.session.commit()

        msg = Message(subject=str('Roverpass Opt-In Agreement Copy : '+campground.name), sender='info@roverpass.com', html=render_template('opt_in_success.html', today=datetime.today().strftime("%d %b, %Y"), form_data=form.data, user=user, campground=campground), recipients=['info@roverpass.com', user.email ])
        with app.open_resource("/var/www/roverpass/roverpass/static/agreement/roverpass_agreement.pdf") as fp:
            msg.attach("roverpass_agreement.pdf", "application/pdf", fp.read())
        mail.send(msg)

        return render_template('notification.html', notice='Thank you for Opting In! We have sent you a confirmation email, including a copy of the contract.')

    elif request.method=='GET':
        if not (user.has_role('campground_owner') and user.camp_owned == campground.id) or user==None:
            form = VerificationNumberForm()
            return render_template('claim_campground_to_opt.html', user=None, form=form, campground=campground)

        if current_user.has_role('campground_owner') and user.camp_owned == campground.id:
            return render_template('opt_in.html', user=current_user, campground=campground, form=form)
    else:
        return render_template('opt_in.html', user=current_user, campground=campground, form=form)

@app.route('/campground/<slug>/edit', methods=['GET']) #get handler: displays edit page if you have the right role & it's your campground
@app.route('/campground/<slug>/edit/<edit_type>/<new_data>', methods=['POST']) #handles receiving and updating of new data
def edit_campground(slug, edit_type=None, new_data=None):
    #get the campground
    campground = Campground.query.filter_by(slug=slug).first()
    if request.method == 'GET':
        if current_user.camp_owned == campground.id:
            similar = Campground.query.filter_by(state=campground.state).all()
            similar.remove(campground)
            return render_template('campground_edit.html', user=current_user, similar=similar, media=Media.query.filter_by(camp_id=campground.id).all(), campground=campground)
        else:
            return redirect(url_for('view_campground', slug=campground.slug, message='You do not have rights to edit this campground.'))
    else:
        if new_data == '' or new_data is None:
            return redirect(url_for('view_campground', slug=campground.slug, message='That field cannot be blank.'))

        if edit_type == 'website':
            ##do it
            print request.form
            website = request.form['website']
            if website[0:7] is not 'http://':
                website = 'http://'+website
            campground.website = website

        if edit_type == 'description':
            print request.form
            description = request.form['description']
            print description
            campground.description = description

        if edit_type == 'price':
            campground.price = new_data

        if edit_type == 'phone_number':
            campground.phone_number = new_data

        if edit_type == 'name':
            campground.name = new_data

        if edit_type == 'address':
            campground.address = new_data
        if edit_type == 'state':
            campground.state = new_data

        db.session.commit()
    return ''

@app.route('/sales/users', methods=['GET', 'POST'])
@roles_required('sales_user')
def sales_users():
    return render_template('sales_users.html', users=User.query.all(), campgrounds=None, num_campgrounds=Campground.query.order_by('-id').first().id)

@app.route('/sales/<page>', methods=['GET', 'POST'])
@login_required
@roles_required('sales_user')
def sales(page=1):
    #if not current_user.has_role('sales'):
    #   abort(404)
    #else:
    num_campgrounds = Campground.query.order_by('-id').first().id
    campgrounds_opt_in = len(Campground.query.filter_by(roverpass_member=True).all())
    query = db.session.query(Campground)
    form = SearchForm()
    form.state.data = 'Texas'

    if request.method == 'GET':
        num_campgrounds = Campground.query.order_by('-id').first().id
        #display 100 campgrounds per page
        try:
            campgrounds = Campground.query.order_by(Campground.id).filter(Campground.id > (int(page)-1)*500).limit(500)
            print (campgrounds.all() == None)
            #campgrounds_opted_in = campgrounds.filter(Campground.id >= int(page)*500).filter_by(roverpass_member=True).limit(500)

            return render_template('sales.html', users=User.query.all(), page_num=page, form=form, campgrounds=campgrounds.all(), num_campgrounds=num_campgrounds, campgrounds_opt_in=campgrounds_opt_in)
        except:
            campgrounds = Campground.query.filter_by(state=str(page).title())
            print (campgrounds.all() == None)
            #campgrounds_opted_in = campgrounds.filter(Campground.query.filter_by(state=page)).filter_by(roverpass_member=True)
            return render_template('sales.html', users=User.query.all(), page_num=page, form=form, campgrounds=campgrounds.all(), num_campgrounds=num_campgrounds, campgrounds_opt_in=campgrounds_opt_in)
    
    elif request.method=='POST' and form.validate():
        if form.query.data:
            results = Campground.query.search(form.query.data).all()
            return render_template('sales.html', users=User.query.all(), page_num=page, form=form, num_campgrounds=num_campgrounds, campgrounds=results, campgrounds_opt_in=campgrounds_opt_in)
    else:
        return render_template('sales.html', users=User.query.all(), page_num=page, form=form, campgrounds=None, num_campgrounds=num_campgrounds, message=form.errors, campgrounds_opt_in=campgrounds_opt_in)


@app.route('/festivals')
def festivals():
    return render_template('base.html')

@app.route('/benefits')
def benefits():
    return render_template('member_benefits.html')
###ERROR HANDLING###
@app.errorhandler(403)
def permissionsRequired(error):
    return redirect(url_for('index', user=current_user, message='You must own the campground to do that.'))

@app.errorhandler(404)
def pageNotFound(error):
    return redirect(url_for('index', user=current_user, message='That page was not found.'))

@app.errorhandler(500)
def server_error(error):
    return redirect(url_for('index', user=current_user, message='Whoops! Something went wrong. We have been notified and will fix it. Please contact us at info@roverpass.com if you have an urgent need.'))


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
