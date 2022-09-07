import requests
import json
from time import sleep
from tqdm import tqdm


session = requests.session()
# TOR proxy
session.proxies = {'http':  'socks5h://127.0.0.1:9150',
                   'https': 'socks5h://127.0.0.1:9150'}


def main():
    n_books = 1479167  # updating this is optional
    step_size = 100
    n_pages = n_books // step_size + 1

    start_idx = 0
    page = start_idx // step_size
    bar = tqdm(total=n_pages - page)

    rename_cols = {'Title': 'title', 'Author': 'authors', 'isbn': 'ISBN'}
    keepGoing = True
    while keepGoing:
        url = f'http://kx5thpx2olielkihfyo4jgjqfb7zx7wxr3sd4xzt26ochei4m6f7tayd.onion/search/?q=&p={page}&num={step_size}&fmt=json'
        # r = session.get(url)
        # sleep(1)
        print(url)
        r = None
        for i in range(8):
            try:
                if i:
                    sleep(60 * 2.5 ** i)
                r = session.get(url, timeout=600)
                sleep(1)
                if r.status_code != 200:
                    print(r.status_code)
                    continue
            except Exception as e:
                print(f'error', e)
            else:
                break
        if not r:
            raise Exception

        r_json = r.json()
        with open('trantor.json', 'a') as f:
            for row in r_json['books']:
                row = {rename_cols[k] if k in rename_cols else k: v for k, v in row.items()}
                row['url'] = f'http://kx5thpx2olielkihfyo4jgjqfb7zx7wxr3sd4xzt26ochei4m6f7tayd.onion/book/{row["id"]}'
                if ' • ' in row['title']:  # trantor has some titles like "[$series_name $series_position] • $title"
                    row['title'] = row['title'].split(' • ')[-1]
                f.write(json.dumps(row) + '\n')
        bar.update(1)
        keepGoing = len(r_json['books']) >= step_size
        page += 1

    print('done')


if __name__ == '__main__':
    main()
