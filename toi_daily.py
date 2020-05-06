# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 23:21:48 2020

@author: praval
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.request
import mysql.connector
import os
from datetime import date
from datetime import timedelta 

# Credentials for Database
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

image_exists = 0
imgName = ''
text = ''

#get todays date so that we can get yesterday's date and scrape news articles (TOI has archives till yesterday in their archive page)
today = date.today()
yesterday = today - timedelta(days = 1)
year = yesterday.year
month = yesterday.month
day = yesterday.day
print(yesterday)

#get the DayCounter variable from the SURGEVariables table
conn = mysql.connector.connect(host=hostname, user=username, passwd=password, database=dbname)
db_cursor = conn.cursor()
sql_st = 'select Variable_Value from SURGEVariables where Variable_Name = "TOI_DayCounter"'
db_cursor.execute(sql_st)
dayCounter_result = db_cursor.fetchall()
dayCounter = dayCounter_result[0][0]

#update the dayCounter variable for next day in SURGEVariables table
sql_update = 'update SURGEVariables set Variable_Value=' + str(dayCounter + 1) + ' where Variable_Name = "TOI_DayCounter"'
db_cursor.execute(sql_update)
conn.commit()
db_cursor.close()
conn.close()

urlList = []
urlMonth = "http://timesofindia.indiatimes.com/" + str(year) + "/" + str(month) + "/" + str(day) + "/archivelist/year-" + str(year) + ",month-" + str(month)+ ",starttime-" + str(dayCounter) + ".cms"
print(urlMonth)
html_page = requests.get(urlMonth)
soup = BeautifulSoup(html_page.content, 'html.parser')
for link in soup.findAll('a'):
    url = str(link.get('href'))
    if (url.endswith('cms') and (url[0] == '/')):
        urlList.append("http://timesofindia.indiatimes.com" + str(link.get('href')))

del urlList[:4] ## Delete the first four links that do not point to articles
del urlList[-6:] ## Delete the last three links that do not point to articles

print(urlList.__sizeof__())
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
    title = soup.find('title')
    if title is None:
        i = i + 1
        continue

    else:
        title = soup.find('title').text
        
    # Extract the header with the date and author information
    byLine = soup.find(class_='as_byline')
    if byLine is not None:
        byLine = byLine.text
       # Find the article publication date
        index = str(byLine).find(':')
        index2 = str(byLine).find('IST')
        date = str(byLine)[index + 2:index2]

        # Find the author of the article
        index = str(byLine).find('TNN')
        index2 = str(byLine).find('Created')
        author = str(byLine)[index + 3:index2]
        header = author
        
    else:
        byLine = soup.find(class_='byline-content')
        if byLine is not None:
            byLine = byLine.text
            
        else:
            byLine = soup.find(class_='_3Mkg- byline')
            if byLine is not None:
                byLine = byLine.text
            else:
                byline = ''
        header = byLine

    # Extract article image
    imgClass = soup.find(class_='coverimgIn')
    if imgClass is not None:
        image_exists = 1
        img_src = imgClass.find('img').attrs['src']
        imgURL = 'https://timesofindia.indiatimes.com' + img_src
        imgName = str(year) + '-' + str(month) + '-' + str(day) + '-' + str(i) + '.jpg'

        
    # Extract the article text
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.decompose()  # rip it out

    article = soup.find(class_='Normal')
    if article is not None:
        text = article.text
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

    else:
        article = soup.find(class_='_3WlLe clearfix')
        if article is not None:
            text = article.text
            # break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
    '''
    if text is not None and title is not None and byLine is not None:
        #preprocess text to store text with escape character " for SQL database
        text = re.sub(r"\\", "", text)
        text = re.sub(r"\"", "\\\" ", text)
        title = re.sub(r"\"", "\\\" ", title)
        byLine = re.sub(r"\"", "\\\" ", byLine)

        # Create a connection to surge database and insert the news paper articles into table
        if len(text) > 0:
            conn = mysql.connector.connect(host=hostname, user=username, passwd=password, database=dbname)
            db_cursor = conn.cursor()
            sql_statement = 'INSERT INTO TimesOfIndia (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL, Image_Exist, Image_Name) VALUES (' + str(year) + ', ' + str(month) + ', ' + str(day) + ', ' + str(i) + ', "' + title + '", "' + byLine + '", "' + text + '", "' + urlLink + '", "' + str(image_exists) + '", "'+ imgName + '")' 
            try:
                db_cursor.execute(sql_statement)
                conn.commit()
            except:
                text = ''
                byLine = ''
                header = ''
                image_exists = 0
                imgName = ''
                i += 1
                continue

    '''
    # reset values of all the variabled=s for next loop
    text = ''
    byLine = ''
    header = ''
    image_exists = 0
    imgName = ''                
    i += 1

