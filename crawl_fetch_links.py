from urllib.request import urljoin
import validators
from validators import ValidationFailure
from bs4 import BeautifulSoup
import requests
from urllib.request import urlparse
import csv
import logging
from flask import Flask , request
from flask_cors import CORS
import os
import re

#########################################################################################
d_app = Flask(__name__)
CORS(d_app)

# Make the archive for dumping csv-links in local folder
if not os.path.isdir('URL_links_dump'):
    os.mkdir('URL_links_dump')

invalid_url_text = "You have entered an invalid URL. Try again with a valid URL"
error_text = "An error occured while crawling. Check the server console for details or try searching with another URL"

#########################################################################################

### URL validator function
def url_validate(url_string: str) -> bool:
    result = validators.url(url_string)
    if isinstance(result, ValidationFailure):
        return False
    return result

#### Nested functions for fresh initialzation of variables on each call
def crawler(input_url , depth):
	#### Intiating variables here so that on each call , variables are reset
	#### using sets here for internal and external links storing
	links_internal = set()
	links_external = set()
	#### URL links dumplist
	dumplist = []

	#########################################################################################
	def link_crawler(input_url):
		temp_urls = set()
		current_url_domain = urlparse(input_url).netloc
		beautiful_soup_object = BeautifulSoup(requests.get(input_url).content, "lxml")
		####working on the anchor tags here
		for anchor in beautiful_soup_object.findAll("a"):
			href = anchor.attrs.get("href")
			if(href != "" or href != None):
				href = urljoin(input_url, href)
				href_parsed = urlparse(href)
				href = href_parsed.scheme
				href += "://"
				href += href_parsed.netloc
				href += href_parsed.path
				final_parsed_href = urlparse(href)
				is_valid = bool(final_parsed_href.scheme) and bool(
					final_parsed_href.netloc)
				if is_valid:
					if current_url_domain not in href and href not in links_external:
						#print("External links:{}".format(href))
						links_external.add(href)
						if href not in dumplist and 'http' in href:
							dumplist.append(href)
					if current_url_domain in href and href not in links_internal:
						#print("Internal links:{}".format(href))
						links_internal.add(href)
						temp_urls.add(href)
						if href not in dumplist and 'http' in href:
							dumplist.append(href)

		return temp_urls

	#########################################################################################
	print("\nCrawling on the URl:", input_url.strip(), " at depth:", depth)
	if (depth == 0):
		print("Internal links at depth 0 is the link itself - {}".format(input_url.strip()))
		dumplist.append(input_url.strip())

	elif (depth == 1):
		link_crawler(input_url.strip())

	else:  ######## using the BFS here - using a queue for implementing breadth wise extraction of links
		queue = []
		queue.append(input_url.strip())
		for j in range(depth):
			for count in range(len(queue)):
				url = queue.pop(0)
				urls = link_crawler(url)
			for i in urls:
				queue.append(i)

	## Dump the links parsed into a csv
	striped_url = re.sub('[^a-zA-Z0-9 \n\.]', '', input_url)
	csv_file_path = 'URL_links_dump/' + striped_url + " depth." + str(depth) + ".csv"

	with open(csv_file_path, 'a+') as csv_file:
		writer = csv.writer(csv_file)
		i = 1
		for item in dumplist:
			writer.writerow([i, item])
			i += 1

	print('Success! Find the csv file at : ', csv_file_path)
	print('Total links extracted:', len(dumplist) , '\n')
	return dumplist

@d_app.route('/crawl', methods=['POST'])
def initiate_crawler():
	data = request.json
	# The link to parse and the depth upto which
	# the crawler shall parse
	payload_url = data['url']
	payload_depth = abs(int(data['depth'])) ### Check for abs & integer

	try:
		if(url_validate(payload_url.strip())):
			#### Initiate the crawler using the payload URL and depth after validating URL
			response = crawler(payload_url , payload_depth)
			return {"status": True, "value": response}
		else:
			return {"status": False , "value":invalid_url_text}

	except:
		logging.exception('')
		return {"status": False , "value":error_text}

if __name__ == '__main__':
    d_app.run(host='0.0.0.0', port='5000')