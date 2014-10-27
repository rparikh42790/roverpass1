from flask.ext.wtf import Form
from wtforms import widgets, Field, FormField, TextField, FileField, SelectMultipleField, HiddenField, IntegerField, RadioField, SelectField, TextAreaField, BooleanField, PasswordField, validators
from wtforms.validators import Required, Regexp, Length, Email, NumberRange, ValidationError
from populate_zip_codes import zip_master

STATES = [('None', '---'), ('Alabama', 'AL'),('Alaska', 'AK'),('Arizona', 'AZ'),('Arkansas', 'AR'),('California', 'CA'),('Colorado', 'CO'),('Connecticut', 'CT'),('Delaware', 'DE'),
                    ('Florida', 'FL'),('Georgia', 'GA'),('Hawaii', 'HI'),('Idaho', 'ID'),('Illinois', 'IL'),('Indiana', 'IN'),('Iowa', 'IA'),
                    ('Kansas', 'KS'),('Kentucky', 'KY'),('Louisiana', 'LA'),('Maine', 'ME'),('Maryland', 'MD'),('Massachusetts', 'MA'),('Michigan', 'MI'),
                    ('Minnesota', 'MN'),('Mississippi', 'MS'),('Missouri', 'MO'),('Montana', 'MT'),('Nebraska', 'NE'),('Nevada', 'NV'),
                    ('New Hampshire', 'NH'),('New Jersey', 'NJ'),('New Mexico', 'NM'),('New York', 'NY'),('North Carolina', 'NC'),('North Dakota', 'ND'),
                    ('Ohio', 'OH'),('Oklahoma', 'OK'),('Oregon', 'OR'),('Pennsylvania', 'PA'),('Rhode Island', 'RI'),('South Carolina', 'SC'),
                    ('South Dakota', 'SD'),('Tennessee', 'TN'),('Texas', 'TX'),('Utah', 'UT'),('Vermont', 'VT'),('Virginia', 'VA'),
                    ('Washington', 'WA'),('West Virginia', 'WV'),('Wisconsin', 'WI'),('Wyoming', 'WY')]

def validate_zip_code(form, field):
    state = form.state.data
    state_code = STATES[[item[0] for item in STATES].index(state)][1]
    if state_code == '---':
        raise ValidationError('You must select a state.')
    if not str(field.data) in zip_master[state_code]:
        raise ValidationError('That zip code is not in the selected state.')

def validate_name(form, field):
    name = form.full_name.data
    if not (name.split()[0] and name.split()[1]):
        raise ValidationError('You must enter both your first and last name.') 

class UserForm(Form):
    full_name = TextField('Full Name', validators = [Required(message='You must enter your name.'), validate_name])
    email = TextField('Email', validators=[Required(message="The email field cannot be empty."), validators.Email(message="Invalid email.")])
    email_again = TextField('Email (again)', validators=[Required(message="The email verification field cannot be empty."), validators.Email(message="Invalid email address."),validators.EqualTo('email', message='Both emails must match.')])
    password = PasswordField('Password', widget=widgets.PasswordInput(hide_value=False), validators=[validators.Length(min=6, message='Password must be at least 6 characters long.'), Required(message="You must enter a password."), Regexp(r'[A-Za-z0-9@#$%^&+=]', message='Password contains invalid characters')])
    password_again = PasswordField('Password (again)', widget=widgets.PasswordInput(hide_value=False), validators=[validators.Length(min=6, message='Password must be at least 6 characters long.'), Required(message="You must enter a password."), validators.EqualTo('password', message='Both passwords must match.')])
    address = TextField('Address', validators=[Required(message="You must enter an address.")])
    city = TextField('City', validators=[Required(message='You must enter a city.')])
    state = SelectField('State', choices=STATES, validators=[Required(message='You must enter your state.')])
    zip_code = IntegerField('Zip Code', validators=[Required(message='You must enter your zip code.'), validate_zip_code])
    roverpass_selection = SelectField('Roverpass', choices=[('1yr', '1 Year - $49.95'), ('1yr-R', '1 Year with Auto-Renew - $46 (Save $3.95)'), ('2yr', '2 Years - $89 (Save $9.95)'), ('3yr', '3 Years - $132 (Save $15.95)')], validators=[Required(message='You must select your RoverPass')])
    agree = BooleanField('Agree To Terms', validators=[Required(message='You must agree to the terms of use.')])


    #card_number = TextField('Card Number', validators=[Required(message='You must enter your credit card number.'), validators.Length(min=16, max=16, message='Invalid credit card number.'), ])
    #cvc = TextField('CVC', validators=[Required(message='You must enter your card\'s security code.'), validators.Length(min=3, max=3, message="Invalid CVV")])
    #expiry_month = SelectField('Expiration Month', choices=MONTHS, validators=[Required(message='You must select your card\'s expiration month.')])
    #expiry_year = SelectField('Expiration Year', choices=YEARS, validators=[Required(message='You must select your card\'s expiration year.')])

class VerificationNumberForm(Form):
	code = TextField('Verification Code', validators=[Required()])

class ReviewForm(Form):
	num_stars = HiddenField('Number of stars', validators=[Required()])
	review_text = TextAreaField('Review', validators=[Required()])

class LoginForm(Form):
	email = TextField('Email', validators=[Required(message='The email field cannot be blank.'), validators.Email(message='Invalid email.')])
	password = PasswordField('Password', validators=[Required(message='The password field cannot be blank.')])
	remember = BooleanField('Remember Me')

class ResendPasswordForm(Form):
	email = TextField('Email', validators=[Required(message='You cannot leave this blank.'), validators.Email(message='Invalid email.')])

class ChangePasswordForm(Form):
	old_password = PasswordField('Old Password', validators=[Required()])
	new_password = PasswordField('New Password', validators=[Required()])
	new_password_again = PasswordField('New Password Again', validators=[Required()])

class RequestVerificationCodeForm(Form):
    name = TextField('Name', validators=[Required(message='You must enter your name.')])
    email = TextField('Email', validators=[validators.Email(message='Invalid email'), Required('You must enter your email.')])
    phone_number = TextField('Phone Number', validators=[Required(message='You must enter your phone number.')])
    additional_comments = TextAreaField('Additional Comments', validators=[])
    
class OptInForm(Form):
	#shit ton of perks
    free_upgrade = BooleanField('Free Upgrade', validators=[])
    special_parking = BooleanField('Special Parking', validators=[])
    free_swag = BooleanField('Free Swag', validators=[])
    free_food_or_drinks = BooleanField('Free Food or Drinks', validators=[])
    free_priority_entry = BooleanField('Free Priority Entry', validators=[])
    wireless_internet    = BooleanField('Wireless Internet', validators=[])
    fifty_amp = BooleanField('Fifty Amp', validators=[])
    thirty_amp = BooleanField('Thirty Amp', validators=[])
    twenty_amp = BooleanField('Twenty Amp', validators=[])
    fifteen_amp = BooleanField('Fifteen Amp', validators=[])
    sixty_amp = BooleanField('Sixty Amp', validators=[])
    eighty_amp = BooleanField('Eighty Amp', validators=[])
    atv = BooleanField('ATV', validators=[])
    bbq = BooleanField('BBQ', validators=[])
    biking = BooleanField('Biking', validators=[])
    boat_ramp = BooleanField('Boat Ramp', validators=[])
    cable_tv = BooleanField('Cable TV', validators=[])
    canoeing = BooleanField('Canoeing', validators=[])
    fishing = BooleanField('Fishing', validators=[])
    fire_rings = BooleanField('Fire Rings', validators=[])
    full_hookup = BooleanField('Full Hookup', validators=[])
    heated_pool = BooleanField('Heated Pool', validators=[])
    hiking = BooleanField('Hiking', validators=[])
    horseshoes = BooleanField('Horseshoes', validators=[])
    pets_welcome = BooleanField('Pets Welcome', validators=[])
    picnic_area = BooleanField('Picnic Area', validators=[])
    playground = BooleanField('Playground', validators=[])
    pool = BooleanField('Pool', validators=[])
    golf = BooleanField('Golf', validators=[])
    restaurant = BooleanField('Restaurant', validators=[])
    security = BooleanField('Security', validators=[])
    shuffleboard = BooleanField('Shuffleboard', validators=[])
    water = BooleanField('Water', validators=[])
    pool = BooleanField('Pool', validators=[])
    snack_bar = BooleanField('Snack Bar', validators=[])
    propane = BooleanField('Propane', validators=[])
    camping_kitchen = BooleanField('Camping Kitchen', validators=[])
    firewood = BooleanField('Firewood', validators=[])
    pavillion = BooleanField('Pavillion', validators=[])
    bike_rentals = BooleanField('Bike Rentals', validators=[])
    laundry = BooleanField('Laundry', validators=[])
    #owner/signer info
    campground_name = TextField('Campground Name', validators=[Required(message='This field cannot be blank.')])
    address = TextField('Campsite Address', validators=[Required(message='This field cannot be blank.')])
    city = TextField('Campsite City', validators=[Required(message='This field cannot be blank.')])
    state = SelectField('State', choices=STATES, validators=[Required(message='This field cannot be blank.')])
    description = TextAreaField('Description', validators=[Length(min=0, max=1000, message='Please enter a shorter description.')])
    contact_phone_number = TextField('Contact Phone Number', validators=[Required(message='This field cannot be blank.')])
    discount_percentage = IntegerField('Percentage Discount', validators=[Required(message='This field cannot be blank.'), NumberRange(min=40, max=100, message="You must enter a discount of at least 40%")])
    signature = TextField('Signature', validators=[Required(message='This field cannot be blank.')])
    code = TextField('Verification Code', validators=[Required()])
    agree_to_terms = BooleanField('Agree to Terms', validators=[Required(message='You must agree to the above terms.')])

class PhotoUploadForm(Form):
	photo = FileField('photo', validators=[Required()])
	
class SearchForm(Form):
    query = TextField('Query', validators=[])
    state = SelectField('State', choices=STATES, default='Any')
    roverpass_discount_only = BooleanField('Roverpass Discount Only')
    wireless_internet    = BooleanField('Wireless Internet', validators=[])
    fifty_amp = BooleanField('Fifty Amp', validators=[])
    thirty_amp = BooleanField('Thirty Amp', validators=[])
    twenty_amp = BooleanField('Twenty Amp', validators=[])
    fifteen_amp = BooleanField('Fifteen Amp', validators=[])
    sixty_amp = BooleanField('Sixty Amp', validators=[])
    eighty_amp = BooleanField('Eighty Amp', validators=[])
    cable_tv = BooleanField('Cable TV', validators=[])
    picnic_area = BooleanField('Picnic Area', validators=[])
    playground = BooleanField('Playground', validators=[])
    sewer = BooleanField('Sewer', validators=[])
    pull_thru_sites = BooleanField('Pull Thru Sites', validators=[])
    shade_trees = BooleanField('Shade Trees', validators=[])
    big_rig_access = BooleanField('Big Rig Access', validators=[])
    pets_allowed = BooleanField('Pets Allowed', validators=[])
    tents_allowed = BooleanField('Tents Allowed', validators=[])
    electric = BooleanField('Electric', validators=[])
    pool = BooleanField('Pool', validators=[])
    water = BooleanField('Water', validators=[])