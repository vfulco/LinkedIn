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
gdb = pd.read_csv('/Users/oliver/Desktop/LinkedIn/Fair_List_Data_Extraction.csv').fillna('')
cols = ['Name']
gdb = gdb[cols]

# construct dataframe
cols = ['GDB Name', 'LinkedIn Name', 'Contact', 'Full Title', 'Current','Location', 'Industry']
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

# Helper functions - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def same_gallery_check(arr1, arr2):
	for u in arr1:
		if any(u in t for t in arr2):
			return True
	return False

# Scraping logic - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  

search_a = 'https://www.linkedin.com/vsearch/f?type=all&keywords='
search_b = '&orig=GLHD&rsid=&pageKey=oz-winner&trkInfo=tarId%3A1460125406163&search=Search'

def navigate_pages(gallery):
	time.sleep(.5)

	# if not already present, refine search by adding 'Gallery'
	if ('Gall' not in gallery) & ('Gale' not in gallery):
		gallery = gallery + ' Gallery'
	
	driver.get(search_a + gallery.replace(' ','+') + search_b)

	global at_least_one_contact
	at_least_one_contact = False
	global pages
	pages = 0

	search_people(gallery)


def search_people(gallery):
	time.sleep(2)

	global contact_table
	global pages

	time.sleep(1)

	people = driver.find_elements_by_xpath('//div[@id="results-container"]//li[contains(@class, "people")]')

	search_results_page = driver.current_url

	# look in search results for contacts currently working at the gallery
	for x in range(0, len(people)):
		time.sleep(1)

		people = driver.find_elements_by_xpath('//div[@id="results-container"]//li[contains(@class, "people")]')

		try:
			driver.find_element_by_class_name('dismiss').click()
		except Exception:
			pass

		try:
			name = people[x].find_element_by_class_name("main-headline")
		except Exception:
			continue # if it's an ad or company profile
		

		try:
			description = people[x].find_element_by_class_name('description').text
		except Exception:
			pass

		if ' at ' in description:
			company = description.split(' at ')[1]
		elif ' for ' in description:
			company = description.split(' for ')[1]
		elif ' of ' in description:
			company = description.split(' of ')[1]
		else:
			company = description

		gallery_name_split = gallery.split(' ')
		# remove word - gallery
		gallery_name_split = [s for s in gallery_name_split if ('Gall' not in s) & ('Gale' not in s)]
		company_name_split = company.split(' ')


		try:
			labels = people[x].find_elements_by_class_name('label')
			labels.pop()
			for y in range(0, len(labels)):
				if labels[y].text == 'Current':
					title = people[x].find_elements_by_class_name('title')[y+1].text
					break
			if ' at ' in title:
				company2 = title.split(' at ')[1]
			elif ' for ' in title:
				company2 = title.split(' for ')[1]
			elif ' of ' in title:
				company2 = title.split(' of ')[1]
			else:
				company2 = title
		except Exception:
			title = 'xyxyxyxyxyxyyxyx'
			company2 = 'xyxyxyxyxyxyyxyx'
			pass

		words_to_check = ['Gall', 'Galer', ' Fine Art ', 'Contemporary', 'Museum']
		gallery_just_name = gallery.replace(' Gallery','')
		gallery_just_name = gallery.replace(' Galeri','')

		if (fuzz.ratio(gallery, company) > 80) | same_gallery_check(gallery_name_split, company_name_split) | (gallery_just_name in description):

			if ([word for word in words_to_check if(word in description)]==[]) & ([word for word in words_to_check if(word in title)]==[]):
				continue

			if (name.text == 'LinkedIn Member'):
				break

			profile_link = name.get_attribute("href")
			driver.get(profile_link)

			contact = scrape_data(gallery, company)

			driver.back()

			contact_table = contact_table.append(contact, ignore_index=True)
						
			global at_least_one_contact
			at_least_one_contact = True

		elif (fuzz.ratio(gallery, company2) > 80) | same_gallery_check(gallery_name_split, company2) | (gallery_just_name in title):

			if ([word for word in words_to_check if(word in description)]==[]) & ([word for word in words_to_check if(word in title)]==[]):
				continue

			if (name.text == 'LinkedIn Member'):
				break

			profile_link = name.get_attribute("href")
			driver.get(profile_link)

			contact = scrape_data(gallery, company2)

			driver.back()

			contact_table = contact_table.append(contact, ignore_index=True)
						
			at_least_one_contact = True

		elif [word for word in words_to_check if(word in description)]!=[]:

			if (name.text == 'LinkedIn Member'):
				break

			profile_link = name.get_attribute("href")
			driver.get(profile_link)

			contact = scrape_data('New Gallery', company)

			driver.back()

			contact_table = contact_table.append(contact, ignore_index=True)
						
			at_least_one_contact = True

	if at_least_one_contact & (pages < 2):

		driver.get(search_results_page)
		time.sleep(1.5)
	
		try:
			next_button = driver.find_element_by_xpath("//li[@class='next']/a")
			next_button.click()
			pages += 1
			time.sleep(2)
			search_people(gallery)
		except Exception:
			pass


def scrape_data(gallery, company):
	time.sleep(.5)

	contact_details = { 'GDB Name': gallery, 'LinkedIn Name': company, 'Contact': '', 'Full Title': '', 'Current': '','Location': '', 'Industry': '' }
	
	try:
		companies = driver.find_elements_by_class_name('current-position')
	except Exception:
		pass

	name = driver.find_element_by_class_name("full-name").text
	contact_details["Contact"] = name

	try:
		contact_details["Full Title"] = driver.find_element_by_class_name("title").text
	except Exception:
		pass

	try:
		contact_details["Current"] = driver.find_element_by_xpath('//tr[@id="overview-summary-current"]/td/ol/li/span/strong/a').text
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

for i in range(0, 50):
	try:
		navigate_pages(gdb['Name'][i])
		print i
	except Exception:
		continue

contact_table = contact_table[cols]
contact_table.to_csv('/Users/oliver/Desktop/LinkedIn/test.csv')
	