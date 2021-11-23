
import pathlib, traceback, configparser
import networkx as nx

#Globals
path = str( pathlib.Path(__file__).parent.absolute() )
query = ""
config = None
argumentIsFact = False
argumentHolds  = False
DG = nx.DiGraph()


def processResult(q,result):
    """
    Processes the results from SWI-Prolog and returns the Directed Graph, if the argument holds and if it's a fact.

    Args:
        q (str): The query
        result (str): The result of the query Swi-Prolog returned

    Returns:
        nx.Digraph: The Directed Graph of the result
        bool: If the argument holds
        bool: If the argument is a fact
    """
    loadConfig()
    printRawResult = config.getboolean('printRawResult')
    printCompactResult = config.getboolean('printCompactResult')
    exportRaw = config.getboolean('ExportRAW')
    export = config.getboolean('Export')
    
    global query
    query = q
    
    result = result.strip()
    if(printRawResult): print(result+'\n')

    # Export the RAW result in a text file
    if (exportRaw):
        with open(path+"/outputRAW.txt","w+") as f:
            f.write(result)
            f.close

    #Format results to remove excess spaces and convert it to a list for calculations
    resultListFormatted = resultFormatter(result)
    
    #Convert formatted result back to string for printing and saving to file
    resultStringFormatted = '\n'.join(resultListFormatted)
    if(printCompactResult): print(resultStringFormatted+'\n')

    # Export the formated result in a text file
    if (export):
        with open(path+"/output.txt","w+") as f:
            f.write(resultStringFormatted)
            f.close
    
    #Build Graph and return
    if (translator(resultListFormatted)):
        return DG, argumentHolds, argumentIsFact
    

def resultFormatter(result):
    """
    Converts a multiline string to a list of lines while removing space only lines

    Args:
        result (str): The multiline string to process

    Returns:
        list: The list of all the lines
    """   
     
    list2 = result.splitlines()
    list3 = []
    for item in list2:
        if not item.isspace():
            if (item.find("RESULT:") != -1): #sometimes the RESULT: line has unwanted spaces on its left
                list3.append(item.lstrip())
            else:
                list3.append(item)
    return list3


def translator(textList):
    """
    Translates the text result of the SWI-Prolog query to a networkx DiGraph

    Args:
        textList (list): A list of strings

    Returns:
        bool: Translation successful
    """  
    namedNodes = config.getboolean('namedNodes')
    # -------------------------- 0 Find how many results ------------------------- #
    results = 0
    startLine = 0
    for line in range(len(textList)) :
        if (textList[line].find("RESULT") != -1): 
            startLine = line
            results = results + 1
    
    #Set line for section 3
    if (results > 1):
        print ("--------Multiple results. Taking Last--------\n")
        line = startLine + 2
    else:
        print ("---------------------------------------------\n")
        line = 2  #line 3-1=2
    
      
    # --------------------------------- 1 Result --------------------------------- #
    global argumentHolds
    if textList[startLine].endswith('holds.'):
        argumentHolds = True
    else:
        argumentHolds = False
    
    # ---------------------------------- 2 Root ---------------------------------- #
    global DG
    DG = nx.DiGraph() #To Clear data. clear() is not working correctly

    #Check if its a fact
    global argumentIsFact
    if (textList[startLine+1].rstrip().endswith("by")):
        argumentIsFact = True
        #Add root and return
        DG.add_nodes_from([(query,{"description":textList[startLine+1].lstrip().rstrip()})])
        return True
    else:
        argumentIsFact = False
    
    #Check if holds and directly supported by fact
    if (argumentHolds and len(textList[startLine:]) == 3 ):
        argumentIsFact = False
        DG.add_nodes_from([(query, {"description":textList[startLine+1].split('|',1)[-1].lstrip().rstrip()+"\n" 
                                   + textList[startLine+2].split('|',1)[-1].lstrip().rstrip()})])
        return True

    
    
    #Add root
    root = textList[startLine + 1].split(':',1)[0].split('(',1)[0].lstrip()
    DG.add_nodes_from([(query if namedNodes else root,{"description":textList[startLine + 1].lstrip().rstrip()})])
    
    
    
    # ---------------------------------- 3 Nodes --------------------------------- #
    
    nodeList = [query if namedNodes else root]
    nodeDepth = 0
    indexDict = {0:0} # At depth 0 index "|" is at 0

    try:
        listlength = len(textList)
        while (line <  listlength):
            nextIndex = textList[line].find("|")
            if (nextIndex == -1): break
            

            #Next Node is Left (No other child node)
            #go back until you find the previous node
            if (nextIndex < indexDict[nodeDepth]):
                while ( textList[line][indexDict[nodeDepth]]  != "|" ):
                    nodeDepth -= 1
                    nodeList.pop()



            #Next Node is Right (attacking, child node)
            if (nextIndex > indexDict[nodeDepth]):
                #increase depth
                nodeDepth += 1
                indexDict[nodeDepth]=nextIndex

                #add new depth node
                if (namedNodes):
                    nodeTitle = ("not "+textList[line].split(" ")[-1][:-1] if textList[line].split(" ")[-2]=="not" 
                                 else textList[line].split(" ")[-1][:-1])
                else:
                    nodeTitle = textList[line].split(':',1)[0].split('(',1)[0].lstrip()[1:]
                nodeList.append(nodeTitle)
                
                #Create Description
                nodeDescription = ""
                i = 0
                while (True):
                    #Break when 1) end of list 2) more than 3 lines of description 
                    # 3) no "|" in the string so not a description line
                    if (line+i >= listlength or i == 3 or (not textList[line].find("|") == nextIndex)): break 
                    nodeDescription = nodeDescription + textList[line+i].split('|',1)[-1].lstrip().rstrip()+"\n"
                    i = i + 1
                nodeDescription = nodeDescription[0:-1] # remove last /n
                
                #Add to graph
                if (nodeList[nodeDepth] not in DG.nodes): 
                    DG.add_nodes_from([ ( nodeList[nodeDepth], {"description":nodeDescription} ) ])
                DG.add_edge(nodeList[nodeDepth], nodeList[nodeDepth-1])

            #Next Node is at the same Position/Depth (both have the same parent, sibling node)
            elif (nextIndex == indexDict[nodeDepth]):
                #nodeDepth doesn't change

                #replace the last node
                if (namedNodes):
                    nodeTitle = ("not "+textList[line].split(" ")[-1][:-1] if textList[line].split(" ")[-2]=="not" 
                                 else textList[line].split(" ")[-1][:-1])
                else:
                    nodeTitle = textList[line].split(':',1)[0].split('(',1)[0].lstrip()[1:]
                nodeList[nodeDepth] = nodeTitle
                
                #Create Description
                nodeDescription = ""
                i = 0
                while (True):
                    #Break when 1) end of list 2) more than 3 lines of description 
                    # 3) no "|" in the string so not a description line
                    if (line+i >= listlength or i == 3 or (not textList[line].find("|") == nextIndex)): break 
                    nodeDescription = nodeDescription + textList[line+i].split('|',1)[-1].lstrip().rstrip()+"\n"
                    i = i + 1
                nodeDescription = nodeDescription[0:-1] # remove last /n
                
                #Add to graph 
                if (nodeList[nodeDepth] not in DG.nodes): 
                    DG.add_nodes_from([ ( nodeList[nodeDepth], {"description":nodeDescription} ) ])
                DG.add_edge(nodeList[nodeDepth], nodeList[nodeDepth-1])

            line += 3   
    
        return True
    except Exception:
        traceback.print_exc()
        return False


def info(DG):
    """
    Prints some basic info about a Graph

    Args:
        DG (networkx.DiGraph): The DiGraph
    """    
    for node in DG.nodes:
        print(node)
        print(DG.nodes[node])
    print("Node: ",DG.number_of_nodes()," Edges: ",DG.number_of_edges())

def loadConfig():
    """
    Loads the config from the disk to the global variable config
    """    
    try:
        global config
        config = configparser.ConfigParser()
        config.read(path+'/settings.ini')
        config = config['UserSettings']   
    except Exception:
        traceback.print_exc()
