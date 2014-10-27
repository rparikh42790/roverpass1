#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/roverpass/roverpass/")
sys.path.append('/var/www/roverpass/roverpass/models')
sys.path.append('/var/www/roverpass/roverpass/forms')

from boiler import app as application
