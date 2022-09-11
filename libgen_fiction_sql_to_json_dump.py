import mysql.connector
import json
import os


def parse_cursor(cursor, columns):
    for x in cursor:
        yield {k: v if type(v) != bytes else json.loads(v.decode()) for k, v in zip(columns, x)}


def main():
    sql_connection = mysql.connector.connect(host='', user='', passwd='', database='')
    cursor = sql_connection.cursor()

    rename_cols = {'Title': 'title', 'Author': 'authors'}
    columns = ['Title', 'Author', 'ASIN', 'MD5']
    cursor.execute(f'select {",".join(columns)} from fiction')
    with open('libgen_fiction.json', 'a') as f:
        for row in parse_cursor(cursor, columns):
            row['url'] = f'https://libgen.rs/fiction/{row["MD5"]}'
            del row["MD5"]
            row = {rename_cols[k] if k in rename_cols else k: v for k, v in row.items()}
            row['authors'] = row['authors'].split('; ')
            f.write(json.dumps(row) + '\n')

    cursor.close()
    sql_connection.close()


if __name__ == '__main__':
    main()
