from airbnb_parser import Parser
import time
import datetime

if __name__ == "__main__":
    # parameterize dates
    date_1 = datetime.date.today() + datetime.timedelta(days=7)
    date_2 = datetime.date.today() + datetime.timedelta(days=14)
    date_1 = date_1.strftime('%Y-%m-%d')
    date_2 = date_2.strftime('%Y-%m-%d')

    locations = {
        'Mayrhofen_AT': f'https://www.airbnb.com/s/Mayrhofen--Austria/homes?query=Mayrhofen%2C%20Austria&checkin={date_1}&checkout={date_2}&adults=4',
        'Kitzbuehel_AT': f'https://www.airbnb.com/s/Kitzbuhel--Austria/homes?query=Kitzbuhel%2C%20Austria&checkin={date_1}&checkout={date_2}&adults=4',
        'Ischgl_AT': f'https://www.airbnb.com/s/Ischgl--Austria/homes?query=Ischgl%2C%20Austria&checkin={date_1}&checkout={date_2}&adults=4',
        'Soelden_AT': f'https://www.airbnb.com/s/Solden--Austria/homes?query=Solden%2C%20Austria&checkin={date_1}&checkout={date_2}&adults=4',
        'ZellAmSee_AT': f'https://www.airbnb.com/s/Zell-am-See--Austria/homes?query=Zell%20am%20See%2C%20Austria&checkin={date_1}&checkout={date_2}&adults=4'
    }

    for location in locations:
        new_parser = Parser(locations[location], f'./{location}.csv')
        t0 = time.time()
        new_parser.parse()
        print(location, time.time() - t0)