from boiler import *

for camp in Campground.query.all():
	if len(Campground.query.filter_by(slug=camp.slug).all()) != 1:
		camp.slug = slugify(unicode(camp.name+camp.city))
		db.session.commit()