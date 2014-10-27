from boiler import *

def check_users_for_renew():
    for user in User.query.all():
        if (datetime.today() - user.pass_purchase_date).days == 335:
            msg = Message('Your Roverpass expires in 30 days', sender='info@roverpass.com', recipients=[user.email], html=render_template('emails/renew_pass.html', user=user,))
            mail.send(msg)
        elif (datetime.today() - user.pass_purchase_date).days == 365:
            user.pass_expired = true
            user.has_pass = false
            db.session.commit()
        if user.camp_owned is not None:
        	campground = Campground.query.filter_by(id=user.camp_owned).first()
        	if campground.roverpass_member == true:
	        	if (datetime.today() - campground.opt_in_date).days == 700:
	        		msg = Message('Your Roverpass account expires in 30 days', sender='info@roverpass.com', recipients=[user.email], html=render_template('emails/renew_opt_in.html', user=user, campground=campground))
	        		mail.send(msg)
	        	if (datetime.today() - campground.opt_in_date).days == 730:
	        		campground.roverpass_member = False
	        		db.session.commit()
	        		msg = Message('Your Roverpass account has expired.', sender='info@roverpass.com', recipients=[user.email], html=render_template('emails/opt_in_expired.html', user=user, campground=campground))
	        		mail.send(msg)
	        		
if __name__ == '__main__':
	check_users_for_renew()
