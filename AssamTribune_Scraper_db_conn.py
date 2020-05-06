# The Assam Tribune archives 2011 - 2020
# http://www.assamtribune.com/scripts/detailsnew.asp?id=jan0111
# retrieve the list of urls and process each url individually

import requests
from bs4 import BeautifulSoup
import re
import mysql.connector

months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

image_exists = 0
imgName = '' 
# Credentials for Database
hostname = 'cse.unl.edu'
username = 'surge'
password = 'YU6gFU'
dbname = 'surge'

year = 2017
while year < 2020:
    dindex = 0
    for m in months:
        day = 1
        while day <= days[dindex]:
            artnum = 0
            urlList = []
            if day < 10:
                day = '0' + str(day)
            urlMonth = "http://www.assamtribune.com/scripts/detailsnew.asp?id=" + m + str(day) + str(year)[2:]

            try:
                html_page = requests.get(urlMonth)
            except:
                day = int(day) + 1
                continue
            soup = BeautifulSoup(html_page.content, 'html.parser')

            # Find all the links of individual article for a single day
            for link in soup.findAll('a'):
                if "detailsnew" in link.get('href'):
                    urlList.append("http://www.assamtribune.com/scripts/" + link.get('href'))

            if len(urlList) > 0:
                urlList.pop(0) ##Remove the day url from the list
            else:
                day = int(day) + 1
                continue
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
                    print(title)
                    
                    # Extract the body of the article
                    indexBegin = articleText.index("<!-- EXT_AssamTribune_Web_ROS_AS_MID,position=1-->")
                    indexEnd = articleText.index("<!-- EXT_AssamTribune_Web_ROS_AS_EOA,position=1-->")
                    
                    header = BeautifulSoup(articleText[indexTitleend:indexBegin], "html.parser").text
                    print(header)
                    
                    #get the index of content of the news
                    indexContent = articleText.index("<br>", ib)
                    indexContentstart = articleText.index("<br>", indexContent)
                    content = articleText[indexContentstart: indexEnd]
                                            
                    aText += articleText[ib:indexBegin] + " "
                    aText += articleText[indexBegin: indexEnd]
                    
                    print(indexDate)
                    print(indexDateend)
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
                    #with open(fileName, "w", encoding="utf-8") as artFile:
                    #artFile.write(link + "\n") ## Write the URL link
                    #artFile.write(cleantext + "\n") ## Write the article date and article text
                    if cleantext is not None and title is not None:
                    #preprocess text to store text with escape character " for SQL database
                        cleantext = re.sub(r"\\", "", cleantext)
                        cleantext = re.sub(r"\"", "\\\" ", cleantext)
                        title = re.sub(r"\"", "\\\" ", title)
                    #author = re.sub(r"\"", "\\\" ", author)
                    
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
                except:
                    continue

                
            day = int(day) + 1
        dindex += 1
    year += 1