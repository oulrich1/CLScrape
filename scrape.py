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
            f.write(pages[idx])

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
    spans = soup.findAll("span", {"class": "price"})
    prices = []
    for el in spans:
        price_string = el.contents;
        prices.append(int(cl_remove_non_digits(price_string)))
    return prices

# CL specific stuff
def cl_get_prices_from_pages(pages):
    prices = []
    for page in pages:
        prices.append(cl_get_prices(page))
    return prices

def format(a, nsig = 2):
    return str.format('{0:.'+str(nsig)+'f}', a)

def cl_get_domain_name(url):
    parsed_uri = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    if domain == ":///":
        return ""
    return domain

def cl_get_domain_names(urls):
    return [cl_get_domain_name(url) for url in urls]

# # # # # # # #
#             #
#   M A I N   #
#             #
# # # # # # # #
def main():

    urls = [
       "https://sfbay.craigslist.org/search/sfc/roo",
       "https://sfbay.craigslist.org/search/nby/roo",
       "https://chico.craigslist.org/search/roo",
       "https://redding.craigslist.org/search/roo",
       "https://sacramento.craigslist.org/search/roo"
    ]

    # scraping takes a while..
    domain_names = cl_get_domain_names(urls)
    pages = get_pages(urls)

    # save pages just in case
    filenames = get_filenames(urls)
    write_pages_to_files(pages, filenames, path="./scraped/")

    # get prices
    pricess = cl_get_prices_from_pages(pages)

    # average prices
    for idx, prices in enumerate(pricess):
        # print("-- " + domain_names[idx] + " --")
        print("-- " + urls[idx] + " --")
        mean = stats.mean(prices)
        median = stats.median(prices)
        stddev = stats.stdev(prices)
        variance = stats.variance(prices)
        print("Min: " + format(min(prices)))
        print("Avg: " + format(mean))
        print("Max: " + format(max(prices)))
        print("Med: " + format(median))
        print("Dev: " + format(stddev))
        print("Var: " + format(variance))
        print("")

    print("Done.")



if __name__ == "__main__":
    main()
    exit()
