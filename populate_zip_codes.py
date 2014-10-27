from xlrd import *
from os import getcwd

zip_book = open_workbook('/var/www/roverpass/roverpass/static/zip_code_database.xls').sheets()[0]
zip_master = {}
zips_for_state = []
#there are 62 possible zip code locations
state_index = 0
index = 0
for count in range(61):
	stateCode = zip_book.cell(index, 1).value
	while zip_book.cell(index, 1).value is stateCode:
		zips_for_state.append(str(int(zip_book.cell(index, 0).value)))
		index+=1
	zip_master[stateCode] = zips_for_state
	zips_for_state = []