# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 17:49:18 2020

@author: praval
"""

# The Pioneer India - Archives
# https://www.dailypioneer.com/archive/
# https://www.dailypioneer.com/searchlist.php?yr=2011&mn=1

import requests
from bs4 import BeautifulSoup
import re
import urllib.request
from urllib.request import Request, urlopen
import os
import mysql.connector
from datetime import date
from datetime import timedelta 

# Database credentials for Surge in CSE Server
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

 #cron job runs firs day of every month and downloads articles from the previous month
today = date.today()
yesterday = today - timedelta(days = 1)
year = yesterday.year
month = yesterday.month

image_exists = 0 #Flag for image. its value when 0 means false else true


artnum = 0
urlList = []

urlMonth = "https://www.dailypioneer.com/searchlist.php?yr=" + str(year) + "&mn=" + str(month)
print(urlMonth)

html_page = requests.get(urlMonth)
soup = BeautifulSoup(html_page.content, 'html.parser')

#Find the pages and the last page id
pgList = []
pageDiv = soup.find('div', class_='pagingList')
if pageDiv is not None:
    pageList = pageDiv.find_all('a')
    lastPage = pageList[-1].get('id')
    print('lastpage = ' + lastPage)
    for index in range(1, int(lastPage)+1):
        pageLink = 'https://www.dailypioneer.com//searchlist.php?yr=' + str(year) + '&mn=' + str(month) + '&page=' + str(index)
        pgList.append(pageLink)
else:
    pgList.append(urlMonth)
    
for pg in pgList:
    html_page = requests.get(pg)
    soup = BeautifulSoup(html_page.content, 'html.parser')
    ## Find the main story link
    print('BIG NEWS ' + str(year) + ' &mn= ' + str(month) )
    alist = soup.find_all('div', class_='BigNews')
    for al in alist:
        link = al.find('a')
        link = 'https://www.dailypioneer.com/'+link.get('href')
        urlList.append(link)

    ## Find the other story links
    inlist = soup.find_all('div', class_='row newsWrap no-gutters')
    if inlist is not None:
        for il in inlist:
            ilist = il.find('a')
            ilink = 'https://www.dailypioneer.com/' + ilist.get('href')
            urlList.append(ilink)

no = 1
for lk in urlList:
    try:
        html_page = requests.get(lk)
    except:
        continue
    soup = BeautifulSoup(html_page.content, 'html.parser')
    if soup.find(itemprop="headline") is not None:
        title = soup.find(itemprop="headline").get_text()
        fileName = str(year) + '-' + str(month) + '-' + str(no)
        
            ## Get Story details
        date = soup.find(itemprop="datePublished").get_text()
        print(date)
        day = date.split(' ')[1]
        author = soup.find(itemprop="author").get_text()
        header = author + " | " + date

            ## find the image
        imageDiv = soup.find(itemprop="image")
        if imageDiv is not None:
            image_exists = 1
            imgURL = imageDiv.find('img').attrs['src']
            imgName = str(year) + '-' + str(month) + '-' + str(no) + '.jpg'
            imageName = imgName
        else:
            imageName = ''
        
        text = soup.find(itemprop="articleBody").get_text().strip()
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
 
        if text is not None and not title is None and header is not None:
            # preprocess text to store text with escape character " for SQL database
            text = re.sub(r"\\", "", text)
            text = re.sub(r"\"", "\\\" ", text)
            title = re.sub(r"\"", "\\\" ", title)
            header = re.sub(r"\"", "\\\" ", header)
            
            # Create a connection to surge database and insert the news paper articles into table
            if len(text) > 0:
                conn = mysql.connector.connect(host=hostname, user=username, passwd=password, database=dbname)
                db_cursor = conn.cursor()
                sql_statement = 'INSERT INTO ThePioneer (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL, Image_Exist, Image_Name) VALUES (' + str(year) + ', ' + str(month) + ', ' + str(day) + ', ' + str(no) + ', "' + title + '", "' + header + '", "' + text + '", "' + lk + '", "' + str(image_exists) + '", "'+ imageName + '")' 
                try:
                    db_cursor.execute(sql_statement)
                    conn.commit()
                except:
                    no = no + 1
                    text = ''
                    header = ''
                    image_exists = 0
                    imageName = ''
                    continue

        # reset values of all the variabled=s for next loop
        text = ''
        header = ''
        image_exists = 0
        imageName = ''
        no = no + 1
