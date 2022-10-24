# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 17:29:15 2020

"""

# Economic Times 2001 - 2020
# Each day's links are available at:https://economictimes.indiatimes.com/archive.cms
# From here, for each year and month and day, build links as:
# https://economictimes.indiatimes.com/archivelist/year-2001,month-1,starttime-36892.cms
# retrieve the list of urls and process each url individually

import requests
from bs4 import BeautifulSoup
import re
import urllib.request
import os
import mysql.connector

# Database credentials for Surge in CSE Server
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

# Create the directory name where the images will be saved
#base_dir = "D:/"
#dir_name = 'ThePioneer_IMAGES'
#dir_path = os.path.join(base_dir, dir_name)

#Create the directory if already not there
#if not os.path.exists(dir_path):
   #os.mkdir(dir_path)

num_skipped_articles = 0

months = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

year = 2020
dayCounter = 44092

while year <= 2020:
    mindex = 0
    dindex = 0
    if year == 2020 and dayCounter == 44092:
        mindex = 8
        dindex = 8
    while mindex < 12:
        day = 1
        if year == 2020 and mindex == 6:
            day = 18
        while day <= days[dindex]:
            artnum = 0
            urlList = []
            urlMonth = "http://economictimes.indiatimes.com/archivelist/year-" + str(year) + ",month-" + str(months[mindex]) +",starttime-" + str(dayCounter) + ".cms"
            print(urlMonth)
            try:
                html_page = requests.get(urlMonth)
            except:
                continue
            soup = BeautifulSoup(html_page.content, 'html.parser')

            #Find the links for the articles
            liDiv = soup.find_all('ul', class_='content')
            for ultag in liDiv:
                alist = ultag.find_all('a')
                for link in alist:#, attrs={'href': re.compile("^http://economictimes.indiatimes.com//")}):
                    print('http://economictimes.indiatimes.com//' + link.get('href'))
                    urlList.append('http://economictimes.indiatimes.com' + link.get('href'))
            print('len =' + str(len(urlList)))
            i = 0
            while i < len(urlList):
                num = 1
                fileName = str(year) + '-' + str(months[mindex]) + '-' + str(day) + '-' + str(i)
                #with open(fileName, "w", encoding="utf-8") as artFile:
                urlLink = urlList[i]
                print(urlLink)
                #artFile.write(urlLink + "\n")
                try:
                    page = requests.get(urlLink)
                except:
                    i=i+1
                    continue
                soup = BeautifulSoup(page.text, 'html.parser')

                # Extract the title
                title = soup.find('h1', class_='artTitle font_faus')
                if title is None:
                    print('NO TITLE')
                    #artFile.write('NO TITLE' + "\n")
                else:
                    title = title.text
                    print(title)
                    #artFile.write(title + "\n")

                #Extract top-level summary
                summary = soup.find('h2', class_='summary')
                if summary is None:
                    print('NO Summary')
                    #artFile.write('NO Summary' + "\n")
                else:
                    # Extract the article text
                    # kill all script and style elements
                    for script in summary(["script", "style"]):
                        script.decompose()  # rip it out
                    summaryT = summary.text
                    print(summaryT)
                    header = summaryT
                    #artFile.write(summaryT + "\n")
                    # if  summary.find('img') is not None:
                    #     image = summary.find('img')
                    #     imgURL = 'http://economictimes.indiatimes.com/' + image.attrs['src']
                    #     imgName = str(year) + '-' + str(m) + '-' + str(no) + '.jpg'
                    #     urllib.request.urlretrieve(imgURL, os.path.join(dir_path, imgName))

                # Extract the header with the date and author information
                publishDate = soup.find('div', class_='publish_on')
                #print(byLine)
                if publishDate is not None:
                    publishDate = publishDate.text
                    # Find the article publication date
                    index = str(publishDate).find(':')
                    index2 = str(publishDate).find('IST')
                    date = str(publishDate)[index + 2:index2]
                    #artFile.write(date + "\n")
                    header = header + ' | ' + date
                # Extract the article text
                # kill all script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()  # rip it out

                article = soup.find(class_='artText')
               #print(article)
                
                if article is not None:
                    text = article.text
                    # break into lines and remove leading and trailing space on each
                    lines = (line.strip() for line in text.splitlines())
                    # break multi-headlines into a line each
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    # drop blank lines
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    #content = text
                    #artFile.write(text + "\n")
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
                        sql_statement = 'INSERT INTO EconomicTimes (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL) VALUES (' + str(year) + ', ' + str(months[mindex]) + ', ' + str(day) + ', ' + str(i) + ', "' + title + '", "' + header + '", "' + text + '", "' + urlLink + '")' 
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
            day += 1
            
            dayCounter += 1
        mindex += 1
        dindex += 1
    year += 1
