import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import json
import time

import pandas as pd

from multiprocessing import Pool

MAYRHOFEN_LINK = 'https://www.airbnb.com/s/Mayrhofen--Austria/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&query=Mayrhofen%2C%20Austria&place_id=ChIJbzLYLzjdd0cRDtGuTzM_vt4&checkin=2021-02-06&checkout=2021-02-13&adults=4&source=structured_search_input_header&search_type=autocomplete_click'

RULES_SEARCH_PAGE = {
    'url': {'tag': 'a', 'get': 'href'},
    'name': {'tag': 'div', 'class': '_hxt6u1e', 'get': 'aria-label'},
    'header': {'tag': 'div', 'class': '_b14dlit'},
    'rooms': {'tag': 'div', 'class': '_kqh46o'},
    'facilities': {'tag': 'div', 'class': '_kqh46o', 'order': 1},
    'badge': {'tag': 'div', 'class': '_17bkx6k'},
    'rating_n_reviews': {'tag': 'span', 'class': '_18khxk1'},
    'price': {'tag': 'span', 'class': '_1p7iugi'},
    'superhost': {'tag': 'div', 'class': '_ufoy4t'},
}

RULES_DETAIL_PAGE = {
    'specialty_1': {'tag': 'div', 'class': '_1qsawv5', 'order': 0},
    'specialty_2': {'tag': 'div', 'class': '_1qsawv5', 'order': 1},
    'specialty_3': {'tag': 'div', 'class': '_1qsawv5', 'order': 2},
    'specialty_4': {'tag': 'div', 'class': '_1qsawv5', 'order': 3},
    'specialty_5': {'tag': 'div', 'class': '_1qsawv5', 'order': 4},
    'refundable_1': {'tag': 'div', 'class': '_cexc0g', 'order': 0},
    'refundable_2': {'tag': 'div', 'class': '_cexc0g', 'order': 1},
    
    'prices_details_1': {'tag': 'li', 'class': '_ryvszj', 'order': 0},
    'prices_details_2': {'tag': 'li', 'class': '_ryvszj', 'order': 1},
    'prices_details_3': {'tag': 'li', 'class': '_ryvszj', 'order': 2},
    'prices_totals_1': {'tag': 'li', 'class': '_adhikmk', 'order': 0},
    'prices_totals_2': {'tag': 'li', 'class': '_adhikmk', 'order': 1},
    
    'ratings_cleanliness': {'tag': 'span', 'class': '_4oybiu', 'order': 0},
    'ratings_accuracy': {'tag': 'span', 'class': '_4oybiu', 'order': 1},
    'ratings_communication': {'tag': 'span', 'class': '_4oybiu', 'order': 2},
    'ratings_location': {'tag': 'span', 'class': '_4oybiu', 'order': 3},
    'ratings_checkin': {'tag': 'span', 'class': '_4oybiu', 'order': 4},
    'ratings_value': {'tag': 'span', 'class': '_4oybiu', 'order': 5},
    
    'lang_responses': {'tag': 'li', 'class': '_1q2lt74', 'order': -1},
    'house_rules': {'tag': 'div', 'class': '_u827kd', 'order': -1},
}


def extract_listings(page_url):
    """Extracts all listings from a given page"""
    
    answer = requests.get(page_url, timeout=5)
    content = answer.content
    soup = BeautifulSoup(content, features='html.parser')
    listings = soup.findAll("div", {"class": "_8s3ctt"})
    
    return listings
        
        
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


def extract_page_features(soup, rules):
    """Extracts all features from the page"""
    features_dict = {}
    for feature in rules:
        try:
            features_dict[feature] = extract_element_data(soup, rules[feature])
        except:
            features_dict[feature] = 'empty'
    
    return features_dict


def extract_soup_js(listing_url, waiting_time=[5, 2]):
    """Extracts HTML from JS pages: open, wait, click, wait, extract"""

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)

    driver.get(listing_url)
    time.sleep(waiting_time[0])
    
    try:
        driver.find_element_by_class_name('_13e0raay').click()
    except:
        pass # amentities button not found
    try:
        driver.find_element_by_class_name('_gby1jkw').click()
    except:
        pass # prices button not found
    
    time.sleep(waiting_time[1])
    detail_page = driver.page_source

    driver.quit()

    return BeautifulSoup(detail_page, features='html.parser')


def scrape_detail_page(base_features):
    detailed_url = 'https://www.airbnb.com' + base_features['url']
    soup_detail = extract_soup_js(detailed_url)

    features_detailed = extract_page_features(soup_detail, RULES_DETAIL_PAGE)
    features_amentities = extract_amentities(soup_detail)

    features_detailed['amentities'] = features_amentities
    features_all = {**base_features, **features_detailed}

    return features_all



def extract_amentities(soup):
    amentities = soup.find_all('div', {'class': '_aujnou'})
    
    amentities_dict = {}
    for amentity in amentities:
        header = amentity.find('div', {'class': '_1crk6cd'}).get_text()
        values = amentity.find_all('div', {'class': '_1dotkqq'})
        values = [v.find(text=True) for v in values]
        
        amentities_dict['amentity_' + header] = values
        
    return json.dumps(amentities_dict)


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
                features = extract_page_features(listing, RULES_SEARCH_PAGE)
                features_list.append(features)

        self.base_features_list = features_list
        

    def process_detail_pages(self):
        with Pool(8) as pool:
            result = pool.map(scrape_detail_page, self.base_features_list)
        pool.close()
        pool.join()

        self.all_features_list = result


    def save(self):
        pd.DataFrame(self.all_features_list).to_csv(self.out_file, index=False)
            
        
    def parse(self):
        self.build_urls()
        self.process_search_pages()
        self.process_detail_pages()
        self.save()


if __name__ == "__main__":
    new_parser = Parser(MAYRHOFEN_LINK, './test.csv')
    t0 = time.time()
    new_parser.parse()
    print(time.time() - t0)