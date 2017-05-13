import bs4
import functools
import json
import os
import random
import requests
import time

def fix_href(href):
    return href.replace('\\"', '').replace('https://angel.co/', '')

def cache(entity):
    def decorator(func):
        @functools.wraps(func)
        def wrapped(item, *args, **kwargs):
            fn = 'cache/%s_%s.json' % (entity, item)
            if os.path.exists(fn):
                return json.load(open(fn))
            data = func(item, *args, **kwargs)
            f = open(fn, 'w')
            json.dump(data, f)
            f.close()
            return data
        return wrapped
    return decorator


@cache('tags')
def scrape_tag(tag):
    tags = set()
    companies = {}
    for page in range(1, 21):
        time.sleep(2.0)
        res = requests.get('https://angel.co/' + tag,
                           data={'page': page},
                           headers={'X-Requested-With': 'XMLHttpRequest'})
        page = bs4.BeautifulSoup(res.content)
        if not page.find_all('a'):
            break
        for a in page.find_all('a', {'class': '\\"startup-link\\"'}):
            href = fix_href(a.attrs['href'])
            name = a.text
            if name:
                companies[href] = name
        for div in page.find_all('div', {'class': 'tags'}):
            tags.update([fix_href(a.attrs['href']) for a in div.find_all('a')])
    return {'tags': list(tags), 'companies': companies}


@cache('companies')
def scrape_company(company, delay):
    time.sleep(delay)
    res = requests.get('https://angel.co/' + company,
                       headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'})
    res.raise_for_status()
    page = bs4.BeautifulSoup(res.content)
    if not page.find('div', {'class': 'summary'}) and not page.find('h3', {'class': 'founders'}):
        print(res.content)
        raise

    data = []
    for li in page.find_all('li', {'class': 'startup_round'}):
        stage = li.find('div', {'class': 'type'}).text.strip()
        date_div = li.find('div', {'class': 'date_display'})
        if date_div:
            date = date_div.text
        else:
            date = None
        raised = li.find('div', {'class': 'raised'}).text.strip()
        valuation_div = li.find('div', {'class': 'valuation'})
        if valuation_div:
            valuation = valuation_div.find('strong').text.strip()
        else:
            valuation = None
        data.append({'stage': stage, 'date': date, 'raised': raised, 'valuation': valuation})
    return data


companies = {}
company_count = {}
tags_to_scrape = set(['san-francisco'])
tags_scraped = set()
while len(tags_to_scrape):
    tag = tags_to_scrape.pop()
    print('Got %6d companies, %6d more tags, now scraping %s' % (len(companies), len(tags_to_scrape), tag))
    if tag in tags_scraped:
        continue
    tags_scraped.add(tag)
    data = scrape_tag(tag)
    companies.update(data['companies'])
    for company in data['companies'].keys():
        company_count[company] = company_count.get(company, 0) + 1
    tags_to_scrape.update([tag for tag in data['tags'] if tag not in tags_scraped and tag not in tags_to_scrape])

delay = 60
for company in sorted(company_count.keys(), key=company_count.get, reverse=True):
    while True:
        print(delay, company)
        try:
            print(scrape_company(company, delay))
            delay = max(delay * 0.95, 30)
            break
        except:
            delay = min(delay * 1.5, 1800)
