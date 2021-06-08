import pandas as pd
import numpy as np
import re
import datetime
import json
import time


LIST_SPECIALTIES = [
    'Clean and tidy',
    'Enhanced Clean',
    'Entire home',
    'Experienced host',
    'Free cancellation',
    'Great check-in experience',
    'Great communication',
    'Great location',
    'Highly rated host',
    'Kitchen',
    'Outstanding hospitality',
    'Pets allowed',
    'Pool',
    'Self check-in',
    'Wifi'
]

LIST_LANGUAGES = [
    'Deutsch',
    'English',
    'Español',
    'Français',
    'Italiano',
    'Nederlands',
    'Norsk',
    'Polski',
    'Português',
    'Čeština',
    'Ελληνικά',
    'Русский',
    'العربية'
]

LIST_RATINGS = ['cleanliness', 'accuracy', 'communication', 'location', 'check-in', 'value']

LIST_AMENITIES = [
    {
        'name': 'TV',
        'substr': ['TV'],
        'positive': ['Basic', 'Entertainment'],
        'negative': ['Not included'],
    },
    {
        'name': 'wifi',
        'substr': ['Wifi'],
        'positive': ['Basic', 'Internet and office'],
        'negative': ['Not included'],
    },
    {
        'name': 'free_parking',
        'substr': ['Free parking'],
        'positive': ['Facilities', 'Parking and facilities'],
        'negative': ['Not included'],
    },
    {
        'name': 'kitchen',
        'substr': ['Kitchen'],
        'positive': ['Kitchen and dining'],
        'negative': ['Not included'],
    },
    {
        'name': 'kitchen_stuff',
        'substr': ['Coffee maker', 'Dishwasher', 'Microwave', 'Oven', 'Refrigerator'],
        'positive': ['Kitchen and dining'],
        'negative': ['Not included'],
    },
    {
        'name': 'outdoor',
        'substr': ['BBQ grill', 'Patio or balcony', 'Garden or backyard'],
        'positive': ['Outdoor'],
        'negative': ['Not included'],
    },
    {
        'name': 'bathtub',
        'substr': ['Bathtub'],
        'positive': ['Bathroom'],
        'negative': ['Not included'],
    },
    {
        'name': 'hair_drier',
        'substr': ['Hair dryer'],
        'positive': ['Bathroom', 'Bed and bath'],
        'negative': ['Not included'],
    },
    {
        'name': 'shampoo',
        'substr': ['Shampoo', 'Shower gel'],
        'positive': ['Bathroom', 'Bed and bath'],
        'negative': ['Not included'],
    },
    {
        'name': 'air_cond',
        'substr': ['Air conditioning'],
        'positive': ['Heating and cooling'],
        'negative': ['Not included'],
    },
    {
        'name': 'pool',
        'substr': ['Pool'],
        'positive': ['Parking and facilities'],
        'negative': ['Not included'],
    },
]

LIST_FACILITIES = [
    'Kitchen',
    'Wifi',
    'Free parking',
    'Dishwasher',
    'Hosted by a business',
    'Washer',
    'Pets allowed',
    'Dryer',
    'Self check-in',
    'Indoor fireplace',
    'Pool',
    'Elevator',
    'Breakfast',
    'Ski-in/Ski-out',
    'Air conditioning',
    'Hot tub',
]


def make_name(data):
    data['name'] = data['name'].replace('empty', np.nan).fillna(data['name_alt'])

    return data


def make_specialties(data, specialties_set=LIST_SPECIALTIES):
    data['specialties'] = data['specialties_1'].replace('empty', np.nan).fillna(data['specialties_2'])
    data['specialties_split'] = data['specialties'].str.split("\*\*__\*\*")

    # Filter out:
    # 1. 'Free cancellation until 3:00 PM on Mar 1' -> 'Free cancellation'
    # 2. Remove 'Superhost', 'Cancellation policy', 'House rules'
    def process_specialties(sp_list, to_remove = ['is a Superhost', 'Cancellation policy', 'House rules']):
        if not isinstance(sp_list, list):
            return ''
        new_list = []
        
        for sp in sp_list:
            if 'Free cancellation' in sp:
                new_list.append('Free cancellation')
            elif any(x in sp for x in to_remove):
                continue
            else:
                new_list.append(sp)
                
        return new_list
    data['specialties_split_clean'] = data['specialties_split'].apply(lambda x: process_specialties(x))

    data_specialties = data.loc[:, ['url', 'specialties_split_clean']]
    for _s in specialties_set:
        data_specialties[f"specialty_{_s}"] = data_specialties['specialties_split_clean'].apply(lambda x: 1 if _s in x else 0)
    data_specialties.drop('specialties_split_clean', axis=1, inplace=True)

    return data_specialties


def make_lang_response(data, lang_set=LIST_LANGUAGES):
    data['lang_responses_split'] = data['lang_responses'].str.split("\*\*__\*\*")
    data_lang_resp = data.loc[:, ['url', 'lang_responses_split']]
    
    # ['Languages: English, Deutsch', 'Response rate: 75%', 'Response time: within a day'] -> separate objects:
    # 'English, Deutsch'; '75%'; 'within a day'
    for _obj in ['Languages', 'Response rate', 'Response time']:
        data_lang_resp[_obj] = data_lang_resp['lang_responses_split'].fillna('empty').apply(lambda x: [_.split(': ')[1] for _ in x if _.startswith(_obj)])
        data_lang_resp[_obj] = data_lang_resp[_obj].apply(lambda x: x[0] if len(x) > 0 else '')
    
    for _l in lang_set:
        data_lang_resp[f"language_{_l}"] = data_lang_resp['Languages'].apply(lambda x: 1 if _l in x.split(', ') else 0)
    
    data_lang_resp['lang_cnt'] = data_lang_resp['Languages'].apply(lambda x: len(x.split(', ')) if len(x) > 0 else 0)
    data_lang_resp['response_rate'] = data_lang_resp['Response rate'].apply(lambda x: x.split('%')[0])
    data_lang_resp['response_time'] = data_lang_resp['Response time']
    
    to_drop = ['lang_responses_split', 'Languages', 'Response rate', 'Response time']
    data_lang_resp.drop(to_drop, axis=1, inplace=True)

    return data_lang_resp


def make_prices(data):
    # price per night total
    data['price_night_all'] = data['price_alt'].replace('empty', np.nan).fillna(data['price'])

    # price per night for the room:
    # €205 €141/ night -> €141
    # €139/ night -> €139
    def price_per_night_regex(price_string):
        match = re.search('([$€][0-9]+ ){0,1}([$€][0-9]+){0,1}/ night', price_string)
        if match:
            result = match[2]
        else:
            result = 'empty'
        return result
    data['price_night_room'] = data['price_per_night'].apply(price_per_night_regex)

    # parse temporary columns prices_1 and prices_2:
    # €160 x 7 nightsView price breakdown€1,120**__**Cleaning feeView price breakdown€100 -> cleaning_fee=100
    # Service feeView price breakdown€0**__**Total€969 -> service_fee=0; total=969
    def parse_fees(input):
        return_cleaning, return_service, return_total = 'empty', 'empty', 'empty'
        if isinstance(input['prices_1'], str):
            _list1 = input['prices_1'].split('**__**')
        else:
            _list1 = ['']
        if isinstance(input['prices_2'], str):
            _list2 = input['prices_2'].split('**__**')
        else:
            _list2 = ['']
        _list = _list1 +_list2

        for _el in _list:
            _sublist = _el.split('View price breakdown')
            if len(_sublist) > 1:
                if _sublist[0] == 'Cleaning fee':
                    return_cleaning = _sublist[1]
                elif _sublist[0] == 'Service fee':
                    return_service = _sublist[1]
            elif _sublist[0].startswith('Total'):
                # €1,120 - > €1120
                return_total = _sublist[0][5:].replace(',', '')

        return return_cleaning, return_service, return_total

    data[['cleaning_fee_EUR', 'service_fee_EUR', 'price_total_EUR']] = data.apply(parse_fees, axis=1, result_type="expand")
        
    return data


def make_rooms(data):
    data['rooms_split'] = data['rooms'].str.split(' · ')

    data['cnt_guests'] = data['rooms_split'].apply(lambda x: x[0].split(' ')[0])
    data['cnt_bedrooms'] = data['rooms_split'].apply(lambda x: x[1].split(' ')[0])
    data['cnt_beds'] = data['rooms_split'].apply(lambda x: x[2].split(' ')[0])
    data['cnt_baths'] = data['rooms_split'].apply(lambda x: x[3].split(' ')[0])
    
    return data


def make_ratings_reviews(data):
    data['listing_rating'] = data['rating_n_reviews'].replace('empty', np.nan).str.split().apply(lambda x: float(x[0]) if isinstance(x, list) else x)
    data['listing_reviews'] = data['rating_n_reviews'].replace('empty', np.nan).str.split().apply(lambda x: float(x[1].strip('()')) if isinstance(x, list) else x)
    return data


def make_refundables(data):
    data['is_refundable'] = data['refundables'].fillna('empty').apply(lambda x: 1 if x!='empty' else 0)
    return data


def make_listing_ratings(data, ratings_list=LIST_RATINGS):
    for idx, _feat in enumerate(ratings_list):
        data[f'rating_{_feat}'] = data['listing_ratings'].fillna('**__**'.join(6*['empty'])).str.split('\*\*__\*\*').str[idx].replace('empty', np.nan)
    return data


def make_host_joined(data):
    data['host_joined_years_ago'] = datetime.date.today().year - data['host_joined'].str.split().str[-1].replace('empty', np.nan).astype('float')
    return data


def make_host_feats(data):
    data['Identity_verified'] = data['host_feats'].fillna('empty').str.split('\*\*__\*\*').apply(lambda x: 1 if 'Identity verified' in x else 0)
    return data


def make_house_rules(data):
    def parse_rules(row):
        house_rules_pets, house_rules_smoking, house_rules_parties = 'empty', 'empty', 'empty'
        row_curr = row['house_rules_split']
        
        # pets
        if '\U000f1906No pets' in row_curr:
            house_rules_pets = 'no'
        elif '\U000f1905Pets are allowed' in row_curr:
            house_rules_pets = 'yes'
            
        # smoking
        if '\U000f1908No smoking' in row_curr:
            house_rules_smoking = 'no'
        elif '\U000f1907Smoking is allowed' in row_curr:
            house_rules_smoking = 'yes'
            
        # parties
        if '\U000f1902No parties or events' in row_curr:
            house_rules_parties = 'no'

        return house_rules_pets, house_rules_smoking, house_rules_parties
    
    data['house_rules_split'] = data['house_rules'].fillna('empty').str.split('\*\*__\*\*')
    data[['house_rules_pets', 'house_rules_smoking', 'house_rules_parties']] = data.apply(parse_rules, axis=1, result_type="expand")

    return data


def parse_amenities(row, am_list=LIST_AMENITIES):
    dict_amenities = json.loads(row['amenities'])

    # {
    #     'name': 'TV',
    #     'substr': ['TV'],
    #     'positive': ['Basic', 'Entertainment'],
    #     'negative': ['Not included'],
    # }
    # search every substr in every positive -> if found then 'yes'
    # search every substr in every negative -> if found then 'no'
    result = ['empty'] * len(am_list)
    for idx, _am in enumerate(am_list):
        for _pos in _am['positive']:
            for _substr in _am['substr']:
                if max([i.find(_substr) for i in dict_amenities.get(f"amenity_{_pos}", [])] + [-1]) >= 0:
                    result[idx] = 'yes'
                    break
        for _neg in _am['negative']:
            for _substr in _am['substr']:
                if max([i.find(_substr) for i in dict_amenities.get(f"amenity_{_neg}", [])] + [-1]) >= 0:
                    result[idx] = 'no'
                    break
    
    return result


def make_amenities(data):
    data_amenities = data.loc[:, ['url', 'amenities']]
    data_amenities.loc[:, 'amenities'] = data_amenities['amenities'].fillna(json.dumps({}))

    # use parse_amenities function
    data_amenities[[f"amenities_{i['name']}" for i in LIST_AMENITIES]] = data_amenities.apply(parse_amenities, axis=1, result_type="expand")
    data_amenities.drop('amenities', axis=1, inplace=True)

    return data_amenities


def make_facilities(data, list_facilities=LIST_FACILITIES):
    data_facilities = data.loc[:, ['url', 'facilities']]

    for _top_facility in list_facilities:
        data_facilities[f"facility_{_top_facility}"] = data_facilities['facilities'].fillna('empty').str.split(' · ').apply(lambda x: 1 if _top_facility in x else 0)
    data_facilities.drop('facilities', axis=1, inplace=True)

    return data_facilities


def make_superhost(data):
    data['is_superhost'] = data['superhost'].fillna('empty').apply(lambda x: 1 if x=='SUPERHOST' else 0)
    
    return data
    

def make_clean(data):
    data = make_name(data)
    data_specialties = make_specialties(data)
    data_lang_resp = make_lang_response(data)
    data = make_prices(data)
    data = make_rooms(data)
    data = make_ratings_reviews(data)
    data = make_refundables(data)
    data = make_listing_ratings(data)
    data = make_host_joined(data)
    data = make_host_feats(data)
    data = make_house_rules(data)
    data_amenities = make_amenities(data)
    data_facilities = make_facilities(data)
    data = make_superhost(data)
    
    # assemble
    columns_bronze = [
        'url',
        'header',
        'location',
        'query'
    ]
    columns_silver = [
        'name',
        'price_night_all', 'price_night_room', 'cleaning_fee_EUR', 'service_fee_EUR', 'price_total_EUR',
        'cnt_guests', 'cnt_bedrooms', 'cnt_beds', 'cnt_baths',
        'listing_rating', 'listing_reviews', 'is_refundable',
        'rating_cleanliness', 'rating_accuracy', 'rating_communication', 'rating_location', 'rating_check-in', 'rating_value',
        'host_joined_years_ago', 'Identity_verified',
        'house_rules_pets', 'house_rules_smoking', 'house_rules_parties',
        'is_superhost'
    ]

    df_to_merge = [data[columns_bronze + columns_silver], data_specialties, data_lang_resp, data_amenities, data_facilities]
    _dfs = [df.set_index('url') for df in df_to_merge]
    data_silver = _dfs[0].join(_dfs[1:], how='outer').reset_index()

    return data_silver
    

def main():
    data_1 = pd.read_csv('./Part 1 - Web Scraping/Mayrhofen_AT.csv')
    data_2 = pd.read_csv('./Part 1 - Web Scraping/Kitzbuehel_AT.csv')
    data_3 = pd.read_csv('./Part 1 - Web Scraping/Ischgl_AT.csv')

    data_1['query'] = 'Mayrhofen_AT'
    data_2['query'] = 'Kitzbuehel_AT'
    data_3['query'] = 'Ischgl_AT'

    data = pd.concat([data_1, data_2, data_3]).reset_index(drop=True)

    data_clean = make_clean(data)
    data_clean.to_csv('./Part 2 - Data Cleaning/data_clean.csv', index=False)

if __name__ == "__main__":
    t0 = time.time()
    main()
    print(time.time() - t0)