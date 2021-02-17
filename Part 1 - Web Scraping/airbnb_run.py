from airbnb_parser import Parser
import time

if __name__ == "__main__":
    locations = {
        'Mayrhofen_AT': 'https://www.airbnb.com/s/Mayrhofen--Austria/homes?query=Mayrhofen%2C%20Austria&checkin=2021-03-06&checkout=2021-03-13&adults=4',
        'Kitzbuehel_AT': 'https://www.airbnb.com/s/Kitzbuhel--Austria/homes?query=Kitzbuhel%2C%20Austria&checkin=2021-03-06&checkout=2021-03-13&adults=4',
        'Ischgl_AT': 'https://www.airbnb.com/s/Ischgl--Austria/homes?query=Ischgl%2C%20Austria&checkin=2021-03-06&checkout=2021-03-13&adults=4',
        'Soelden_AT': 'https://www.airbnb.com/s/Solden--Austria/homes?query=Solden%2C%20Austria&checkin=2021-03-06&checkout=2021-03-13&adults=4',
        'ZellAmSee_AT': 'https://www.airbnb.com/s/Zell-am-See--Austria/homes?query=Zell%20am%20See%2C%20Austria&checkin=2021-03-06&checkout=2021-03-13&adults=4'
    }

    for location in locations:
        new_parser = Parser(locations[location], f'./{location}.csv')
        t0 = time.time()
        new_parser.parse()
        print(location, time.time() - t0)