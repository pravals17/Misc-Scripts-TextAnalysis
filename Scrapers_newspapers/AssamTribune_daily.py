# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 00:11:50 2020

@author: praval
"""

# The Assam Tribune archives 2011 - 2020
# http://www.assamtribune.com/scripts/detailsnew.asp?id=jan0111
# retrieve the list of urls and process each url individually

import requests
from bs4 import BeautifulSoup
import re
import mysql.connector
from datetime import date

months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

#get today's date to scrape news from today
today = date.today()
year = today.year
month = today.month
day = today.day
m = months[month - 1]
print(today)

image_exists = 0
imgName = '' 

# Credentials for Database
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'


artnum = 0
urlList = []
if day < 10:
    day = '0' + str(day)
urlMonth = "http://www.assamtribune.com/scripts/detailsnew.asp?id=" + m + str(day) + str(year)[2:]

try:
    html_page = requests.get(urlMonth)
except:
    exit
soup = BeautifulSoup(html_page.content, 'html.parser')

# Find all the links of individual article for a single day
for link in soup.findAll('a'):
    try:
        if "detailsnew" in link.get('href'):
            urlList.append("http://www.assamtribune.com/scripts/" + link.get('href'))
    except:
        continue
if len(urlList) > 0:
    urlList.pop(0) ##Remove the day url from the list
    
month = months.index(m) + 1
num = 1
for link in urlList:
    try:
        page = requests.get(link)
        soup = BeautifulSoup(page.text, 'html.parser')

        # Extract the article text
        articleText = page.text
        # Extract the location and date information
        indexDate = articleText.index("<font face=\"Verdana\" color=\"#FFFFFF\" size=-2>")
        indexDateend = articleText.index("</b>", indexDate)
        aText = articleText[indexDate: indexDateend]
        ib = articleText.index("<font size=+1>")
        
        #extract title of the news article
        indexTitleend = articleText.index("<br>", ib)
        title = articleText[ib+ len('<font size=+1>'):indexTitleend]
        
        # Extract the body of the article
        indexBegin = articleText.index("<!-- EXT_AssamTribune_Web_ROS_AS_MID,position=1-->")
        indexEnd = articleText.index("<!-- EXT_AssamTribune_Web_ROS_AS_EOA,position=1-->")
        
        header = BeautifulSoup(articleText[indexTitleend:indexBegin], "html.parser").text
        
        #get the index of content of the news
        indexContent = articleText.index("<br>", ib)
        indexContentstart = articleText.index("<br>", indexContent)
        content = articleText[indexContentstart: indexEnd]
                                
        aText += articleText[ib:indexBegin] + " "
        aText += articleText[indexBegin: indexEnd]

        # Remove any html tags from the article text
        #cleantext = BeautifulSoup(aText, "html.parser").text
        cleantext = BeautifulSoup(content, "html.parser").text
        
        # Remove extra line breaks
        lines = (line.strip() for line in cleantext.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        cleantext = '\n'.join(chunk for chunk in chunks if chunk)


        fileName = 'E:\\00Data\\AssamTribune\\Articles\\' + str(year) + '-' + str(m) + '-' + str(
            day) + '-' + str(num)
        
        if cleantext is not None and title is not None:
        #preprocess text to store text with escape character " for SQL database
            cleantext = re.sub(r"\\", "", cleantext)
            cleantext = re.sub(r"\"", "\\\" ", cleantext)
            title = re.sub(r"\"", "\\\" ", title)
        
        # Create a connection to surge database and insert the news paper articles into table
            if len(cleantext) > 0:
                conn = mysql.connector.connect(host=hostname, user=username, passwd=password, database=dbname)
                db_cursor = conn.cursor()
                sql_statement = 'INSERT INTO AssamTribune (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL, Image_Exist, Image_Name) VALUES (' + str(year) + ', ' + str(month) + ', ' + str(day) + ', ' + str(num) + ', "' + title + '", "' + header + '", "' + cleantext + '", "' + link + '", "' + str(image_exists) + '", "'+ imgName + '")' 
                try:
                    db_cursor.execute(sql_statement)
                    conn.commit()
                except:
                    cleantext = ''
                    title = ''
                    num += 1
                    continue

        num += 1
        cleantext = ''
        title = ''
    except:
        continue