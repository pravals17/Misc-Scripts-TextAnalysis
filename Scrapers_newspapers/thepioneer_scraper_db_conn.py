# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 23:17:17 2020

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

# Database credentials for Surge in CSE Server
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

num_skipped_articles = 0
# # Create the directory name where the images will be saved
dir_path = '/home/fac/surge/newspaper_data/ThePioneer_Images/'
# #Create the directory if already not there
if not os.path.exists(dir_path):
    os.mkdir(dir_path)


months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
year = 2013

image_exists = 0 #Flag for image. its value when 0 means false else true

while year <= 2020:        
    for m in months:
        if year == 2013 and m < 12:
            continue
        artnum = 0
        urlList = []

        urlMonth = "https://www.dailypioneer.com/searchlist.php?yr=" + str(year) + "&mn=" + str(m)
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
                pageLink = 'https://www.dailypioneer.com//searchlist.php?yr=' + str(year) + '&mn=' + str(m) + '&page=' + str(index)
                pgList.append(pageLink)
                #print(pageLink)
            # for pg in pageList:
            #     pageLink = pg.get('href')
            #     pageLink = 'https://www.dailypioneer.com/' + str(pageLink)
            #     pgList.append(pageLink)
            #     print(pageLink)
        else:
            pgList.append(urlMonth)
        for pg in pgList:
            html_page = requests.get(pg)
            soup = BeautifulSoup(html_page.content, 'html.parser')
            ## Find the main story link
            print('BIG NEWS ' + str(year) + ' &mn= ' + str(m) )
            alist = soup.find_all('div', class_='BigNews')
            for al in alist:
                link = al.find('a')
                link = 'https://www.dailypioneer.com/'+link.get('href')
                urlList.append(link)
                #print(link)

            ## Find the other story links
            inlist = soup.find_all('div', class_='row newsWrap no-gutters')
            #print(inlist)
            if inlist is not None:
                for il in inlist:
                    ilist = il.find('a')
                    ilink = 'https://www.dailypioneer.com/' + ilist.get('href')
                    urlList.append(ilink)
                        #print('iILIST = ' + ilink)
                    #print(ilist)
        print(len(urlList))
        no = 1
        for lk in urlList:
            try:
                html_page = requests.get(lk)
            except:
                continue
            soup = BeautifulSoup(html_page.content, 'html.parser')
            if soup.find(itemprop="headline") is not None:
                title = soup.find(itemprop="headline").get_text()
                fileName = str(year) + '-' + str(m) + '-' + str(no)
                print(lk)
                print(fileName)
                
                    ## Get Story details
                #artFile.write(lk + "\n")
                #artFile.write(title+ "\n")
                date = soup.find(itemprop="datePublished").get_text()
                print("Date:")
                print(date)
                day = date.split(' ')[1]
                #artFile.write(date+ "\n")
                author = soup.find(itemprop="author").get_text()
                
                header = author + " | " + date
                #artFile.write(author+ "\n")
                    ## find the image
                #with open(fileName, "w", encoding="utf-8") as artFile:
                imageDiv = soup.find(itemprop="image")
                if imageDiv is not None:
                    image_exists = 1
                    imgURL = imageDiv.find('img').attrs['src']
                    imgName = str(year) + '-' + str(m) + '-' + str(no) + '.jpg'
                    print("image alt = " + imageDiv.find('img').attrs['alt'] + "\n")
                    #try:
                    #urllib.request.urlretrieve(imgURL, os.path.join(dir_path, imgName))
                    imageName = imgName
                    #except urllib.request.HTTPError:
                        #imageName = ''
                        #artFile.write("Image not retrieved" + "\n")
                else:
                    imageName = ''
                
                text = soup.find(itemprop="articleBody").get_text().strip()
                # break into lines and remove leading and trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)
                #content = text
                    #artFile.write(text+ "\n")
 
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
                        sql_statement = 'INSERT INTO ThePioneer (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL, Image_Exist, Image_Name) VALUES (' + str(year) + ', ' + str(m) + ', ' + str(day) + ', ' + str(no) + ', "' + title + '", "' + header + '", "' + text + '", "' + lk + '", "' + str(image_exists) + '", "'+ imageName + '")' 
                        try:
                            db_cursor.execute(sql_statement)
                            conn.commit()
                        except:
                            num_skipped_articles +=1
                            print(num_skipped_articles)
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
    year = year + 1
