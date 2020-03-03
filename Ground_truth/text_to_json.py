# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 23:03:40 2020

@author: praval
"""
# Create an pre-annoteted JSON file using StanforNER to be uploaded to dataturks for ground truth generation
import nltk
from nltk.tag import StanfordNERTagger
from nltk import tokenize
import json
import unicodedata
import re
import os

def clean_sentences(string):
    string = unicodedata.normalize("NFKD", string)
    string = re.sub(r"\\", " ", string)
    string = re.sub(r"\'", " ", string)
    string = re.sub(r"\"", " ", string)
    string = re.sub(r"\n", " ", string)
    string = re.sub(r"=", " ", string)
    string = re.sub(r"-", " ", string)
    string = re.sub(r"/", " ", string)
    #string = re.sub(r".", " ", string)
    return string.strip()

def concat_placenames(original_tags):
    locations = []
    l = len(original_tags)
    i=0;
    # Iterate over the tagged words.
    while i<l:
        #print(i)
        e,t = original_tags[i];
        # If it's a location, then check the next 3 words.
        if t == 'LOCATION':
            j = 1;
            s = e; 
            # Verify the tags for the next 3 words.
            while i+j<len(original_tags):
                # If the next words are also locations, then concatenate them to make a large string.
                if original_tags[i+j][1] == 'LOCATION':
                    s = s+" "+original_tags[i+j][0];
                    j+=1;
                else:
                    break;
            i = i+j;
            # Save the locations to a locations list
            locations+=[s];
        else:
            i=i+1;
        #print(locations)
    return locations

def get_JSON(sent, count_articles_tagged_by_stanfordNER):
    
    st = StanfordNERTagger('C:/Users/prava/Downloads/stanford-ner-2018-10-16/stanford-ner-2018-10-16/classifiers/english.all.3class.distsim.crf.ser.gz', 'C:/Users/prava/Downloads/stanford-ner-2018-10-16/stanford-ner-2018-10-16/stanford-ner.jar', encoding='utf-8') 
    #sent = 'Bengaluru: Hundreds march on Borewell Road against government\'s apathy. BENGALURU: More than 200 residents of BBMP s Mahadevapura Zone walked peacefully this morning on Borewell Road in Whitefield, demanding restoration of the road and civic amenities. Citizens marched the 1.5 km stretch from the post office to the Ambedkar statue, while around 200 children and residents stood with placards in solidarity for the cause. Organised by Nallurahalli Rising along with Whitefield Rising, the protest in Hagadur ward drew people Kadugudi, Garadacharpalya and Hoodi wards.Led by a band of drummers and accompanied by a contingent of police, traffic police and traffic wardens, the protesters held placards, wore black and donned masks, to symbolise the pathetic condition of one of Whitefield s oldest roads. The reasons for the protest are many: poor road conditions, garbage strewn roads, fatal accidents due to water tankers that even the police cannot seem to control and all this in Nallurahalli and Whitefield itself. Residents say that six fatal road accidents have taken place over the past year. And there are many minor accidents too.The road is too narrow for the volume of traffic, there are also numerous shops that encroach footpaths and make parking difficult.Nearby roads from Ramagondanahalli and Siddhapura, the Nallurahalli New Temple Road, Outer Circle and Inner Circle are also similarly affected.Half of the streetlights, they say, do not function. One of their main problems is regarding the Under ground drainage work that began in August 2016, and was scheduled to be completed in October, of the same year. The BWSSB has dug up the road and left it open, this despite, repeated requests made to the BWSSB and BBMP.Residents say that the BWSSB contractor has just poured quarry dust and pebbles wherever pits and channels have been dug, and that this is dangerous for pedestrians, cyclists and two wheelersAs a resident put it, Borewell Road (and much of Whitefield) is sinking and stinking! A portion of Outer Circle caved in when an SUV passed by on Monday. This was a chance for people\'s voices to be heard.'
    sent = clean_sentences(sent)
    #sent = sent_cleaned.replace(".", " ")
    text_tags = nltk.word_tokenize(sent)
    
    original_tags = st.tag(text_tags)
    
    data_dict = {}
    sent_cleaned = clean_sentences(sent)
    locations = concat_placenames(original_tags)
    list_set = set(locations) 
    # convert the set to the list 
    unique_locs = (list(list_set))
    if len(unique_locs) > 0:
        count_articles_tagged_by_stanfordNER = count_articles_tagged_by_stanfordNER + 1
    
    data_dict['content'] = sent_cleaned
    
    annotation = []
    #data_dict['annotation'] = annotation
    
    label = {}
    points = []
    labels = []
    for locs in unique_locs:
        label = {}
        points = []
        labels = []
        start = [w.start() for w in re.finditer(locs, sent_cleaned)]
        #end = [w.start() + len(locs) - 1 for w in re.finditer(locs, sent_cleaned)]
        labels.append('LOCATION')
        label['label'] = labels
        #point_labels = {} #labels inside the point array: start, end and text
        for indexes in start:
            point_labels = {} #labels inside the point array: start, end and text
            point_labels['start'] = indexes
            point_labels['end'] = indexes + len(locs) - 1
            point_labels['text'] = locs
            points.append(point_labels)
            label['points'] = points
        
        annotation.append(label)
    
    data_dict['annotation'] = annotation
    return data_dict, count_articles_tagged_by_stanfordNER



def main():
    read_directory = 'D:/Surge docs/toi/'
    write_directory = 'D:/Surge docs/JSON-text/'
    entries = os.listdir(read_directory)
    count_articles_tagged_by_stanfordNER = 0
    
    for entry in entries:
        file = open(read_directory + entry, 'r')
        sent = file.read()
        data_dict, count_articles_tagged_by_stanfordNER = get_JSON(sent, count_articles_tagged_by_stanfordNER)
        
        print(count_articles_tagged_by_stanfordNER)
        #filename = entry.strip('.txt')
        os.chdir(write_directory)
        json_data = json.dumps(data_dict)
        #f = open(filename + '.json', 'w')
        f = open(entry, 'w')
        f.write(json_data)
        f.close()
        '''     
        # concat all the json or txt files to one so that it can be uploaded to dataturks as one file
        for files in file_list:
            file = open('D:\\Surge docs\\JSON-text\\' + files, 'r')
            content = file.read()
            full_data = full_data + ', ' + content
            
        # Save the concatenated file to a file
        f = open('D:/Surge docs/full_text.json', 'w')
        f.write(full_data)
        f.close()
            '''
            
if __name__ == "__main__":
    main()