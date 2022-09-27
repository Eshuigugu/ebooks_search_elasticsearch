import mysql.connector
import json
import os


def parse_cursor(cursor, columns):
    for x in cursor:
        yield {k: v if type(v) != bytes else json.loads(v.decode()) for k, v in zip(columns, x)}


def main():
    sql_connection = mysql.connector.connect(host='', user='', passwd='', database='')
    cursor = sql_connection.cursor()
    
    columns = ['books.title', 'books.author', 'isbn.isbn', 'books.md5_reported']
    rename_cols = {'books.author': 'authors', 'books.title': 'title', 'books.zlibrary_id': 'zlibrary_id', 'isbn.isbn': 'ISBN', 'books.md5_reported': 'md5_reported'}
    cursor.execute(f'select {",".join(columns)} from books LEFT JOIN isbn ON books.zlibrary_id=isbn.zlibrary_id group by books.zlibrary_id')
    with open('zlib.json', 'w') as f:
        for row in parse_cursor(cursor, columns):
            row = {rename_cols[k] if k in rename_cols else k: v for k, v in row.items()}
            row['url'] = f'https://b-ok.cc/s/?q={row["md5_reported"]}'
            del row["md5_reported"]
            row['authors'] = row['authors'].split(', ')
            f.write(json.dumps(row) + '\n')

    cursor.close()
    sql_connection.close()


if __name__ == '__main__':
    main()
