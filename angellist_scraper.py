import bs4
import functools
import json
import os
import requests
import time

def fix_href(href):
    return href.replace('\\"', '').replace('https://angel.co/', '')

def cache(entity):
    def decorator(func):
        @functools.wraps(func)
        def wrapped(item):
            fn = 'cache/%s_%s.json' % (entity, item)
            if os.path.exists(fn):
                return json.load(open(fn))
            data = func(item)
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
                print(href, name)
                companies[href] = name
        for div in page.find_all('div', {'class': 'tags'}):
            tags.update([fix_href(a.attrs['href']) for a in div.find_all('a')])
    return {'tags': list(tags), 'companies': companies}

tags_to_scrape = set(['san-francisco'])
tags_scraped = set()
while len(tags_to_scrape):
    tag = tags_to_scrape.pop()
    print(tag)
    if tag in tags_scraped:
        continue
    tags_scraped.add(tag)
    data = scrape_tag(tag)
    tags_to_scrape.update([tag for tag in data['tags'] if tag not in tags_scraped and tag not in tags_to_scrape])
