from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common import action_chains, keys
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import os,sys
from fuzzywuzzy import fuzz
reload(sys) 
sys.setdefaultencoding('utf8')


# Pandas Dataframes - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# read in gdb
gdb = pd.read_csv('/Users/oliver/Desktop/gdb-mar28/GDB_Apr-6.csv').fillna('')
cols = ['Name']
gdb = gdb[cols]

# construct dataframe
cols = ['GDB Name', 'LinkedIn Name', 'Contact', 'Full Title', 'Location', 'Industry', 'Title', 'Duration']
contact_table = pd.DataFrame(columns=cols)

# Log in to LinkedIn with Selenium - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

driver = webdriver.Firefox()
driver.get("https://linkedin.com")
driver.maximize_window()

email = 'oliverplunkett2015@u.northwestern.edu'
password = 'oliverrory9'
driver.find_element_by_id('login-email').send_keys(email)
driver.find_element_by_id('login-password').send_keys(password)
driver.find_element_by_name('submit').click()

wait = ui.WebDriverWait(driver, 3)
action = webdriver.ActionChains(driver)

# Scraping logic - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

search_a = 'https://www.linkedin.com/vsearch/f?type=all&keywords='
search_b = '&orig=GLHD&rsid=&pageKey=oz-winner&trkInfo=tarId%3A1460125406163&search=Search'

def navigate_pages(gallery):
	time.sleep(.5)

	# if not already present, refine search by adding 'Gallery'
	if 'Gallery' not in gallery:
		gallery = gallery + ' Gallery'
	
	driver.get(search_a + gallery.replace(' ','+') + search_b)

	global at_least_one_contact
	at_least_one_contact = False
	global pages
	pages = 0

	search_people(gallery)


def search_people(gallery):
	time.sleep(.5)

	global contact_table
	global pages

	wait.until(lambda driver: driver.find_element_by_class_name('result').is_displayed())
	people = driver.find_elements_by_class_name('result')

	# look in search results for contacts currently working at the gallery
	for i in range(0, len(people)):
		
		try:
			driver.find_element_by_class_name('dismiss').click()
		except Exception:
			pass

		try:
			name = driver.find_elements_by_class_name('result')[i].find_element_by_class_name('main-headline')
		except Exception:
			continue # if it's an ad or company profile

		try:
			description = driver.find_elements_by_class_name('result')[i].find_element_by_class_name('description').text
		except Exception:
			continue

		if ' at ' in description:
			company = description.split(' at ')[1]
		elif ' for ' in description:
			company = description.split(' for ')[1]
		elif ' of ' in description:
			company = description.split(' of ')[1]
		else:
			company = description

		print company

		if (name.text != 'LinkedIn Member') & (fuzz.ratio(gallery, company) > 80):

			i = i - 1

			profile_link = name.get_attribute("href")
			driver.get(profile_link)

			contact = scrape_data(gallery)

			driver.back()

			contact_table = contact_table.append(contact, ignore_index=True)
						
			global at_least_one_contact
			at_least_one_contact = True

	if at_least_one_contact & (pages < 2):
	
		try:
			next_button = driver.find_element_by_xpath("//li[@class='next']/a")
			next_button.click()
			pages += 1
			time.sleep(2)
			search_people(gallery)
		except Exception:
			pass


def scrape_data(gallery):
	time.sleep(.5)

	contact_details = { 'GDB Name': gallery, 'LinkedIn Name': gallery, 'Contact': '', 'Full Title': '', 'Location': '', 'Industry': '', 'Title': '', 'Duration': '' }
	
	companies = driver.find_elements_by_class_name('current-position')
	name = driver.find_element_by_class_name("full-name").text
	contact_details["Contact"] = name

	for i in range(0,len(companies)):

		company = companies[i].find_element_by_name('company')

		if company.text == gallery:

			contact_details["Name"] = company.text

			try:
				contact_details["Title"] = companies[i].find_element_by_tag_name('h4').text
			except Exception:
				continue			
			try:
				contact_details["Duration"] = companies[i].find_element_by_class_name("experience-date-locale").text
			except Exception:
				continue

	try:
		contact_details["Full Title"] = driver.find_element_by_class_name("title").text
	except Exception:
		pass

	try:
		contact_details["Location"] = driver.find_element_by_name("location").text
	except Exception:
		pass
	try:
		contact_details["Industry"] = driver.find_element_by_name("industry").text
	except Exception:
		pass	

	return contact_details

for i in range(0,200):
	try:
		navigate_pages(gdb['Name'][i])
	except Exception:
		continue

contact_table = contact_table[cols]
contact_table.to_csv('/Users/oliver/Desktop/LinkedIn/test.csv')
	