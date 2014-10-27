from boiler import *

for camp in Campground.query.all():
	camp.perks = list(set(camp.perks))
	db.session.commit()
