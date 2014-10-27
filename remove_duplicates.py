from boiler import *

for camp in Campground.query.all():
	if len(Campground.query.filter_by(name=camp.name).all()) > 1:
		print 'removing duplicate '+camp.name
		db.session.delete(camp)
		db.session.commit()
