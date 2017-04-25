from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import re
import requests
import codecs

# python 3+
from bs4 import BeautifulSoup as BS
import statistics as stats
from urllib.parse import urlparse


# python 2.7
# from BeautifulSoup import BeautifulSoup as BS
# from urlparse import urlparse


#
# #
# # #
#
#  P U R P O S E
#  Compare Prices for Housing:
#   Example given only scrapes the room for rent
#
#  USAGE: use python3+
# # #
# #
#

# # Global Constants # #
# NONE

# # Global Settings # #
# NONE



def make_get_request(url):
    html = ""
    try:
        page = requests.get(url)
        if page.status_code != 200:
            raise Exception
        if page:
            html = page.text
            url = page.url
    except requests.exceptions.MissingSchema:
        print("Failed to GET page: " + url)
    return html

# Returns html text in list
def get_pages(urls):
    return [make_get_request(url) for url in urls]

# ie: given: "hey/there/buddy.php"
#     returns "buddy.html"
def get_filename(url, extension=".html"):
    s = url.split('/')
    for i in range(1, len(s)+1):
        end = s[-i]
        if len(end) > 0:
            return end.split('.')[0] + extension
    return "index" + extension

def get_filenames(urls):
    return [get_filename(url) for url in urls]

# given: "hey/there/buddy.php"
# returns: "hey/there"
def get_baseurl(url):
    return "/".join(url.split("/")[0:-1])

def get_baseurls(urls):
    return [get_baseurl(url) for url in urls]


def write_pages_to_files(pages, filenames, path="./"):
    for idx, filename in enumerate(filenames):
        make_dir_if_not_exists(path)
        with codecs.open(path + filename, "w", "utf-8-sig") as f:
            f.write(pages[idx][1])

def is_media(url):
    media=[".jpg", ".jpeg", ".png"]
    for m in media:
        if re.search(".*" + m, url):
            return True
    return False

# takes an html page string..
# uses beautiful soup to extract element attributes
# returns a list of image urls..
def get_img_urls(html):
    soup = BS(html)
    imgEls = soup.findAll('img')
    img_urls = []
    for el in imgEls:
        if el.get("src"):
            img_url = el["src"]
            if is_media(img_url):
                img_urls.append(img_url)
    return img_urls


# takes a list of html pages as strings
# returns a list of lists of image urls, see get_img_urls(page)
def get_img_urls_ll(pages):
    return [get_img_urls(html) for html in pages]

def make_dir_if_not_exists(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except:
        print("  Failed to check or create path '" + path + "' directory.")


# downloads image at url 'link' and stores in local "download_path"
# uses 'requests' lib to make a get request through a stream.
# does not throw, fails silently, prints to console on error or success.
def download_image(link, download_path):
    # Check or create download path
    make_dir_if_not_exists(download_path)

    # Download the image by making a get request through a stream
    try:
        img_response = None
        try:
            img_response = requests.request(
                'get', link, stream=True)
            if img_response.status_code != 200:
                raise Exception()
        except:
            # print("  (Request Error)")
            raise Exception()

        # If all is still well then read the response context
        img_content = img_response.content
        with open(os.path.join(download_path,  link.split('/')[-1]), 'wb') as f:
            byte_image = bytes(img_content)
            f.write(byte_image)
            print("  Download Complete: " + link)
    except:
        print("    Failed to download: " + link)



def download_images(links, download_path):
    for link in links:
        download_image(link, download_path)

# '0':'9' -> ['0','1','2', .. '8']
def ord_chr_range(a, b):
    return [chr(x) for x in range(ord(a), ord(b))]

# '0':'10' -> ['0','1','2', .. '9']
def str_range(a, b):
    return [str(s) for s in range(int(a), int(b))]

def cl_remove_non_digits(strPrice):
    return re.sub("\D", "", str(strPrice))




def cl_get_prices(page):
    soup = BS(page, "lxml")
    # get the spans with prices class
    selector = {"class": "price"}
    spans = soup.findAll("span", selector)
    prices = []
    for el in spans:
        price_string = el.contents;
        prices.append(int(cl_remove_non_digits(price_string)))
    return prices

def cl_get_prices_from_pages(pages):
    prices = []
    for page in pages:
        prices.append(cl_get_prices(page))
    return prices


def cl_get_info_from_page(page):
    # this is returned, describes cost and location
    info = {
        "prices": [],     # all prices that resulted from query
        "locations": [],  # all locations that resulted from query
        "label": ""       # names this result (ie: location name)
        }

    # find all row items and store in info
    info["label"] = page[0]
    soup = BS(page[1], "lxml")
    selector = {"class": "result-row"}
    rows = soup.findAll("li", selector)
    tempInfos = []  # as HTML
    for row in rows:
        tempInfos.append(row.findAll("p", {"class": "result-info"})[0])
    for row in tempInfos:
        # get the spans with price class
        selector = {"class": "result-price"}
        spans_price = row.findAll("span", selector)
        # get spans with locations
        selector = {"class": "result-hood"}
        location_wrapper = row.findAll("span", selector)

        # default initialized item information
        location = ""
        price = -1

        # Extract the data and store in item info
        for el in spans_price:  # unwrap iterator
            price_string = el.contents
            price = int(cl_remove_non_digits(price_string))
        for el in location_wrapper: # unwrap iterator
            location = el.contents[0].strip()

        # Validation of data and insert into lists of information
        if location and len(location) != 0 and price >= 0:
            info["prices"].append(price)
            info["locations"].append(location)

    return info

def cl_get_info_from_pages(pages):
    infos = []
    for page in pages:
        infos.append(cl_get_info_from_page(page))
    return infos




def format(a, nsig = 2):
    return str.format('{0:.'+str(nsig)+'f}', a)

def cl_get_base_url(url):
    parsed_uri = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    if domain == ":///":
        return ""
    return domain

def cl_get_base_urls(urls):
    return [cl_get_base_url(url) for url in urls]

def cl_remove_protocol_identifier(url):
    strs = ["http://", "https://"]
    for s in strs:
        g = re.match(s, url)
        if g is not None:
            return url[len(s):] # return base domain name
    return url # return original if no match found

def cl_get_resource_name(url):
    domain = cl_get_base_url(url)
    domain = cl_remove_protocol_identifier(domain)
    domain = domain.replace("/", "")
    domain = domain.replace("\\", "")
    return domain

def cl_get_resource_names(urls):
    return [cl_get_resource_name(url) for url in urls]

def cl_compute_price_stats(prices):
    stat_info = {
        "minimum": min(prices),
        "maximum": max(prices),
        "mean": stats.mean(prices),
        "median": stats.median(prices),
        "stddev": stats.stdev(prices),
        "variance": stats.variance(prices),
        }
    stat_info["lstd1"] = stat_info["mean"] - stat_info["stddev"]
    stat_info["rstd1"] = stat_info["mean"] + stat_info["stddev"]
    return stat_info

# full path to the file.
def get_path_to_file(fullpath):
    return "/".join(fullpath.split("/")[0:-1])

# locations is an array of strings
def cl_write_locations(filename, locations):
    make_dir_if_not_exists(get_path_to_file(filename))
    with codecs.open(filename, "w", "utf-8-sig") as f:
        f.write("[Locations]: " + str(filename))
    with codecs.open(filename, "a", "utf-8-sig") as f:
        for location in locations:
            f.write(location)

# # # # # # # #
#             #
#   M A I N   #
#             #
# # # # # # # #
def main():



    urls = [
       "https://sfbay.craigslist.org/search/sfc/roo?",
       "https://sfbay.craigslist.org/search/nby/roo?",
       "https://sfbay.craigslist.org/search/pen/roo?",
       "https://elpaso.craigslist.org/search/pen/roo?",
        "https://austin.craigslist.org/search/roo?",
        "https://indianapolis.craigslist.org/search/roo?",
        ]

    maxMinQuery = "&min_price=500&max_price=4000"
    for i in range(len(urls)):
        urls[i] += maxMinQuery

    locationQueries = [
        { "name": "San Francisco",
          "locations":
            [ "", "Financial", "Mission", "Sunset", "Richmond" ] },
        { "name": "North Bay",
          "locations":
            ["",  "sausalito", "larkspur", "mill+valley", "san+rafael", "novato", "petaluma", "rohnert+park", "windsor" ] },
        { "name": "Peninsula",
          "locations":
            ["",  "palo+alto", "sunnyvale", "san+mateo" ] },
        { "name": "El Paso",
          "locations": [""] },
        { "name": "Austin",
          "locations": [""] },
        { "name": "Indianapolis",
          "locations": [""] },
    ]

    # scraping takes a while..
    # base_urls = cl_get_resource_names(urls)
    # pages = get_pages(urls)
    # This scrapes multiple times for one location (gathers history)
    pages = []
    for idx, locationQuery in enumerate(locationQueries):
        url = urls[idx]
        for location in locationQuery["locations"]:
            locationName = locationQuery["name"]
            u = url
            if len(location) > 0:
                locationName += " (" + location + ")"
                u += "&query=" + location

            url_combined_pages = ""
            searchRoot=0
            searchRootInc=120
            searchRootQuery = "&s="
            searchRootQueriesPerLocation=3
            for query in range(searchRootQueriesPerLocation):
                u += searchRootQuery + str(searchRootInc*(query+searchRoot))
                print("Getting: " + u)
                url_combined_pages += (make_get_request(u) + '\n')
            pages.append([locationName, url_combined_pages])

    # save pages just in case
    filenames = map(lambda x: x[0] + ".html", pages)
    print(filenames)
    write_pages_to_files(pages, filenames, path="./scraped/")

    # get the prices on cl
        # pricess = cl_get_prices_from_pages(pages)
    infos = cl_get_info_from_pages(pages)

    # some stats on the prices, does not include prices
    stat_info = {
        "price_stats": [],   # stat per query
        "locations": [],     # [] of locations per query
        "labels": [],        # location-names of each query
        }

    # set the data
    for info in infos:
        stat_info["price_stats"].append(cl_compute_price_stats(info["prices"])),
        stat_info["locations"].append(info["locations"])
        stat_info["labels"].append(info["label"])

    for info in infos:
        cl_write_locations("./locations/locations.txt", info["locations"])

    # show the average prices
        # for idx, prices in enumerate(pricess):
    for idx, stats in enumerate(stat_info["price_stats"]):
        print("-- " + stat_info["labels"][idx] + " --")
        print("Min: " + format(stats["minimum"]))
        print(" LAV: " + format(stats["lstd1"]))
        print(" Avg: " + format(stats["mean"]))
        print(" RAV: " + format(stats["rstd1"]))
        print("Max: " + format(stats["maximum"]))
        print(" - - - -")
        print("Median: " + format(stats["median"]))
        print("Deviat: " + format(stats["stddev"]))
        print("Varian: " + format(stats["variance"]))
        print("")

    print("Done.")



if __name__ == "__main__":
    main()
    exit()
