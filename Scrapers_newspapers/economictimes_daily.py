# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 18:42:49 2020

@author: praval
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.request
import os
import mysql.connector
from datetime import date
from datetime import timedelta 

# Database credentials for Surge in CSE Server
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'


image_exists = 0
imgName = ''
text = ''

#get todays date so that we can get yesterday's date and scrape news articles (ET has archives till yesterday in their archive page)
today = date.today()
yesterday = today - timedelta(days = 1)
year = yesterday.year
month = yesterday.month
day = yesterday.day
print(yesterday)

#get the DayCounter variable from the SURGEVariables table
conn = mysql.connector.connect(host=hostname, user=username, passwd=password, database=dbname)
db_cursor = conn.cursor()
sql_st = 'select Variable_Value from SURGEVariables where Variable_name = "ET_DayCounter"'
db_cursor.execute(sql_st)
dayCounter_result = db_cursor.fetchall()
dayCounter = dayCounter_result[0][0]


#update the dayCounter variable for next day
sql_update = 'update SURGEVariables set Variable_Value=' + str(dayCounter + 1) + ' where Variable_Name = "ET_DayCounter"'
db_cursor.execute(sql_update)
conn.commit()
db_cursor.close() #close the cursor
conn.close() #close the connection

urlList = []
urlMonth = "http://economictimes.indiatimes.com/archivelist/year-" + str(year) + ",month-" + str(month) +",starttime-" + str(dayCounter) + ".cms"
print(urlMonth)
try:
    html_page = requests.get(urlMonth)
except:
    exit
soup = BeautifulSoup(html_page.content, 'html.parser')

#Find the links for the articles
liDiv = soup.find_all('ul', class_='content')
for ultag in liDiv:
    alist = ultag.find_all('a')
    for link in alist:#, attrs={'href': re.compile("^http://economictimes.indiatimes.com//")}):
        print('http://economictimes.indiatimes.com//' + link.get('href'))
        urlList.append('http://economictimes.indiatimes.com/' + link.get('href'))
print('len =' + str(len(urlList)))
i = 0
while i < len(urlList):
    num = 1
    fileName = str(year) + '-' + str(month) + '-' + str(day) + '-' + str(i)
    urlLink = urlList[i]

    try:
        page = requests.get(urlLink)
    except:
        i=i+1
        continue
    soup = BeautifulSoup(page.text, 'html.parser')

    # Extract the title
    title = soup.find('h1', class_='clearfix title')
    if title is None:
        print('NO TITLE')
    else:
        title = title.text

    #Extract top-level summary
    summary = soup.find('h2', class_='title2')
    if summary is None:
        print('NO Summary')
        
    else:
        # Extract the article text
        # kill all script and style elements
        for script in summary(["script", "style"]):
            script.decompose()  # rip it out
        summaryT = summary.text
        print(summaryT)
        header = summaryT

    # Extract the header with the date and author information
    publishDate = soup.find('div', class_='publish_on')
    #print(byLine)
    if publishDate is not None:
        publishDate = publishDate.text
        # Find the article publication date
        index = str(publishDate).find(':')
        index2 = str(publishDate).find('IST')
        date = str(publishDate)[index + 2:index2]
        header = header + ' | ' + date
    # Extract the article text
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.decompose()  # rip it out

    article = soup.find(class_='artText')
    if article is not None:
        text = article.text
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        #content = text
        
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
            sql_statement = 'INSERT INTO EconomicTimes (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL) VALUES (' + str(year) + ', ' + str(month) + ', ' + str(day) + ', ' + str(i) + ', "' + title + '", "' + header + '", "' + text + '", "' + urlLink + '")' 
            try:
                db_cursor.execute(sql_statement)
                conn.commit()
            except:
                # reset values of all the variables for next loop
                text = ''
                header = ''
                image_exists = 0
                imageName = ''
                i += 1
                continue
    # reset values of all the variables for next loop if the except block is not executed
    text = ''
    header = ''
    image_exists = 0
    imageName = ''
    i += 1
