from SPARQLWrapper import SPARQLWrapper,JSON
from pygraph.classes.digraph import digraph
from pygraph.readwrite.dot import write
import sqlite3
from gensim import corpora, models, similarities
from nltk.corpus import stopwords, wordnet
from nltk import word_tokenize, pos_tag, WordPunctTokenizer

conn = sqlite3.connect('db/sem_web.db')

GR = digraph()
context = []
queue = []
visited = []
path = []
iup = 0
endpoint = 'http://dbpedia.org/sparql'
done = False

log = open('sem_weblog.txt','w')

class MyQUEUE:	
    def __init__(self):
        self.holder = []
    def enqueue(self,val):
        self.holder.append(val)
    def dequeue(self):
        val = None
        try:
            val = self.holder[0]
            if len(self.holder) == 1:
                self.holder = []
            else:
                self.holder = self.holder[1:]	
        except:
            pass	
        return val		
    def IsEmpty(self):
        result = False
        if len(self.holder) == 0:
            result = True
        return result

def SemSim(URI1,URI2):
    q = MyQUEUE()
    BFS(URI1,URI2,q)

def BFS(URI1,URI2,q):
    global queue,visited,done,DG,log    

    # Sort list so node1-node2 == node2-node1
    lijstje=[URI1,URI2]
    URI1 = sorted(lijstje)[0]
    URI2 = sorted(lijstje)[1]

    log = open('pathfinderlog.txt','a')                            
    log.write('"node1";"' + str(URI1) + '"\n')
    log.write('"node2";"' + str(URI2) + '"\n')
    log.close()

    # Check if initial URI-path is already in db
    c = conn.cursor()
    c.execute('SELECT * FROM sem_web WHERE node1=? AND node2=?',(URI1,URI2))
    if len(c.fetchall()) > 0:
        print "Initial URI Path already exists!"
        c.execute('SELECT * FROM sem_web WHERE node1=? AND node2=?',(URI1,URI2))
        result = c.fetchall()
        c.close()
        URI1 = result[0][0]
        URI2 = result[0][1]
        pathlength = result[0][2]
        print "URI1:",URI1
        print "URI2:",URI2
        print "pathlength:",pathlength
        log = open('pathfinderlog.txt','a')
        log.write('"pathlength";"' + str(pathlength) + '"\n')
        log.close()

        done = True
        return 'finished'
    
    else:
        print "Initial URI Path is unknown to me..."
        done = False
        queue=[]
        visited=[]
        q.enqueue([URI1])
        while q.IsEmpty() == False:
            curr_path = q.dequeue()
            queue.append(curr_path)
            for i in range(len(curr_path)):
                if len(curr_path) > 1:
                    
                    node1 = curr_path[i][0]
                    node2 = curr_path[i][2]
                    edgeLabel = curr_path[i][1]
                    if GR.has_node(node1) is False:
                        GR.add_node(node1)
                    if GR.has_node(node2) is False:
                        GR.add_node(node2)
                    if GR.has_edge((node1,node2)) is False:
                        GR.add_edge((node1,node2),label=str(edgeLabel))

                    c = conn.cursor()
                    c.execute('SELECT * FROM sem_web WHERE node1=? AND node2=?',(node1,node2))
                    if len(c.fetchall()) > 0:
                        print "Path already exists!"
                    else:
                        print "Inserting path!"
                        c.execute('insert into sem_web values (?,?,1,"-")',(node1,node2))
                        conn.commit()
                    c.close()

                    if node1 == URI2:
                        done = True
                        showPath(queue,URI1,URI2)
                        if done == True:
                            string = "Found a link! Stored in path. Length:",len(path),"| Visited:",len(visited),"nodes."
                            log = open('pathfinderlog.txt','a')                            
                            log.write('"pathlength";"' + str(len(path)) + '"\n')
                            log.close()
                            print string                            
                            print 'Wrote path to log-file'
                            
                            c = conn.cursor()
                            c.execute('SELECT * FROM sem_web WHERE node1=? AND node2=?',(URI1,URI2))
                            if len(c.fetchall()) > 0:
                                print "BEST VER Path already exists!"
                            else:
                                print "BEST VER Inserting path!"
                                c.execute('insert into sem_web values (?,?,?,"-")',(URI1,URI2,len(path)))
                                conn.commit()
                            c.close()
                            findFlips(path,URI1,URI2)
                            return len(path)
                        
                    if node2 == URI2:
                        print "\nFound a link!"
                        done = True
                        showPath(queue,URI1,URI2)
                        if done == True:
                            string = "Found a link! Stored in path. Length:",len(path),"| Visited:",len(visited),"nodes."
                            print string
                            log = open('pathfinderlog.txt','a')                            
                            log.write('"pathlength";"' + str(len(path)) + '"\n')
                            log.close()
                            print 'Wrote path to log-file'

                            c = conn.cursor()
                            c.execute('SELECT * FROM sem_web WHERE node1=? AND node2=?',(URI1,URI2))
                            if len(c.fetchall()) > 0:
                                print "BEST VER Path already exists!"
                            else:
                                print "BEST VER Inserting path!"
                                c.execute('insert into sem_web values (?,?,?,"-")',(URI1,URI2,len(path)))
                                conn.commit()
                            c.close()
                            findFlips(path,URI1,URI2)                            
                            return len(path)
                        
                    if node1 not in visited and 'http://www.w3.org/2002/07/owl#Class' not in node1 and 'http://www.geneontology.org/formats/oboInOwl#ObsoleteClass' not in node1:
                        node = node1
                        visited.append(node)
                        getNodes(node,URI2)
                        q.enqueue(context)
                    else:
                        if 'http://www.w3.org/2002/07/owl#Class' not in node2 and 'http://www.geneontology.org/formats/oboInOwl#ObsoleteClass' not in node2 and node2 not in visited:
                            node = node2
                            visited.append(node)
                            getNodes(node,URI2)
                            q.enqueue(context)
                        else:
                            i+=1
                else:
                    node = curr_path[0]
                    visited.append(node)
                    getNodes(node,URI2)
                    q.enqueue(context)

def createGraph(list_of_nodes):
    global path,dicto,pathList,GR
    for i in range(1,len(list_of_nodes)):
        currentURI = list_of_nodes[i]
        otherURI = list_of_nodes[i-1]
        SemSim(otherURI,currentURI)

        # plot BFS result
        for i in range(len(path)):
            nodeLeft = path[i][0]
            edgeLabel = path[i][1]
            nodeRight = path[i][2]
            if GR.has_node(nodeLeft) is False:
                GR.add_node(nodeLeft)
            if GR.has_node(nodeRight) is False:
                GR.add_node(nodeRight)
            if GR.has_edge((nodeLeft,nodeRight)) is False:
                GR.add_edge((nodeLeft,nodeRight),label=str(edgeLabel))

        # plot parent1
        findParents([[currentURI]])
        log = open('pathfinderlog.txt','a')                            
        log.write('"node1 depth: ' + str(pathList[0][0]) + '";"' + str(len(pathList)) + '"\n')
        log.close()
        if GR.has_node(pathList[0][0]) is False:
            GR.add_node(pathList[0][0])
        for i in range(1,len(pathList)):
            prevNode = pathList[i-1][0]
            node = pathList[i][0]
            if GR.has_node(node) is False:
                GR.add_node(node)
            if GR.has_edge((prevNode,node)) is False:
                GR.add_edge((prevNode,node),label='rdfs:subClassOf')

        # plot parent2
        findParents([[otherURI]])
        log = open('pathfinderlog.txt','a')                            
        log.write('"node2 depth: ' + str(pathList[0][0]) + '";"' + str(len(pathList)) + '"\n')
        log.close()        
        if GR.has_node(pathList[0][0]) is False:
            GR.add_node(pathList[0][0])
        for i in range(1,len(pathList)):
            prevNode = pathList[i-1][0]
            node = pathList[i][0]
            if GR.has_node(node) is False:
                GR.add_node(node)
            if GR.has_edge((prevNode,node)) is False:
                GR.add_edge((prevNode,node),label='rdfs:subClassOf')

    # write graph to DOT-file
    dot = write(GR)
    dotLabel = relabel(dot)
    f = open('graph.gv','w')
    f.write(dotLabel)
    findLCS(list_of_nodes[0],list_of_nodes[1])

def relabel(text):
    # from URI to label
    global dicto
    for i, j in dicto.iteritems():
        text = text.replace(i, j)
    return text

def showPath(list,start,target):
    global path
    path = []
    for x in range(len(list),0,-1):
        if x-1 > 1:
            hop = list[x-1]
            for i in range(len(hop)):
                leftNode = hop[i][0]
                rightNode = hop[i][2]
                if leftNode == target:
                    path.append(hop[i])
                    target = rightNode
                    break
                if rightNode == target:
                    path.append(hop[i])
                    target = leftNode
                    break
        if x-1 == 1:
            hop = list[x-1]
            for i in range(len(hop)):
                leftNode = hop[i][0]
                rightNode = hop[i][2]
                if leftNode == start and rightNode == target:
                    path.append(hop[i])
                    return path                    
                if rightNode == start and leftNode == target:
                    path.append(hop[i])
                    return path

def findFlips(path,start,target):
    flips = ""
    count=0
    for i in range(0,len(path)):
        prevLeft = path[i-1][0]
        prevRight = path[i-1][2]
        
        left = path[i][0]
        right = path[i][2]
        print left,right

        if left == prevRight:
            flips += "U"
        if right == prevRight:
            flips += "D"
        if right == prevLeft:
            flips += "D"
    print flips
    for i in range(1,len(flips)):
        prevLetter = flips[i-1]
        letter = flips[i]
        if letter == prevLetter:
            count += 0
        else:
            count += 1
    log = open('pathfinderlog.txt','a')                            
    log.write('"directionflips:";"' + str(count) + '"\n')
    log.close()
    return count

def getNodes(URI,URI2):
    global context
    context=[]
    sparql = SPARQLWrapper(endpoint)
    
    # Direct neighbours
    querystring="PREFIX obo: <http://purl.org/obo/owl> SELECT DISTINCT ?p ?s WHERE { <" + str(URI) + "> ?p ?s . FILTER (isURI(?s )) . }"
    print URI
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([URI,x["p"]["value"],x["s"]["value"]])
    querystring="SELECT DISTINCT ?o ?p WHERE { ?o ?p <" + str(URI) + "> . FILTER (isURI(?o )) . }"
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([x["o"]["value"],x["p"]["value"],URI])

    # BNode neighbours
    querystring="SELECT DISTINCT ?s2 ?p WHERE { <" + str(URI) + "> ?p ?s . ?s ?x ?s2 . FILTER (isBlank(?s )) . FILTER (isURI(?s2)) .}"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([URI,x["p"]["value"],x["s2"]["value"]])
    querystring="SELECT DISTINCT ?s2 ?p WHERE { ?o ?p <" + str(URI) + "> . ?o ?x ?s2 . FILTER (isBlank(?o )) . FILTER (isURI(?s2)) .}"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([x["s2"]["value"],x["p"]["value"],URI])
    return context    

#======================================================#
# 'shared parents' stuff                               #
#======================================================#

def findLCS(URI1,URI2):
    LCS = [[findCommonParents(URI1,URI2)]]
    findParents(LCS)
    log = open('pathfinderlog.txt','a')                            
    log.write('"LCS depth: ' + str(pathList[0][0]) + '";"' + str(len(pathList)) + '"\n')
    log.close()
    
def findParents(URI):
    global iup, pathList,endpoint
    list_out=[]
    iup += 1
    print "[findParents]\t","Hop",iup,"found",len(URI[iup-1]),"nodes"
    for i in range(len(URI[iup-1])):
        sparql = SPARQLWrapper(endpoint)
        sparql.addCustomParameter("infer","false")
        querystring = 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?super WHERE { <' + URI[iup-1][i] + '> rdfs:subClassOf ?super . FILTER isURI(?super) }'
        sparql.setReturnFormat(JSON)
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            list_out.append(x["super"]["value"])
    if len(list_out) > 0:
        URI.append(list_out)
        findParents(URI)
    else:
        print "[findParents]\t","Reached the top!"
        print "[findParents]\t",URI[0][0]
        print "[findParents]\t","Hop | Path:"
        print "[findParents]\t","Depth:",len(URI)
        for i in range(len(URI)):
            print "[findParents]\t",i,"  |",URI[i]
        iup=0
        pathList = URI
        return pathList

def findCommonParents(URI1,URI2):
    global done
    done = False
    # Input URI strings, output common Parent
    print ""
    URI1 = [[URI1]]
    URI2 = [[URI2]]
    iup = 0
    global result1,result2,pathList,parent1,parent2

    # First pathList generation
    findParents(URI1)
    print "[findCommonP]\t","1st URI processed\n"
    result1 = pathList
    
    # Flush results for 2nd
    pathList = []

    # Second pathList generation
    findParents(URI2)
    print "[findCommonP]\t","2nd URI processed\n"
    result2 = pathList

    for i in range(len(result1)):
        for j in range(len(result2)):
            for i2 in range(len(result1[i])):
                for j2 in range(len(result2[j])):
                    if set(result1[i][i2]) == set(result2[j][j2]):
                        print "[findCommonP]\t","CommonParent found!"
                        done = True
                        print "[findCommonP]\t","Result1[" + str(i) + "][" + str(i2) +"]",
                        print "matches with result2[" +str(j) + "][" + str(j2) + "]"
                        print "[findCommonP]\t",result1[i][i2]
                        parent1 = result1
                        parent2 = result2
                        if done == True:
                            return result1[i][i2]
    return parent1,parent2

def findMultiParent(URIlist):
    global bigList
    n = len(URIlist)
    for i in range(n):
        for j in range(i+1,n):
            print str(URIlist[i]),"-",str(URIlist[j])
            findCommonParents(URIlist[i],URIlist[j])
            bigList.append([parent1,parent2])


#======================================================#
# Textual comparison                                   #
#======================================================#
def getContext(node1):
    context1=[]
    neighboursOut=[]
    neighboursIn=[]
    sparql = SPARQLWrapper(endpoint)
    print endpoint

    # Get own out literals
    querystring="SELECT DISTINCT ?s WHERE { <" + str(node1) + "> ?p ?s . FILTER (isLiteral(?s ))  }"
    print querystring
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'http://www.w3.org/2002/07/owl#Class' not in x["s"]["value"]:
            context1.append(x["s"]["value"])
            print "Own OUT literals:",x["s"]["value"]

    # Get own out bnode-literals
    querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?desc WHERE { <" + str(node1) + "> ?p ?s . ?s ?x ?desc . FILTER (isBlank(?s )) . FILTER (isLiteral(?desc)) }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'http://www.w3.org/2002/07/owl#Class' not in x["desc"]["value"]:
            context1.append(x["desc"]["value"])
            print "Own OUT bnode-literals:",x["desc"]["value"]

    # Get own in literals
    querystring="SELECT DISTINCT ?o WHERE { ?o ?p <" + str(node1) + "> . FILTER (isLiteral(?o )) }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context1.append(x["o"]["value"])
        print "Own IN literals",x["o"]["value"]

    # Get own in bnode-literals
    querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?desc WHERE { ?o ?p <" + str(node1) + "> . ?o ?x ?desc . FILTER (isBlank(?o )) . FILTER (isLiteral(?desc)) }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context1.append(x["desc"]["value"])
        print "Own IN literals:",x["desc"]["value"]
    direct = context1
    print "Final direct:",direct
    context1=[]

    # Get all out neighbour URI's
    querystring="SELECT DISTINCT ?s WHERE { <" + str(node1) + "> ?p ?s . FILTER (isURI(?s ))  }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'http://www.w3.org/2002/07/owl#Class' not in x["s"]["value"]:
            neighboursOut.append(x["s"]["value"])
    print "Neighbour OUT nodes:",neighboursOut

    # Get all in neighbour URI's
    querystring="SELECT DISTINCT ?o WHERE { ?o ?p <" + str(node1) + "> . FILTER (isURI(?o )) }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'http://www.w3.org/2002/07/owl#Class' not in x["o"]["value"]:
            neighboursIn.append(x["o"]["value"])
    print "Neighbours IN:",neighboursIn

    # Get literal + bnode-literals for OUT neighbours
    for i in range(len(neighboursOut)):
        # Get all neighbour literals
        querystring="SELECT DISTINCT ?s WHERE { <" + str(neighboursOut[i]) + "> ?p ?s . FILTER (isLiteral(?s ))  }"
        sparql.setReturnFormat(JSON)
        sparql.addCustomParameter("infer","false")
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context1.append(x["s"]["value"])

        # Get all neighbour bnode-literals
        querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?desc WHERE { <" + str(neighboursOut[i]) + "> ?p ?s . ?s ?x ?desc . FILTER (isBlank(?s )) . FILTER (isLiteral(?desc)) }"
        sparql.setReturnFormat(JSON)
        sparql.addCustomParameter("infer","false")
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context1.append(x["desc"]["value"])

    # Get literal + bnode-literals for IN neighbours
    for i in range(len(neighboursIn)):
        querystring="SELECT DISTINCT ?o WHERE { ?o ?p <" + str(neighboursIn[i]) + "> . FILTER (isLiteral(?o )) }"
        sparql.setReturnFormat(JSON)
        sparql.addCustomParameter("infer","false")
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context1.append(x["o"]["value"])

        querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?desc WHERE { ?o ?p <" + str(neighboursIn[i]) + "> . ?o ?x ?desc . FILTER (isBlank(?o )) . FILTER (isLiteral(?desc)) }"
        sparql.setReturnFormat(JSON)
        sparql.addCustomParameter("infer","false")
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context1.append(x["desc"]["value"])
    neighbours = context1
    print "Direct:",direct
    print "Neighbours:",neighbours
    final = [direct,neighbours]
    print "\nFinal:",final