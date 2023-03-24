# defend default settings 
MAX_LINK_DENSITY = 0.2
LENGTH_LOW = 70
LENGTH_HIGH = 200
STOPWORDS_LOW = 0.30
STOPWORDS_HIGH = 0.32

# get value from wiki page
from bs4 import BeautifulSoup
import requests
req = requests.get('https://vi.wikipedia.org/wiki/Trang_Ch%C3%ADnh')
soup = BeautifulSoup(req.text, 'html.parser')

# step 1: Preprocessing
extract_list=['header','head','style','script']
for a in soup.find_all(i for i in extract_list):
    a.extract()

# define necessary function to import html to json file
# write html to text.txt
with open('text.html', "w", encoding="utf-8") as f:
    f.write(str(soup))

# find all dom
soup = soup.find_all()
text = []

# function to remove all \n
def func(value):
    return ''.join(value.splitlines())

# function to find dom path
def find_dom_path(tag, path=''):
    if not tag.parent:
        return tag.name
    else:
        parent_path = find_dom_path(tag.parent, path)
        siblings = tag.parent.find_all(tag.name, recursive=False)
        index = 1
        for sibling in siblings:
            if sibling == tag:
                break
            index += 1
        return f'{parent_path}.{tag.name}'
    
# insert all hrml to a json
ok_tag = ['blockquote', 'caption', 'center', 'col', 'colgroup', 'dd', 'div', 'dl', 'dt', 'fieldset', 'form', 'legend', 'optgroup', 'option', 'p', 'pre', 'table', 'td', 'textarea', 'tfoot', 'th', 'thead', 'tr', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',]
header = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
for i in soup:
    if func(str(i.text)) != '':
        if(str(i.name) in ok_tag):
            if i.find_all('li') or i.find_all('p'):
                continue
            else:
                if str(i.name) in header:
                    text.append({'tag': str(find_dom_path(i)).replace("[document].",''), 'context': func(str(i.text).strip()), 'boilerplate':'', 'header': True})
                else:
                    text.append({'tag': str(find_dom_path(i)).replace("[document].",''), 'context': func(str(i.text).strip()), 'boilerplate':'', 'header': False})

# step 2: Context-free classification
# defind all necessary function to defind boilerplate for tag
def stopwords_count(text, stopwords):
    return sum(word.lower() in stopwords for word in text.split())

def stopwords_density(text, stopwords):
    words_count = len(text.split())
    if words_count == 0:
        return 0
    return stopwords_count(text, stopwords) / words_count

def links_density(text):
    chars_count_in_links=0
    text_length = len(text)
    if text_length == 0:
        return 0
    return chars_count_in_links / text_length

stoplist = ['blockquote', 'caption', 'center', 'col', 'colgroup', 'dd', 'div', 'dl', 'dt', 'fieldset', 'form', 'legend', 'optgroup', 'option', 'p', 'pre', 'table', 'td', 'textarea', 'tfoot', 'th', 'thead', 'tr', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',]

# Context-free classification
for content in text:
    link_density = links_density(content['context'])
    numeber_of_words = len(content['context'].split())
    
    words_count = len(content['context'].split())
    stopwords_density = words_count
    if words_count != 0:
        stopwords_density = sum(word.lower() in stoplist for word in content['context'].split()) / words_count
    
    length = len(content['context'])
    if(content['tag'] == 'select' or content['tag'] == '0xC2 0xA9'):
        content['boilerplate'] = 'bad'
    else :
        if link_density > MAX_LINK_DENSITY:
            content['boilerplate'] = 'bad'
        
        # short blocks
        elif length < LENGTH_LOW:
            if link_density > 0:
                content['boilerplate'] = 'bad'
            else:
                content['boilerplate'] = 'short'
        
        # medium and long blocks
        elif stopwords_density > STOPWORDS_HIGH:
            if length > LENGTH_HIGH:
                content['boilerplate'] = 'good'
            else:
                content['boilerplate'] = 'near-good'
        elif stopwords_density > STOPWORDS_LOW:
            content['boilerplate'] = 'near-good'
        else:
            content['boilerplate'] = 'bad'


# step 3: Context-sensitive classification
for i in range(len(text)-1):
    pre = text[i-1]['boilerplate']
    next = text[i+1]['boilerplate']
    if (pre == 'good' and next == 'good'):
        text[i]['boilerplate'] = 'good'
    elif (pre == 'bad' and next == 'bad'):
        text[i]['boilerplate'] = 'bad'
    elif (pre == 'bad' and next == 'near-good') or (next == 'bad' and pre == 'near-good') :
        text[i]['boilerplate'] = 'good'
    elif text[i]['boilerplate']  == 'short':
        text[i]['boilerplate'] = 'bad'
    else: text[i]['boilerplate'] = 'good'

# write all none boilerplate to text.json
text2 = []
for t in text:
    if t['boilerplate'] == 'good':
        text2.append(t)

import json
with open('text.json', 'w', encoding='utf-8') as f:
    json.dump(text2, f, ensure_ascii=False, indent=4)