import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import json
import time

import os

import pandas as pd

from multiprocessing import Pool

MAYRHOFEN_LINK = 'https://www.airbnb.com/s/Mayrhofen--Austria/homes?query=Mayrhofen%2C%20Austria&checkin=2021-04-06&checkout=2021-04-13&adults=4'

RULES_SEARCH_PAGE = {
    'url': {'tag': 'a', 'get': 'href'},
    'name': {'tag': 'div', 'class': '_hxt6u1e', 'get': 'aria-label'},
    'name_alt': {'tag': 'a', 'get': 'aria-label'},
    'header': {'tag': 'div', 'class': '_b14dlit'},
    'rooms': {'tag': 'div', 'class': '_kqh46o'},
    'facilities': {'tag': 'div', 'class': '_kqh46o', 'order': 1},
    'badge': {'tag': 'div', 'class': '_17bkx6k'},
    'rating_n_reviews': {'tag': 'span', 'class': '_18khxk1'},
    'price': {'tag': 'span', 'class': '_1p7iugi'},
    'price_alt': {'tag': 'span', 'class': '_olc9rf0'},
    'superhost': {'tag': 'div', 'class': '_ufoy4t'},
}

RULES_DETAIL_PAGE = {
    'location': {'tag': 'span', 'class': '_jfp88qr'},
    
    'specialties_1': {'tag': 'div', 'class': 't1bchdij', 'order': -1},
    'specialties_2': {'tag': 'div', 'class': '_1qsawv5', 'order': -1},

    'price_per_night': {'tag': 'div', 'class': '_ymq6as'},
    
    'refundables': {'tag': 'div', 'class': '_cexc0g', 'order': -1},
        
    'prices_1': {'tag': 'li', 'class': '_ryvszj', 'order': -1},
    'prices_2': {'tag': 'li', 'class': '_adhikmk', 'order': -1},
    
    'listing_ratings': {'tag': 'span', 'class': '_4oybiu', 'order': -1},
    
    'host_joined': {'tag': 'div', 'class': '_1fg5h8r', 'order': 1},
    'host_feats': {'tag': 'span', 'class': '_pog3hg', 'order': -1},
    
    'lang_responses': {'tag': 'li', 'class': '_1q2lt74', 'order': -1},
    'house_rules': {'tag': 'div', 'class': '_u827kd', 'order': -1},
}


def extract_listings(page_url, attempts=10):
    """Extracts all listings from a given page"""
    
    listings_max = 0
    listings_out = [BeautifulSoup('', features='html.parser')]
    for idx in range(attempts):
        try:
            answer = requests.get(page_url, timeout=5)
            content = answer.content
            soup = BeautifulSoup(content, features='html.parser')
            listings = soup.findAll("div", {"class": "_gig1e7"})
        except:
            # if no response - return a list with an empty soup
            listings = [BeautifulSoup('', features='html.parser')]

        if len(listings) == 20:
            listings_out = listings
            break

        if len(listings) >= listings_max:
            listings_max = len(listings)
            listings_out = listings

    return listings_out
        
        
def extract_element_data(soup, params):
    """Extracts data from a specified HTML element"""
    
    # 1. Find the right tag
    if 'class' in params:
        elements_found = soup.find_all(params['tag'], params['class'])
    else:
        elements_found = soup.find_all(params['tag'])
        
    # 2. Extract text from these tags
    if 'get' in params:
        element_texts = [el.get(params['get']) for el in elements_found]
    else:
        element_texts = [el.get_text() for el in elements_found]
        
    # 3. Select a particular text or concatenate all of them
    tag_order = params.get('order', 0)
    if tag_order == -1:
        output = '**__**'.join(element_texts)
    else:
        output = element_texts[tag_order]
    
    return output


def extract_listing_features(soup, rules):
    """Extracts all features from the listing"""
    features_dict = {}
    for feature in rules:
        try:
            features_dict[feature] = extract_element_data(soup, rules[feature])
        except:
            features_dict[feature] = 'empty'
    
    return features_dict


def extract_soup_js(listing_url, waiting_time=[20, 1]):
    """Extracts HTML from JS pages: open, wait, click, wait, extract"""

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--blink-settings=imagesEnabled=false')
    driver = webdriver.Chrome(options=options)

    # if the URL is not valid - return an empty soup
    try:
        driver.get(listing_url)
    except:
        print(f"Wrong URL: {listing_url}")
        return BeautifulSoup('', features='html.parser')
    
    # waiting for an element on the bottom of the page to load ("More places to stay")
    try:
        myElem = WebDriverWait(driver, waiting_time[0]).until(EC.presence_of_element_located((By.CLASS_NAME, '_4971jm')))
    except:
        pass

    # click cookie policy
    try:
        driver.find_element_by_xpath("/html/body/div[6]/div/div/div[1]/section/footer/div[2]/button").click()
    except:
        pass
    # alternative click cookie policy
    try:
        element = driver.find_element_by_xpath("//*[@data-testid='main-cookies-banner-container']")
        element.find_element_by_xpath("//button[@data-testid='accept-btn']").click()
    except:
        pass

    # looking for price details
    price_dropdown = 0
    try:
        element = driver.find_element_by_class_name('_gby1jkw')
        price_dropdown = 1
    except:
        pass

    # if the element is present - click on it
    if price_dropdown == 1:
        for i in range(10): # 10 attempts to scroll to the price button
            try:
                actions = ActionChains(driver)
                driver.execute_script("arguments[0].scrollIntoView(true);", element);
                actions.move_to_element_with_offset(element, 5, 5)
                actions.click().perform()
                break
            except:
                pass
        
    # looking for amenities
    driver.execute_script("window.scrollTo(0, 0);")
    try:
        driver.find_element_by_class_name('_13e0raay').click()
    except:
        pass # amenities button not found

    time.sleep(waiting_time[1])

    detail_page = driver.page_source

    driver.quit()

    return BeautifulSoup(detail_page, features='html.parser')


def scrape_detail_page(base_features):
    """Scrapes the detail page and merges the result with basic features"""
    
    detailed_url = 'https://www.airbnb.com' + base_features['url']
    soup_detail = extract_soup_js(detailed_url)

    features_detailed = extract_listing_features(soup_detail, RULES_DETAIL_PAGE)
    features_amenities = extract_amenities(soup_detail)

    features_detailed['amenities'] = features_amenities
    features_all = {**base_features, **features_detailed}

    return features_all


def extract_amenities(soup):
    amenities = soup.find_all('div', {'class': '_aujnou'})
    
    amenities_dict = {}
    for amenity in amenities:
        header = amenity.find('div', {'class': '_1crk6cd'}).get_text()
        values = amenity.find_all('div', {'class': '_1dotkqq'})
        values = [v.find(text=True) for v in values]
        
        amenities_dict['amenity_' + header] = values
        
    return json.dumps(amenities_dict)


class Parser:
    def __init__(self, link, out_file):
        self.link = link
        self.out_file = out_file

    
    def build_urls(self, listings_per_page=20, pages_per_location=15):
        """Builds links for all search pages for a given location"""
        url_list = []
        for i in range(pages_per_location):
            offset = listings_per_page * i
            url_pagination = self.link + f'&items_offset={offset}'
            url_list.append(url_pagination)
            self.url_list = url_list


    def process_search_pages(self):
        """Extract features from all search pages"""
        features_list = []
        for page in self.url_list:
            listings = extract_listings(page)
            for listing in listings:
                features = extract_listing_features(listing, RULES_SEARCH_PAGE)
                features['sp_url'] = page
                features_list.append(features)

        self.base_features_list = features_list
        

    def process_detail_pages(self):
        """Runs detail pages processing in parallel"""
        n_pools = os.cpu_count() // 2
        with Pool(n_pools) as pool:
            result = pool.map(scrape_detail_page, self.base_features_list)
        pool.close()
        pool.join()

        self.all_features_list = result


    def save(self, feature_set='all'):
        if feature_set == 'basic':
            pd.DataFrame(self.base_features_list).to_csv(self.out_file, index=False)
        elif feature_set == 'all':
            pd.DataFrame(self.all_features_list).to_csv(self.out_file, index=False)
        else:
            pass
            
        
    def parse(self):
        self.build_urls()
        self.process_search_pages()
        self.process_detail_pages()
        self.save('all')


if __name__ == "__main__":
    new_parser = Parser(MAYRHOFEN_LINK, './test.csv')
    t0 = time.time()
    new_parser.parse()
    print(time.time() - t0)