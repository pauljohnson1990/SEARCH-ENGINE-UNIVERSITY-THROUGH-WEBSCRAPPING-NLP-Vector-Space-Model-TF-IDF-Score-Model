import time
import requests
from bs4 import BeautifulSoup
from urllib import robotparser
from urllib.parse import urlparse
import json
import os
import nltk
nltk.download("punkt")
nltk.download('stopwords')
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
ps = PorterStemmer()
sw = stopwords.words('english')


def text_preprocessing(doc):
    """Cleaning the text documents"""
    tokens = word_tokenize(doc)
    tmp=""
    for w in tokens:
        if w.isalpha():
            w=w.lower()
            if w not in sw:
                tmp+=ps.stem(w)+" "
    return tmp

def seek_publications(url,crawl_delay):
    """Seek pulications with atleast one CSM author"""
    if os.path.isfile('corpus.json'):
        with open('publications.json', 'r') as f:
            publications = json.load(f)
        with open('corpus.json', 'r') as c:
            corpus = json.load(c)
        with open('titles.json', 'r') as t:
            titles = json.load(t)
        with open('staff.json', 'r') as s:
            staff = json.load(s)

    else:
        publications = []
        corpus={}
        titles=[]
        staff={}
    next_index=len(publications)
    keep_going = True
    page_num = 1
    i = 1
    new_url = url
    documents = []
    text = requests.get(new_url).text
    soup = BeautifulSoup(text, "html.parser")
    link = soup.find_all("li")
    change= False
    while keep_going:
        for l in link:
            title = l.find_all("h3", class_="title")
            for t in title:
                if (t.string!= None) and (t.string not in titles):
                    change = True
                    titles.append(t.string)
                    publink = l.find("a", class_="link")
                    year = l.find("span", class_="date")
                    author = l.find_all("a", class_="link person")
                    author2 = l.find_all("span",
                                         class_=None)  # it contains name of title,authors(both inside and outside CSM ),journal
                    publication = {}

                    print("Fetching paper ", i, "......")
                    publication["Title"] = t.string
                    publication["Link"] = publink.get("href")  # Publication Link

                    # Abstract of papers
                    time.sleep(crawl_delay)
                    abs = requests.get(publication["Link"]).text
                    abs_soup = BeautifulSoup(abs, "html.parser")
                    text_block = abs_soup.find("div", class_="textblock")
                    content = ''
                    if text_block is not None:
                        for elem in text_block.descendants:
                            if elem.name == 'br':
                                content += '\n'
                            elif isinstance(elem, str):
                                content += elem.string
                    if content != '':
                        publication["Abstract"] = content

                    # Authors
                    publication["Author"] = []
                    CSM_AUTHOR = False
                    for a in author:
                        if a.string:
                            Author = {}
                            Author["Name"] = a.string
                            Author["Alink"] = a.get("href")  # Author Link
                            publication["Author"].append(Author)
                            time.sleep(crawl_delay)
                            aut_text = requests.get(Author["Alink"]).text
                            aut_soup = BeautifulSoup(aut_text, "html.parser").find('a', class_="link primary")
                            if aut_soup:
                                if aut_soup.string == 'Research Centre for Computational Science and Mathematical Modelling':
                                    CSM_AUTHOR = True # if the Author is a member of RCCSMM
                                    if a.string in staff:  # to count the no of staff crawled and max no of publication per staff
                                        staff[a.string] += 1
                                    else:
                                        staff[a.string] = 1

                    for a in range(1, len(author2)):
                        a2 = author2[a].string
                        if a2:
                            k = 0
                            j = 0
                            if a == len(author2) - 1:
                                j = 1
                            for d in publication["Author"]:
                                if d["Name"] == a2:
                                    k = 1
                            if k == 0 and j == 0:
                                Author = {}
                                Author["Name"] = author2[a].string
                                publication["Author"].append(Author)
                            elif j == 1 and k == 0:  # Journal
                                publication["Journal"] = author2[len(author2) - 1].string

                    # Publication Year
                    publication["Year"] = int(year.string[-4:])
                    if CSM_AUTHOR:
                        publications.append(publication)
                        print(publication)
                        # Document For building corpus for the searching.
                        doc = ''
                        doc += publication['Title'].lower() + ". "
                        for ap in publication["Author"]:
                            doc += ap.get("Name").lower() + " "
                        if publication.get('Abstract'):
                            doc += publication.get('Abstract').lower()
                        documents.append(text_preprocessing(doc))
                    else:
                         print("None of the authors is a member of Research Centre for Computational Science and Mathematical Modelling")
                    i += 1


        new_url = url + f"?page={page_num}"
        page_num += 1
        print("Seeking :", new_url)
        time.sleep(crawl_delay)
        text = requests.get(new_url).text
        soup = BeautifulSoup(text, "html.parser")
        link = soup.find_all("li")
        page_detail = soup.find("li", class_="search-pager-information")
        page_detail = page_detail.string
        page_detail = page_detail.replace("\n", "").replace("results", "").replace("out", "").replace("of", "").replace("-", "").split()
        if int(page_detail[-1]) < int(page_detail[-2]):
            keep_going = False
            print("Crawling finished")



    if change:
        # Building corpus from documents
        # corpus is the Inverted Index of words with indices
        # of documents and the termfrequency of the word in the document
        for i_d in range(len(documents)):
            for w in documents[i_d].split():
                if w in corpus:
                    if next_index+i_d in corpus[w]:
                        corpus[w][next_index+i_d] += 1
                    else:
                        corpus[w][next_index+i_d] = 1
                else:
                    corpus[w] = {next_index+i_d: 1}
        with open('publications.json', 'w') as f:
            json.dump(publications, f)
        with open('corpus.json', 'w') as c:
            json.dump(corpus, c)
        with open('titles.json', 'w') as t:
            json.dump(titles, t)
        with open('staff.json', 'w') as s:
            json.dump(staff, s)
        print("Crawling Summary")
        print("No of documents with atleast one CSM author : ", len(publications))
        print("No of Staff whose publications are crawled : ", len(staff))
        print("Maximum No of Publication per staff : ", max(staff.values()))
        print("corpus :\n", corpus)
    else:
        print("No Change")



while True:
    url='https://pureportal.coventry.ac.uk/en/organisations/research-centre-for-computational-science-and-mathematical-modell/publications/'
    root_website = urlparse(url).hostname
    rp = robotparser.RobotFileParser()
    rp.set_url('https://' + root_website + "/robots.txt") # get robots.txt file from root to find crawl_delay
    rp.read()
    crawl_delay = rp.crawl_delay("*")
    if crawl_delay is None:
        crawl_delay = 0
    seek_publications(url, crawl_delay)
    time.sleep(604800)# 7daysx24hoursx60minutesx60seconds = 604800 seconds