import mysql.connector
import json
import os


def parse_cursor(cursor, columns):
    for x in cursor:
        yield {k: v if type(v) != bytes else json.loads(v.decode()) for k, v in zip(columns, x)}


def main():
    sql_connection = mysql.connector.connect(host='', user='', passwd='', database='')
    cursor = sql_connection.cursor()

    rename_cols = {'author': 'authors'}
    columns = ['zlibrary_id', 'title', 'author']
    cursor.execute(f'select {",".join(columns)} from books')
    with open('zlib.json', 'a') as f:
        for row in parse_cursor(cursor, columns):
            row['url'] = f'https://b-ok.cc/book/{row["zlibrary_id"]}'
            del row["zlibrary_id"]
            row = {rename_cols[k] if k in rename_cols else k: v for k, v in row.items()}
            row['authors'] = row['authors'].split(', ')
            f.write(json.dumps(row) + '\n')

    cursor.close()
    sql_connection.close()


if __name__ == '__main__':
    main()
