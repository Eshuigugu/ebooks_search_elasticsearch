Collection of scripts to search many websites and APIs for books.


The *_to_json_dump.py scripts put a bunch of books into a ${source_name}.json file.   
Each book takes one line, and should have values for title, authors, and url. ASIN and ISBN optional

for libgen_fiction_sql_to_json_dump.py and libgen_nonfiction_sql_to_json_dump.py  
point them to the mysql host, database, and table

for myanonamouse_api_to_json_dump.py  
fill in mam_id

for trantor_api_to_json_dump.py  
point it to a TOR proxy.  
takes a long time to run from start to end  

ebook_hunter_html_to_json_dump.py should work as is.  
takes a long time to run

for overdrive_html_to_json_dump.py  
update the variable subdomains to the list of overdrive subdomains you use

for zlib_sql_to_json_dump.py 
get zlib metadata sql dump from http://2urmf2mk2dhmz4km522u4yfy2ynbzkbejf2cvmpcbzhpffvcuksrz6ad.onion/zlib-downloads.html
otherwise similar to the libgen_*_sql_to_json_dump.py scripts.

push_to_elasticsearch.py puts all the books onto elasticsearch


main.py searches for public domain books requested on myanonamouse using elasticsearch.  
Fill in mam_id to use it for that purpose

On my test run it took 3 seconds for each requested book and it got hits for 18% of the requested books.


Required python packages:  
appdirs==1.4.4  
beautifulsoup4==4.11.1  
jellyfish==0.8.2  
mysql_connector_repackaged==0.3.1  
requests==2.22.0  
requests_toolbelt==0.9.1  
tqdm==4.61.1  
