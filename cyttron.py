import csv
import nltk
from nltk import word_tokenize, pos_tag, WordPunctTokenizer
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
from nltk.corpus import stopwords, wordnet
import re
from SPARQLWrapper import SPARQLWrapper,JSON
from difflib import SequenceMatcher
from pprint import pprint
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
from gensim import corpora, models, similarities

# sparql-lists
label = []
desc = []
bigList= []
contextIn= []
contextOut= []
foundLabel= []
foundDesc= []
URI= []

iup = 0
pathList = []

#teststring
string = "Since AD is associated with a decrease in memory function and the hippocampus might play a role in memory function, researchers focussed on the degeneration of the hippocampus. Bilateral hippocamal atrophy is found in the brains of Alzheimer patients9. Reduction of the hippocampus for diagnosing is measured in two different ways. By using volumetry of the hippocampus itself or by using volumetry of the AHC (amygdale hippocampal complex). Volumetric studies of the hippocampus showed a reduction of 25 -39% 10,11,12. When measuring relative size in relation to the total cranial volume even a bigger reduction is found of 45%10. Yearly measurements of hippocampal volumes in Alzheimer patients showed a 3.98 /-1.92% decrease per year (p < 0.001)6. Patients with severe AD disease show higher atrophy rates compared to early or mild AD10,11. Correlations are found between hippocampal atrophy and severity of dementia, age 11and sex. Because a correlation is found between age and hippocampal atrophy, volumetric changes should be correct for age and sex. For clinical diagnoses it still remains uncertain whether volumetric measurements of the hippocampus alone is the most accurate way, some studies imply so 12. For diagnosing AD by hippocampal volume measurements the sensitivity varies between 77% and 95% and a specificity of 71-92% 9, 11-14. The sensitivity and specificity varies due the variance of patients and controls used. Patients varies in severity of disease and controls in these studies included FTP, MCI or non-alzheimer elderly. Other studies found that diagnosis based on volumetric changes are comparable for the hippocampus and ERC, but due the more easier use and less variability of hippocampal volumetry, the hippocampus is more feasible for diagnosis 13, 15.  Other studies found that combinations of different volumetric measurements with parahippocampal cortex, ERC14or amygdale (see AHC)  are indeed needed for a more accurate diagnosis of AD patients. AD has some similar atrophic regions compared to Mild Cognitive Impairment (MCI), therefore volumetry of the ERC in combination with hippocampal volumetry can give a more accurate diagnosis of AD 14. Total intracranial volume (TIV) and temporal horn indices (THI:  ratio of THV to lateral ventricular volume) can be used as surrogate marker for volume loss of hippocampal formation. A negative correlation is found between THI and THV and the declarative reminding test 16. Some studies indicate that the accuracy of AD diagnosis increases by volumetry of amygdala-hippocampal complex (AHC) compared to only volumetric measurements of the hippocampus 10"
repo="cyttron"
endpoint="http://dvdgrs-900:8080/openrdf-sesame/repositories/" + repo

sparql = SPARQLWrapper(endpoint)

wikiTxt=""

f = open('log\wordMatch.csv','w')
f.write('"string";"# total labels";"total labels";"# unique labels";"unique labels"'+ "\n")
f.close()

fd = open('log\descMatch.csv','w')
fd.close()

csvread = csv.reader(open('db\cyttron-db.csv', 'rb'), delimiter=';')
pub=[]
group=[]
priv=[]

#======================================================#
# Fill a list of Label:URI values (Cyttron_DB)         #
#======================================================#
def getLabels():
    global label,sparql,endpoint
    print endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.addCustomParameter("infer","false")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>

        SELECT ?URI ?label
        WHERE {
            ?URI rdfs:label ?label .
            ?URI a owl:Class .
        }
    """)
    
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        label.append([x["label"]["value"],x["URI"]["value"]])

    print "Filled list: label. With:",str(len(label)),"entries"
    
#======================================================#
# Fill a list of Desc:URI values (Cyttron_DB)          #
#======================================================#
def getDescs():
    global desc,sparql,endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.addCustomParameter("infer","false")
    sparql.setReturnFormat(JSON)
    # GO + DOID + MPATH
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>

        SELECT ?URI ?desc
        WHERE {
            ?URI a owl:Class .
            ?URI oboInOwl:hasDefinition ?bnode .
            ?bnode rdfs:label ?desc .
        }
    """)
    
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        desc.append([x["desc"]["value"],x["URI"]["value"]])

    print "filled lists: desc. With:",str(len(desc)),"entries"

#======================================================#
# Scan a string for occurring ontology-words           #
#======================================================#
def wordMatch(string):
    # wordMatch with regexp word boundary
    global label,foundLabel,f
    foundLabel=[]
    foundTotal=[]
    foundUnique=[]
    f = open('log\wordMatch.csv','a')
    f.write('"' + str(string) + '";"')
    f.close()
    for i in range(len(label)):
        currentLabel = str(label[i][0]).lower()
        currentURI = str(label[i][1]).lower()
        string = string.lower()
        c = re.findall(r"\b"+re.escape(currentLabel)+r"\b",string)
        countLabel = len(c)
        if countLabel > 0:
            foundLabel.append([countLabel,currentURI,currentLabel])
            foundUnique.append(currentLabel)
            for i in range(countLabel):
                foundTotal.append(currentLabel)
    foundLabel.sort(reverse=True)
    print foundLabel
    f = open('log\wordMatch.csv','a')
    if len(foundTotal) > 0:
        if len(foundTotal) > 1:
            f.write(str(len(foundTotal)) + '";"' + ', '.join(foundTotal[:-1]) + ', ' + foundTotal[-1] + '";"')
        if len(foundTotal) == 1:
            f.write('1";"' + (foundTotal[0]) + '";"')        
    else:
        f.write('0";"";"')
    if len(foundUnique) > 0:
        if len(foundUnique) > 1:
            f.write(str(len(foundUnique)) + '";"' + ', '.join(foundUnique[:-1]) + ', ' + foundUnique[-1] + '"' + "\n")
        if len(foundUnique) == 1:
            f.write('1";"' + (foundUnique[0]) + '"' + "\n")        
    else:
        f.write('0";""' + "\n")
    f.close()
    print foundUnique
    print foundTotal
    print "Found",len(foundUnique),"unique labels"
    print "and",len(foundTotal),"total labels"
        
#======================================================#
# Scan a string, generate syns for each word           #
# wordMatch syn-string                                 #
#======================================================#
def wordNetWordMatch(string):
    newString = ""
    string = nltk.word_tokenize(string)
    for i in range(len(string)):
        currentWord = string[i].lower()
        synonyms = []
        for syn in wordnet.synsets(currentWord):
            for lemma in syn.lemmas:
                synonyms.append(str(lemma.name).replace('_',' ').lower())
        synonyms = set(synonyms)
        word = ', '.join(synonyms)
        # print currentWord+str(":"),word
        newString += word
    wordMatch(newString)

#======================================================#
# Use Gensim to calculate similarity                   #
#======================================================#
def descMatch(string,int):
    "Returns the x most similar descriptions"
    temp=[]
    global foundDesc,fd,desc
    fd = open('log\descMatch.csv','a')
    fd.write('"' + string)
    foundDesc=[]
    cleanDesc=[]
    stopset = set(stopwords.words('english'))

    ### Corpus stuff: create a TF-IDF metric using cleaned descriptions as training corpus
    # 1. tokenize + clean each desc entry, store in new list
    for i in range(len(desc)):
        words = WordPunctTokenizer().tokenize(desc[i][0])
        wordsCleaned = [word.lower() for word in words if word.lower() not in stopset and len(word) > 2]
        cleanDesc.append(wordsCleaned)
    # Create a dictionary (word:occurrence) out of the cleaned list
    dictionary = corpora.Dictionary(cleanDesc)
    # Create a bag-of-words model out of the entries in cleanDesc
    vecDesc = [dictionary.doc2bow(x) for x in cleanDesc]
    # Create a TF-IDF measure out of the BOW
    tfidf = models.TfidfModel(vecDesc,id2word=dictionary)
    corpus_tfidf = tfidf[vecDesc]

    ### String stuff: tokenize, clean and convert to BOW format before comparing
    tokenString = WordPunctTokenizer().tokenize(string)
    cleanString = [token.lower() for token in tokenString if token.lower() not in stopset and len(token) > 2]
    vecString = dictionary.doc2bow(cleanString)

    ### Compare!
    index = similarities.MatrixSimilarity(corpus_tfidf)
    sims = index[vecString]
    sims = sorted(enumerate(sims), key=lambda item: -item[1])
    sims = sims[:int]
    print len(sims)
    for i in range(len(sims)):
        ID = sims[i][0]
        sim = sims[i][1]
        descString = desc[ID]
        foundDesc.append([descString,sim])
    
#======================================================#
# Generate syns from string, gensim similarity         #
#======================================================#    
def descWordNetMatch(string,int):
    newString = ""
    string = nltk.word_tokenize(string)
    for i in range(len(string)):
        currentWord = string[i].lower()
        synonyms = []
        for syn in wordnet.synsets(currentWord):
            for lemma in syn.lemmas:
                synonyms.append(str(lemma.name).replace('_',' ').lower())
        synonyms = set(synonyms)
        word = ', '.join(synonyms)
        newString += word
    descMatch(newString,int)
    
#======================================================#
# CyttronDB-specific functions to process lists        #
#======================================================#        
def listWordMatch(list):
    for i in range(len(list)):
        string = list[i]
        print str(i+1),"of",str(len(list))
        wordMatch(string)
        print ""

def listWordNetMatch(list):
    for i in range(len(list)):
        string = list[i]
        print str(i+1),"of",str(len(list))
        wordNetWordMatch(string)
        print ""

def listDescMatch(list,int):
    for i in range(len(list)):
        string = list[i]
        print str(i+1),"of",str(len(list))
        descMatch(string,int)
        print ""

def listWordNetDescMatch(list,int):
    for i in range(len(list)):
        string = list[i]
        print str(i+1),"of",str(len(list))
        descWordNetMatch(string,int)
        print ""

#======================================================#
# Retrieve Wiki page raw text                          #
#======================================================# 
def wikiGet(title):
    global wikiTxt
    article = urllib.quote(title)

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')] #wikipedia needs this

    resource = opener.open("http://en.wikipedia.org/wiki/" + article)
    data = resource.read()
    resource.close()
    soup = BeautifulSoup(data)
    text = str(soup.findAll('p'))
    wikiTxt = nltk.clean_html(text)
    print title,'in wikiTxt'

#======================================================#
# Stuff                                                #
#======================================================# 
def switchEndpoint():
    global endpoint,repo
    if repo == "cyttron":
        repo = "dbp"
        endpoint="http://dvdgrs-900:8080/openrdf-sesame/repositories/" + repo
        print "Switched SPARQL endpoint to DBPedia:",endpoint
        exit
    else:
        repo = "Cyttron_DB"
        endpoint="http://dvdgrs-900:8080/openrdf-sesame/repositories/" + repo
        print "Switched SPARQL endpoint to Cyttron DB:",endpoint
        exit
		
def cleanCSV(csvread):
    global pub,group,priv
    for line in csvread:
        if len(line[0]) > 0:
            pub.append(line[0])
        if len(line[1]) > 0:
            group.append(line[1])
        if len(line[2]) > 0:
            priv.append(line[2])
    total1 = len(pub)
    total2 = len(group)
    total3 = len(priv)
    pub = list(set(pub))
    group = list(set(group))
    priv = list(set(priv))
    print "Public entries:",total1,"total",len(pub),"unique"
    print "Group entries:",total2,"total",len(group),"unique"
    print "Priv entries:",total3,"total",len(priv),"unique"

def main():
    cleanCSV(csvread)

if __name__ == '__main__':
    main()
