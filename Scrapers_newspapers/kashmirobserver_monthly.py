# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 12:19:35 2020

@author: praval
"""

# Kashmir Observer - Archives
# https://kashmirobserver.net/news/local-news/
# https://kashmirobserver.net/news/local-news/page/1/

import requests
from bs4 import BeautifulSoup
import re
import mysql.connector
from datetime import date
from datetime import timedelta 

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

 #cron job runs firs day of every month and downloads articles from the previous month
today = date.today()
yesterday = today - timedelta(days = 1)
year = yesterday.year
month = yesterday.month

print(today)

urlMain = "https://kashmirobserver.net/" + str(year) + "/" + str(month) + "/page/1/"
image_exists = 0
imgName = '' 
# Credentials for Database
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

html_page = requests.get(urlMain)
soup = BeautifulSoup(html_page.content, 'html.parser')

# Find the pages and the last page id
pgList = []
pageDiv = soup.find('div', class_='archive-pagination')
if pageDiv is not None:
    pageList = pageDiv.find_all('a')
    lastPage = pageList[-2].get('href')
    s = lastPage.split("https://kashmirobserver.net/" + str(year) + "/" + str(month) + "/page/")
    s2 = s[-1].split('/')
    lpIndex = int(s2[0])
    for index in range(1, lpIndex + 1):
        pageLink = "https://kashmirobserver.net/" + str(year) + "/" + str(month) + "/page/" + str(index) +'/'
        pgList.append(pageLink)

for pg in pgList:
    print(pg)
    html_page = requests.get(pg)
    soup = BeautifulSoup(html_page.content, 'html.parser')
    urlList = []
    ## Find the article links
    inlist = soup.find_all('article')
    if inlist is not None:
        for il in inlist:
            ilist = il.find('a')
            ilink = ilist.get('href')
            urlList.append(ilink)           
    
    no = 1
    for lk in urlList:
        try:
            html_page = requests.get(lk)
            soup = BeautifulSoup(html_page.content, 'html.parser')
            if soup.find('h1', class_="post-title") is not None:
                title = soup.find('h1', class_="post-title").get_text()
                dateTime = soup.find('p', class_="single_postmeta").get_text()
                dateTime = dateTime.split()
                dateTime = dateTime[1] + ','+ dateTime[2] + dateTime[3]
    
                month = months.index(dateTime.split(',')[0]) + 1
                day = int(dateTime.split(',')[1])
                year = int(dateTime.split(',')[2])
                
                fileName = 'E:\\00Data\\KashmiriObserver\\Articles\\' + str(dateTime) + '-' + str(no)
                    ## Get Story details
    
                # Extract the article text
                # kill all script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()  # rip it out
    
                article = soup.find('article')
                texts = article.find_all('p')
                text = ''
                for t in texts[0:-9]:
                    text+= t.get_text() + '\n'
                # break into lines and remove leading and trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)

                if text is not None and title is not None:
                    #preprocess text to store text with escape character " for SQL database
                    text = re.sub(r"\\", "", text)
                    text = re.sub(r"\"", "\\\" ", text)
                    title = re.sub(r"\"", "\\\" ", title)
                    # Create a connection to surge database and insert the news paper articles into table
                    if len(text) > 0:
                        conn = mysql.connector.connect(host=hostname, user=username, passwd=password, database=dbname)
                        db_cursor = conn.cursor()
                        sql_statement = 'INSERT INTO KashmirObserver (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL, Image_Exist, Image_Name) VALUES (' + str(year) + ', ' + str(month) + ', ' + str(day) + ', ' + str(no) + ', "' + title + '", "' + dateTime + '", "' + text + '", "' + lk + '", "' + str(image_exists) + '", "'+ imgName + '")' 
                        try:
                            db_cursor.execute(sql_statement)
                            conn.commit()
                        except:
                            text = ''
                            title = ''
                            no = no + 1
                            continue
                    no = no + 1
                    text = ''
                    title = ''
            
        except:
            continue
