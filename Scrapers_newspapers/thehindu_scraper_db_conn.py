# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 22:25:21 2020
"""

# The Hindu archives 2010 - 2019


import requests
from bs4 import BeautifulSoup
import re
import urllib.request
from urllib.request import Request, urlopen
import os
import mysql.connector

# Database credentials for Surge in CSE Server
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

num_skipped_articles = 0

# Create the directory name where the images will be saved
base_dir = '/home/fac/surge/newspaper_data/'
dir_name = 'HINDU_IMAGES'
dir_path = os.path.join(base_dir, dir_name)

#Create the directory if already not there
if not os.path.exists(dir_path):
    os.mkdir(dir_path)


months = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

year = 2011
image_exists = 0 #Flag for image. its value when 0 means false else true
imgName = ''

while year <= 2020:
    mindex = 0
    dindex = 0
    while mindex < 12:
        day = 1
        while day <= days[dindex]:
            artnum = 0
            urlList = []
            urlMonth = "https://www.thehindu.com/archive/web/" + str(year) + "/" + str(months[mindex]) + "/" + str(day)
            print(urlMonth)
            html_page = requests.get(urlMonth)
            soup = BeautifulSoup(html_page.content, 'html.parser')
            print('LIST')
            alist = soup.find_all('ul', class_='archive-list') #'table', { "class" : "wikitable sortable"}
            #print(alist)
            for al in alist:
                for link in al.find_all('a', attrs={'href': re.compile("^https://www.thehindu.com/")}):
                    urlList.append(link.get('href'))
                    #print(link.get('href'))
            print(urlList.__sizeof__())
            i = 0
            while i < len(urlList):
                num = 1
                fileName = str(year) + '-' + str(months[mindex]) + '-' + str(day) + '-' + str(i)
                
                urlLink = urlList[i]
                print(urlLink)
                #artFile.write(urlLink + "\n")
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
                    #artFile.write('NO TITLE' + "\n")
                else:
                    title = soup.find('title').text
                    index = str(title).find('-')
                    title = title[:index].strip()
                    print(title)
                    #artFile.write(title + "\n")

                # Extract the header with the date and author information
                author = soup.find(class_='auth-nm lnk')
                if author is not None:
                    author = author.text.strip()
                    header = author
                    #artFile.write('AUTHOR = ' + author + "\n")
                datetime = soup.find(class_='blue-color ksl-time-stamp')
                if datetime is not None:
                    datetime = datetime.text.strip()
                    header = datetime
                    #artFile.write('DATETIME = ' + datetime + "\n")
                if author is not None and datetime is not None:
                    header = author + " | " + datetime
                elif len(header) <= 0:
                    header = None

                # Extract article image - NOT WORKING
                #with open(fileName, "w", encoding="utf-8") as artFile:
                imgClass = soup.find(class_='img-container picture')
                if imgClass is not None:
                    #print(imgClass)
                    image_exists = 1
                    index = str(imgClass).find('srcset="')
                    index2 = str(imgClass).find('"/>')
                    img_src = str(imgClass)[index+8:index2]
                    #img_src = imgClass.find('source', media='min-width: 1281px',attrs=['srcset'])
                    print(img_src)
                    imgURL = img_src
                    imgName = str(year) + '-' + str(months[mindex]) + '-' + str(day) + '-' + str(i) + '.jpg'
                    #req = Request(imgURL, headers={'User-Agent': 'Mozilla/5.0'})
    
                    #artFile.write('IMAGE = ' + imgURL + "\n")
                        #imageName = imgName
                    #else:
                        #artFile.write('IMAGE NONE ' + "\n")

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
                    #content = atext
                    #artFile.write('TEXT = ' + atext + "\n")
                    
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
                        sql_statement = 'INSERT INTO TheHindu (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL, Image_Exist, Image_Name) VALUES (' + str(year) + ', ' + str(months[mindex]) + ', ' + str(day) + ', ' + str(i) + ', "' + title + '", "' + header + '", "' + atext + '", "' + urlLink + '", "' + str(image_exists) + '", "'+ imgName + '")' 
                        try:
                            db_cursor.execute(sql_statement)
                            conn.commit()
                        except:
                            num_skipped_articles +=1
                            print(num_skipped_articles)
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

            day += 1
        mindex += 1
        dindex += 1
    year += 1
