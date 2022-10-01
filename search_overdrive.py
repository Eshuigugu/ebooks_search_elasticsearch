from time import sleep
import requests

overdrive_subdomains = ['hcpl']


def search_overdrive(title, authors, mediatype='Ebook', wait=False):
    queries = list({f'{title} {author}'
                    for author in authors[:2]})  # search by title + series and author, max of 20 queries
    media_items = []
    for subdomain in overdrive_subdomains:
        od_api_url = f'https://{subdomain}.overdrive.com/rest/media'
        for query in queries:
            params = {
                'query': query,
                'mediaTypes': mediatype,
                # 'showOnlyAvailable': 'true'  # can limit to only available titles
            }
            try:
                r = sess.get(od_api_url, params=params, timeout=10)
            except requests.ConnectionError as e:
                print(f'error {e}')
                if wait:
                    sleep(10)
                return media_items

            if wait:
                sleep(1)
            r_json = r.json()
            if r.status_code == 200 and r_json['items']:
                for media_item in r_json['items']:
                    media_item['url'] = f'https://{subdomain}.overdrive.com/media/{media_item["id"]}'
                    media_item['source_name'] = f'overdrive_{subdomain}'
                    media_item['authors'] = [x['name'] for x in media_item['creators'] if x['role'] == 'Author'] if authors \
                        else [media_item['firstCreatorName']]
                media_items += r_json['items']
            elif r.status_code != 200:
                print(f'status code {e}')
    # ensure each result is unique
    media_items = list({x['url']: x for x in media_items}.values())
    return media_items


sess = requests.Session()
