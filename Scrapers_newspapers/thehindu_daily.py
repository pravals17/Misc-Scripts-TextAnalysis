# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 16:47:25 2020

@author: praval
"""

# The Hindu archives 2010 - 2019


import requests
from bs4 import BeautifulSoup
import re
import urllib.request
from urllib.request import Request, urlopen
import os
import mysql.connector
from datetime import date

# Database credentials for Surge in CSE Server
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

# Create the directory name where the images will be saved
base_dir = '/home/fac/surge/newspaper_data/'
dir_name = 'HINDU_IMAGES'
dir_path = os.path.join(base_dir, dir_name)

#Create the directory if already not there
if not os.path.exists(dir_path):
    os.mkdir(dir_path)

#get todays date so that we can scrape news articles published today
today = date.today()
year = today.year
month = today.month
day = today.day
print(today)

image_exists = 0 #Flag for image. its value when 0 means false else true
imgName = ''


urlList = []
urlMonth = "https://www.thehindu.com/archive/web/" + str(year) + "/" + str(month) + "/" + str(day) + "/"
print(urlMonth)
html_page = requests.get(urlMonth)
soup = BeautifulSoup(html_page.content, 'html.parser')
print('LIST')
alist = soup.find_all('ul', class_='archive-list') #'table', { "class" : "wikitable sortable"}
#print(alist)
for al in alist:
    for link in al.find_all('a', attrs={'href': re.compile("^https://www.thehindu.com/")}):
        urlList.append(link.get('href'))
        
print(urlList.__sizeof__())
i = 0
while i < len(urlList):
    num = 1
    fileName = str(year) + '-' + str(month) + '-' + str(day) + '-' + str(i)
    urlLink = urlList[i]

    try:
        page = requests.get(urlLink)
    except:
        i = i + 1
        continue
    soup = BeautifulSoup(page.text, 'html.parser')

    # Extract the title
    title = soup.find('title')
    if title is None:
        print('NO TITLE')
    else:
        title = soup.find('title').text
        index = str(title).find('-')
        title = title[:index].strip()

    # Extract the header with the date and author information
    author = soup.find(class_='auth-nm lnk')
    if author is not None:
        author = author.text.strip()
        header = author
        
    datetime = soup.find(class_='blue-color ksl-time-stamp')
    if datetime is not None:
        datetime = datetime.text.strip()
        header = datetime
        
    if author is not None and datetime is not None:
        header = author + " | " + datetime
    elif len(header) <= 0:
        header = None

    # Extract article image - NOT WORKING
    imgClass = soup.find(class_='img-container picture')
    if imgClass is not None:
       
        image_exists = 1
        index = str(imgClass).find('srcset="')
        index2 = str(imgClass).find('"/>')
        img_src = str(imgClass)[index+8:index2]
        imgURL = img_src
        imgName = str(year) + '-' + str(month) + '-' + str(day) + '-' + str(i) + '.jpg'

    # Extract the article text
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.decompose()  # rip it out

    article = soup.find(id=re.compile('^content-body-14269002-')) #16835231
    if article is not None:
        atext = article.text
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in atext.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        atext = '\n'.join(chunk for chunk in chunks if chunk)

        
    if atext is not None and title is not None and header is not None:
        #preprocess text to store text with escape character " for SQL database
        atext = re.sub(r"\\", "", atext)
        atext = re.sub(r"\"", "\\\" ", atext)
        title = re.sub(r"\"", "\\\" ", title)
        header = re.sub(r"\"", "\\\" ", header)
        
        # Create a connection to surge database and insert the news paper articles into table
        if len(atext) > 0:
            conn = mysql.connector.connect(host=hostname, user=username, passwd=password, database=dbname)
            db_cursor = conn.cursor()
            sql_statement = 'INSERT INTO TheHindu (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL, Image_Exist, Image_Name) VALUES (' + str(year) + ', ' + str(month) + ', ' + str(day) + ', ' + str(i) + ', "' + title + '", "' + header + '", "' + atext + '", "' + urlLink + '", "' + str(image_exists) + '", "'+ imgName + '")' 
            try:
                db_cursor.execute(sql_statement)
                conn.commit()
            except:
                atext = ''
                header = ''
                image_exists = 0
                imgName = ''
                i += 1
                continue
            
    # reset values of all the variabled=s for next loop
    atext = ''
    header = ''
    image_exists = 0
    imgName = ''
    i += 1

