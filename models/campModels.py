from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
from kickstart import *
from slugify import slugify
import hashlib, random, requests
from sqlalchemy_searchable import make_searchable, SearchQueryMixin
from sqlalchemy_utils.types import TSVectorType
	
#from sqlalchemy_imageattach.entity import Image, image_attachment
"""
This contains all the database objects required for a Campground. This includes Reviews and Media objects.
"""

make_searchable()


class CampgroundQuery(BaseQuery, SearchQueryMixin):
    pass

class Campground(db.Model):
	"""
	campgrounds are the foundation of Roverpass. They are RV sites.
	This is the model from which profile pages are derived; it is also the access point for reviews.
	"""
	query_class = CampgroundQuery
	__tablename__ = 'campground'

	id = db.Column(db.Integer(), primary_key=True, unique=True)
	name = db.Column(db.String())
	location = db.Column(db.String())
	city = db.Column(db.String())
	description = db.Column(db.String())
	opt_in_date = db.Column(db.DateTime)
	roverpass_member = db.Column(db.Boolean())
	phone_number = db.Column(db.String())
	address = db.Column(db.String())
	num_hookups = db.Column(db.Integer())
	discount_percentage = db.Column(db.Integer())
	formatted_address = db.Column(db.String())
	state = db.Column(db.String())
	slug = db.Column(db.String())
	price = db.Column(db.Integer())
	discount_price = db.Column(db.Integer())
	website = db.Column(db.String())
	verification_code = db.Column(db.String(6))
	background_image = db.Column(db.String())
	reviews = db.relationship('Review', backref=db.backref('campground'))
	perks = db.relationship('Perk', backref=db.backref('campground'))
	media = db.relationship('Media', backref=db.backref('campground'))
	#searchable fields
	search_vector = db.Column(TSVectorType('name', 'state', 'city'))
	#pictures = image_attachment('Media')

	def add_perks(perks):
		for perk in perks:
			if perk[1] == 'True':
				this_perk = Perk(perk_name = perk[0], camp_id = self.id)

	def generate_slug(self):
		"""
		Returns a properly cleaned slug for URL generation, based on name
		also: generates verification code and calculates discounted price
		"""
		self.discount_percentage = 40
		#moved slug generation to crawlers.py
		self.slug = slugify(unicode(self.name))
		self.discount_price = int(self.price * (self.discount_percentage)/100)
		self.verification_code = hashlib.sha224(str(random.randrange(100000))).hexdigest()[:6]
		return slugify(unicode(self.name))

class Perk(db.Model):
	"""
	A perk is a benefit provided by the campground. Many-to-One to campground.
	"""
	__tablename__ = 'perks'

	id = db.Column(db.Integer, primary_key=True)
	perk_name = db.Column(db.String(80))
	camp_id = db.Column(db.Integer, db.ForeignKey('campground.id'))

	def __repr__(self):
		return self.perk_name

	def __init__(self, perk_name):
		self.perk_name = perk_name

class Media(db.Model):
	"""
	Image-only media to display on campground site.
	"""
	id = db.Column(db.Integer, primary_key=True)
	camp_id = db.Column(db.Integer, db.ForeignKey('campground.id'))
	url = db.Column(db.String())
	__tablename__ = 'media'

class Review(db.Model):
	"""
	Users will have Reviews. Also a Many-To-One with campground.
	"""
	__tablename__ = 'reviews'
	id = db.Column(db.Integer, primary_key=True)
	stars = db.Column(db.Integer)
	review_text = db.Column(db.Text())
	#db relationship
	camp_id = db.Column(db.Integer, db.ForeignKey('campground.id'))
