# -*- coding: utf-8 -*-
"""
Created on Sun Feb  9 14:48:28 2020
"""
import requests
from bs4 import BeautifulSoup
import re
import urllib.request
import mysql.connector
import os

# Credentials for Database
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

num_skipped_articles = 0
base_dir = "/home/fac/surge/newspaper_data/"
dir_name = 'TOI_IMAGES'
dir_path = os.path.join(base_dir, dir_name)

#Create the directory if already not there
if not os.path.exists(dir_path):
    os.mkdir(dir_path)
    
months = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

year = 2020
dayCounter = 43831
image_exists = 0
imgName = ''
text = ''

while year <= 2020:
    mindex = 0
    dindex = 0
    while mindex < 12:
        day = 1
        while day <= days[dindex]:
            artnum = 0
            urlList = []
            urlMonth = "http://timesofindia.indiatimes.com/" + str(year) + "/" + str(months[mindex]) + "/" + str(day) + "/archivelist/year-" + str(year) + ",month-" + str(months[mindex])+ ",starttime-" + str(dayCounter) + ".cms"
            print(urlMonth)
            html_page = requests.get(urlMonth)
            soup = BeautifulSoup(html_page.content, 'html.parser')
            for link in soup.findAll('a'):
                url = str(link.get('href'))
                if (url.endswith('cms') and (url[0] == '/')):
                    urlList.append("http://timesofindia.indiatimes.com" + str(link.get('href')))
                    #print("http://timesofindia.indiatimes.com" + str(link.get('href'))
            del urlList[:4] ## Delete the first four links that do not point to articles
            del urlList[-3:] ## Delete the last three links that do not point to articles

            print(urlList.__sizeof__())
            i = 0
            while i < len(urlList):
                num = 1
                fileName = str(year) + '-' + str(months[mindex]) + '-' + str(day) + '-' + str(i)
                
                urlLink = urlList[i]
                print(urlLink)
                try:
                    page = requests.get(urlLink)
                except:
                    i=i+1
                    continue
                soup = BeautifulSoup(page.text, 'html.parser')

                # Extract the title
                title = soup.find('title')
                if title is None:
                    print('NO TITLE')
                    i = i + 1
                    continue
                    #artFile.write('NO TITLE' + "\n")
                else:
                    title = soup.find('title').text
                    #index = str(title).find('-')
                    #title = title[:index]
                    print(title)
                    #artFile.write(title + "\n")
                    
                # Extract the header with the date and author information
                byLine = soup.find(class_='as_byline')
                #print(byLine)
                if byLine is not None:
                    byLine = byLine.text
                   # Find the article publication date
                    index = str(byLine).find(':')
                    index2 = str(byLine).find('IST')
                    date = str(byLine)[index + 2:index2]
                    #artFile.write(date + "\n")

                    # Find the author of the article
                    index = str(byLine).find('TNN')
                    index2 = str(byLine).find('Created')
                    author = str(byLine)[index + 3:index2]
                    header = author
                    #artFile.write(author + "\n")
                else:
                    byLine = soup.find(class_='byline-content')
                    if byLine is not None:
                        byLine = byLine.text
                        #artFile.write(byLine + "\n")
                    else:
                        byLine = soup.find(class_='_3Mkg- byline')
                        if byLine is not None:
                            byLine = byLine.text
                        else:
                            byline = ''
                    header = byLine
                            #artFile.write(byLine + "\n")
                            # Extract the article text

                # Extract article image
               #with open(fileName, "w") as artFile:
                imgClass = soup.find(class_='coverimgIn')
                if imgClass is not None:
                    image_exists = 1
                    print(imgClass)
                    img_src = imgClass.find('img').attrs['src']
                    print(img_src)
                    imgURL = 'https://timesofindia.indiatimes.com' + img_src
                    imgName = str(year) + '-' + str(months[mindex]) + '-' + str(day) + '-' + str(i) + '.jpg'
                    #urllib.request.urlretrieve(imgURL, os.path.join(dir_path, imgName))
                    #artFile.write('IMAGE = '+ imgURL + "\n")
                        #imageName = imgName
                    #else:
                        #artFile.write('IMAGE NONE '+ "\n")
                    
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
                    #artFile.write(text + "\n")
                    #content = text
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
                        #artFile.write(text + "\n")
                        #content = text
                #print(content)
                print(len(text))
                print(byLine)
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
                        sql_statement = 'INSERT INTO TimesOfIndia (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL, Image_Exist, Image_Name) VALUES (' + str(year) + ', ' + str(months[mindex]) + ', ' + str(day) + ', ' + str(i) + ', "' + title + '", "' + byLine + '", "' + text + '", "' + urlLink + '", "' + str(image_exists) + '", "'+ imgName + '")' 
                        try:
                            db_cursor.execute(sql_statement)
                            conn.commit()
                        except:
                            num_skipped_articles +=1
                            print(num_skipped_articles)
                            text = ''
                            byLine = ''
                            header = ''
                            image_exists = 0
                            imgName = ''
                            i += 1
                            continue
                            
                
                # reset values of all the variabled=s for next loop
                text = ''
                byLine = ''
                header = ''
                image_exists = 0
                imgName = ''                
                i += 1

            day += 1
            dayCounter += 1
        mindex += 1
        dindex += 1
    year += 1
