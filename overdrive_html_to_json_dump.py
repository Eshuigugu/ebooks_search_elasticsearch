import requests
from bs4 import BeautifulSoup
from time import sleep
import json
import re


def loan_books_from_page(subdomain, page):
    url = f'https://{subdomain}.overdrive.com/search?page={page}&sortBy=newlyadded&format=ebook-kindle'
    print(f'browsing page {url}')
    try:
        r = sess.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'})
        soup = BeautifulSoup(r.text, 'html.parser')
        page_title = soup.find('title').text
    except:page_title='error'
    if 'error' in page_title.lower() or 'Gateway Time-out' in page_title or r.status_code != 200:
        sleep(30)
        r = sess.get(url, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
    sleep(1)
    for x in soup.find_all('script'):
        try:
            books_meta_json = json.loads(re.search('window.OverDrive.mediaItems = (.+)', str(x)).group(1).strip('; '))
            break
        except:
            pass
    if not len(books_meta_json) and "We couldn't find any matches for your search." in page_title:
        print(f'found no books. maybe no more pages')
        return False

    for k, v in books_meta_json.items():
        v['url'] = f'https://{subdomain}.overdrive.com/media/{k}'
        v['authors'] = [x['name'] for x in v['creators'] if x['role'] == 'Author']
        if 'subtitle' in v and v['subtitle']:
            v['title'] = v['title'] + ': ' + v['subtitle']
        for x in v['formats']:
            if x['id'] in ['ebook-overdrive', 'ebook-epub-adobe']:
                for y in x['identifiers']:
                    if y['type'] in ['ISBN', 'ASIN']:
                        v[y['type']] = y['value']
    return list(books_meta_json.values())


def get_filename(subdomain):
    return f'overdrive_{subdomain}.json'


def main():
    for subdomain in subdomains:
        with open(get_filename(subdomain), 'a') as f:
            books=True
            page=1
            while books:
                books = loan_books_from_page(subdomain, page)
                if books:
                    for row in books:
                        f.write(json.dumps(row) + '\n')
                    print(row)
                page += 1


subdomains = ['hcpl']
filenames = [get_filename(x) for x in subdomains]

sess = requests.Session()
if __name__ == '__main__':
    main()
