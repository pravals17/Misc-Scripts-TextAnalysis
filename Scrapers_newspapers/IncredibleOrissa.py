# Incredible Orissa - Archives
# https://incredibleorissa.com/odia-news/
# https://incredibleorissa.com/odia-news/page/1/

import requests
from bs4 import BeautifulSoup
import re
import urllib.request
from urllib.request import Request, urlopen
import os
import mysql.connector

# Credentials for Database
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

urlMain = "https://incredibleorissa.com/odia-news/page/1/"
image_exists = 0
imgName = '' 

html_page = requests.get(urlMain)
soup = BeautifulSoup(html_page.content, 'html.parser')

# Find the pages and the last page id
pgList = []
pageDiv = soup.find('div', class_='pagination')
if pageDiv is not None:
    pageList = pageDiv.find_all('a')
    lastPage = pageList[-1].get('href')
    s = lastPage.split('https://incredibleorissa.com/odia-news/page/')
    s2 = s[-1].split('/')
    lpIndex = int(s2[0])
    print(lpIndex)
    for index in range(1, lpIndex + 1):
        pageLink = 'https://incredibleorissa.com/odia-news/page/' + str(index)
        pgList.append(pageLink)
        print(pageLink)

for pg in pgList:
    html_page = requests.get(pg)
    soup = BeautifulSoup(html_page.content, 'html.parser')
    urlList = []
    ## Find the article links
    inlist = soup.find_all('span', class_='readMore')
    # print(inlist)
    if inlist is not None:
        for il in inlist:
            ilist = il.find('a')
            ilink = ilist.get('href')
            urlList.append(ilink)
            print('iILIST = ' + ilink)
            # print(ilist)
    print(len(urlList))
    no = 1
    for lk in urlList:
        try:
            html_page = requests.get(lk)
        except:
            continue
        soup = BeautifulSoup(html_page.content, 'html.parser')
        if soup.find('h1', class_="title single-title") is not None:
            title = soup.find('h1', class_="title single-title").get_text()
            dateTime = soup.find('span', class_="thetime").get_text()
            fileName = '/Volumes/GD/IO/Articles/' + str(dateTime) + '-' + str(no)
            month = months.index(dateTime.split(' ')[0]) + 1
            day = int(dateTime.split(' ')[1].replace(',', ''))
            year = int(dateTime.split(' ')[2])
            
            print(lk)
            print(fileName)
            print(dateTime)
            '''
            with open(fileName, "w", encoding="utf-8") as artFile:
                ## Get Story details
                artFile.write(lk + "\n")
                artFile.write(title + "\n")
                artFile.write(dateTime + "\n")
                author = soup.find('span', class_="theauthor").get_text()
                artFile.write(author + "\n")
                '''
            author = soup.find('span', class_="theauthor").get_text()
            article = soup.find('div', class_='post-single-content box mark-links')
            articleText = article.find_all('p')
                
            text = ''
            for p in articleText:
                text = text + p.get_text()
            
            if text is not None and title is not None:
                #preprocess text to store text with escape character " for SQL database
                text = re.sub(r"\\", "", text)
                text = re.sub(r"\"", "\\\" ", text)
                title = re.sub(r"\"", "\\\" ", title)
                author = re.sub(r"\"", "\\\" ", author)
                
                # Create a connection to surge database and insert the news paper articles into table
                if len(text) > 0:
                    conn = mysql.connector.connect(host=hostname, user=username, passwd=password, database=dbname)
                    db_cursor = conn.cursor()
                    sql_statement = 'INSERT INTO IncredibleOrissa (Year_Pub, Month_Pub, Day_Pub, Article_Num, Title, Header, Content, Source_URL, Image_Exist, Image_Name) VALUES (' + str(year) + ', ' + str(month) + ', ' + str(day) + ', ' + str(no) + ', "' + title + '", "' + author + '", "' + text + '", "' + lk + '", "' + str(image_exists) + '", "'+ imgName + '")' 
                    try:
                        db_cursor.execute(sql_statement)
                        conn.commit()
                    except:
                        text = ''
                        header = ''
                        image_exists = 0
                        imgName = ''
                        no = no + 1
                        continue

                # reset values of all the variabled=s for next loop
            text = ''
            byLine = ''
            header = ''
            image_exists = 0
            imgName = ''                
            no = no + 1