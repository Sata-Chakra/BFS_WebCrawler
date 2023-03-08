from urllib.request import urljoin
import validators
from validators import ValidationFailure
from bs4 import BeautifulSoup
import requests
from urllib.request import urlparse
import azure.functions as func

error_text = "An error occured while crawling. Check the server console for details or try searching with another URL"

#########################################################################################

#### Nested functions for fresh initialzation of variables on each call
def crawler(input_url:str , depth:int)-> list:
	#### Intiating variables here so that on each call , variables are reset
	#### using sets here for internal and external links storing
	links_internal = set()
	links_external = set()
	#### URL links dumplist
	dumplist = []
	dumplist.append(input_url)
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

	print('Total links extracted:', len(dumplist) , '\n')
	return dumplist

### URL validator function
def url_validate(url_string: str) -> bool:
    result = validators.url(url_string)
    if isinstance(result, ValidationFailure):
        return False
    return result

def main(req: func.HttpRequest) -> func.HttpResponse:
	req_body = req.get_json()
	logging.info('Python HTTP trigger function is processing a request')
	payload_url = str(req_body.get('url'))
	payload_depth = abs(int(req_body.get('depth')))
	print('main function is success')
	if(url_validate(payload_url)):
		response = crawler(payload_url, payload_depth)
		print({"status": True, "value": response})
		return func.HttpResponse({"status": True, "value": response},status_code=200)

	else:
		print({"status": True, "value": response})
		return func.HttpResponse(
			 {"status": False , "value":error_text},
			 status_code=200
		)
