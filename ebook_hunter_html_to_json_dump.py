import json
from bs4 import BeautifulSoup
import requests
import re
from time import sleep
import urllib
import os


sess = requests.Session()
base_url = 'https://ebook-hunter.org'
links = set()


def scrape_subpage(sub_dir='Books'):
    page = 0
    keep_going=True
    while keep_going:
        page += 1
        url = f'https://ebook-hunter.org/Books/{sub_dir}/{page}/'

        print(url)
        for _ in range(3):
            try:
                sleep(1)
                r = sess.get(url, timeout=5)
                if r.status_code == 200:
                    break
                else:
                    print(r.status_code, r.text)
                    sleep(20)
            except Exception as e:
                print(e)

        if r.status_code == 200:
            html = r.text
            soup = BeautifulSoup(html, parser='html.parser', features="lxml")
            books = soup.find(id="mains_left", class_="float_left").findChildren(class_="mains_left_box", recursive=False)[-1].findChildren('div', class_="index_box", recursive=False)

            # format, url, categories, lang, pub date, author(s)
            if len(books):
                with open('ebookhunter.json', 'a') as f:
                    for b in books:
                        title = b.find(class_="index_box_title list_title").get_text().strip()
                        title = title[::-1].split(' yb ')[-1][::-1]

                        info_str = b.find(class_="index_box_info list_title").get_text().strip().splitlines()[0]
                        filetype, lang, pub_date, author = [x.strip() for x in info_str.split('|', maxsplit=3)]
                        author = re.sub('\[.*\]', '', author).strip()
                        author = author[7:] if author.startswith('Author:') else author
                        authors = re.split(' [\&\|] ', author)
                        if authors == ['Unknown']:
                            authors = None
                        url = base_url + urllib.parse.quote(b.find('a').get('href'))
                        categories = b.find(class_="index_box_tools").get_text().strip()[20:-20].strip()
                        uid = url.split('_')[-1].strip('/')

                        json_dict = {'uid': uid, 'title': title, 'authors': author, 'filetype': filetype, 'lang': lang, 'pub_date': pub_date, 'url': url, 'categories': categories}
                        f.write(json.dumps(json_dict) + '\n')
                    print(json_dict)


                # get all links in the page
                for a in soup.find_all('a'):
                    url = a.get('href')
                    if url.startswith('/Books/') and url not in links:
                        links.add(url)
                        with open('ebook_hunter_links.txt', 'a') as f:
                            f.write(url + '\n')

        if page > 5000 or not len(books):
            keep_going = False

    with open('ebook_hunter_scraped_pages.txt', 'a') as f:
        f.write(sub_dir + '\n')


def scrape_ebook_hunter():
    if os.path.exists('ebook_hunter_links.txt'):
        file_txt = open('ebook_hunter_links.txt', 'r').read()
        found_categories = {x for x in file_txt.splitlines()}
        found_categories = {x[7:-1].strip() for x in found_categories}
        found_categories = {x for x in found_categories if not x.split('/')[-1].isdigit() and len(x) < 70}
    else:
        found_categories = set()
    if os.path.exists('ebook_hunter_scraped_pages.txt'):
        with open('ebook_hunter_scraped_pages.txt', 'r') as f:
            found_categories = sorted(list(found_categories - set(f.read().splitlines())), key=lambda x:len(x))
    else:
        found_categories = ['']
    print(f'got {len(found_categories)} links')

    for category in found_categories:
        scrape_subpage(category)


def main():
    for _ in range(3):
        scrape_ebook_hunter()


if __name__ == '__main__':
    main()
