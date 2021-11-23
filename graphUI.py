import wx
from wx.lib.floatcanvas import FloatCanvas
from wx.lib.floatcanvas.FCObjects import *
from wx.lib.floatcanvas.Utilities.BBox import asBBox

import networkx as nx
import random
import configparser
import pathlib

# ---------------------------------- Globals --------------------------------- #
#Local path
path = str( pathlib.Path(__file__).parent.absolute() )

#Globals
CanvasFrame = None
holds = None
config = None
debugPrint = False

positions={}
descriptions={}
edges={}
resultTitle="resultTitle"

class DescriptionFrame(wx.Frame):
    """
    Custom Node Description Window
    """
    
    def __init__(self, text, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        frameSizer = wx.BoxSizer(orient=wx.VERTICAL)
        hBox = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.SetSizer(frameSizer)
        
        self.SetBackgroundColour("background")
        self.SetIcon(wx.ArtProvider.GetIcon(wx.ART_FIND, wx.ART_OTHER))
        
        self.titleText = wx.StaticText(self, 
                                       label=text, 
                                       style = wx.CENTER)
        self.titleText.SetFont(wx.Font(wx.FontInfo(config.getint("DescriptionTextSize"))))
        
        hBox.AddStretchSpacer(1)
        hBox.Add(self.titleText, flag=wx.EXPAND)
        hBox.AddStretchSpacer(1)
        
        frameSizer.AddStretchSpacer(1)
        frameSizer.Add(hBox, flag=wx.EXPAND|wx.ALL, border=20)
        frameSizer.AddStretchSpacer(1)
        
        self.Layout()
        self.SetSizerAndFit(frameSizer)
        self.SetMinSize((250,150))
        self.Show()
        self.SetFocus()


class FloatCanvasFrame(wx.Frame):
    """
    Custom FloatCanvas Class
    """ 

    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.dc = wx.ScreenDC()
        frameSizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.SetSizer(frameSizer)
        
        #Set icon
        try:
            icon = wx.Icon()
            icon.CopyFromBitmap(wx.Bitmap(path+"/icon.png", wx.BITMAP_TYPE_ANY))
            self.SetIcon(icon)
        except Exception:
            print("icon.png is missing",file=sys.stderr)
        
        self.SetMinSize((400,400))
        self.Layout()
        # -------------------------- Set values from config -------------------------- #
        
        self.compactHoverDesc = config.getboolean("CompactHoverDescriptions")
        self.zoomSpeed = config.getfloat("ZoomSpeed")
        
        self.nodeSize = config.getint('NodeSize')
        self.nodeTextSize = config.getint('NodeTextSize')
        self.selectionRingSize = config.getint('SelectionRingSize')
        
        self.arrowSize = config.getint('ArrowSize')
        self.arrowLineSize = config.getint('ArrowLineSize')
        self.arrowAngle = config.getint('ArrowAngle')
        
        self.titleTextSize = config.getint('TitleTextSize')
        self.hoverTextSize = config.getint('HoverTextSize')
        
        # ----------------------------- Add Colors to DB ----------------------------- #
        wx.TheColourDatabase.AddColour("background",wx.Colour(config.get('BackgroundColor')))
        wx.TheColourDatabase.AddColour("node",wx.Colour(config.get('NormalNodeColor')))
        wx.TheColourDatabase.AddColour("acceptNode",wx.Colour(config.get('AcceptNodeColor')))
        wx.TheColourDatabase.AddColour("rejectNode",wx.Colour(config.get('RejectNodeColor')))
        wx.TheColourDatabase.AddColour("nodeText",wx.Colour(config.get('NodeTextColor')))
        wx.TheColourDatabase.AddColour("selectedNodeRing",wx.Colour(config.get('SelectionRingColor')))
        wx.TheColourDatabase.AddColour("hoverNodeRing",wx.Colour(config.get('HoverRingColor')))
        
        # ------------------------------- Add the Title ------------------------------ #
        self.titleText = wx.StaticText(self, 
                                       label=resultTitle, 
                                       style = wx.ALIGN_CENTRE_HORIZONTAL)
        self.titleText.SetFont(wx.Font(wx.FontInfo(self.titleTextSize).Bold()))
        frameSizer.Add(self.titleText, 0, flag=wx.EXPAND)
        
        # ------------------------------ Add the Canvas ------------------------------ #
        self.Canvas = FloatCanvas.FloatCanvas(self, size = (100,100), BackgroundColor = "background")
        frameSizer.Add(self.Canvas, 1, flag=wx.EXPAND)
        # ---------------- Create variables and events for navigation ---------------- #
        self.mouseDown = False
        self.lastx = self.x = 0
        self.lasty = self.y = 0
        self.Canvas.Bind(FloatCanvas.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Canvas.Bind(FloatCanvas.EVT_LEFT_UP, self.OnMouseUp)
        self.Canvas.Bind(FloatCanvas.EVT_MOTION, self.OnMouseMotion)
        self.Canvas.Bind(FloatCanvas.EVT_MOUSEWHEEL, self.OnMouseWheel)
        
        # -------------------------------- Status Bar -------------------------------- #
        self.CreateStatusBar()
        self.StatusBar.SetFieldsCount(2)
        
        # --------------------------------- Set Data --------------------------------- #
        self.SetData()
        
        # -------------------------------- Show Window ------------------------------- #
        self.Show(True)
        self.Canvas.ZoomToBB()
        self.Canvas.Zoom(0.8)
        
        # ---------------------------- Bind Canvas events ---------------------------- #
        #Bind events for node selection/hover
        #Must be done after the canvas is shown
        self.NodeObjects.Bind(FloatCanvas.EVT_FC_ENTER_OBJECT, self.OnOverPoints)
        self.NodeObjects.Bind(FloatCanvas.EVT_FC_LEAVE_OBJECT, self.OnLeavePoints)
        self.NodeObjects.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.OnClickPoints)
        

    # ---------------------------------------------------------------------------- #
    #                                Data Functions                                #
    # ---------------------------------------------------------------------------- #

    def SetData(self):
        # --------------------------- Add all arrows/edges --------------------------- #
        for u,v in edges:
            x , y = positions[u][0], positions[u][1]
            dx , dy = positions[v][0], positions[v][1]
            
            arrowsObj = ArrowLine([(x, y), (dx, dy)], 
                                  LineWidth=self.arrowLineSize, 
                                  ArrowHeadSize=self.arrowSize, 
                                  ArrowHeadAngle=self.arrowAngle, 
                                  InForeground=True)
            self.Canvas.AddObject(arrowsObj)

        # --------------------------------- Add Nodes -------------------------------- #
        self.nodes=[]
        for node in positions:
            self.nodes.append(positions[node])
        nodesObj = PointSet(tuple(self.nodes), 
                            Diameter=self.nodeSize, 
                            Color="node", 
                            InForeground=True)
        self.NodeObjects = self.Canvas.AddObject(nodesObj)
        
        # --------------------------- Add special root node -------------------------- #
        
        rootNodeObj = Point(tuple(self.nodes[0]), 
                            Diameter=self.nodeSize, 
                            Color="acceptNode" if holds else "rejectNode", 
                            InForeground=True)
        self.Canvas.AddObject(rootNodeObj)

        # ------------------------------ Add all labels ------------------------------ #
        self.nodeLabels =[]
        self.lastHighlight = -1
        self.hoverName = ""
        self.highlightedLabel = None
        for node in positions:
            nodeLabel = Text(node, 
                             positions[node], 
                             Size=self.nodeTextSize, 
                             Position="cc", 
                             Color="nodeText", 
                             Weight=wx.FONTWEIGHT_BOLD, 
                             InForeground=True)
            self.nodeLabels.append(nodeLabel)
            self.Canvas.AddObject(nodeLabel)
            
        # -------------------------- Set Font for hover text ------------------------- #
        hoverFont = wx.Font(config.getint("HoverTextSize"), 
                            wx.FONTFAMILY_DEFAULT, 
                            wx.FONTSTYLE_NORMAL, 
                            wx.FONTWEIGHT_NORMAL)
        wx.DC.SetFont(self.dc,hoverFont)
        # ----------------------------- Hover Description ---------------------------- #
        self.descriptions = descriptions
        self.overPoints = False
        width = config.getfloat('VerticalNodeDist')
        self.hoverDescription = Text("", 
                                     (0,0),
                                     Position="cc", 
                                     Font=hoverFont, 
                                     InForeground=True)
        self.hoverDescriptionBox = Rectangle((-width/2,0), 
                                             (width,0), 
                                             FillColor="background", 
                                             InForeground=True)
        self.hoverDescriptionBox.Hide()
        self.Canvas.AddObject(self.hoverDescriptionBox)
        self.Canvas.AddObject(self.hoverDescription)
        
        

    def UpdateData(self):
        # ------------------------------- Update Canvas ------------------------------ #
        #Close old description windows
        self.Canvas.DestroyChildren()
        #Reset Canvas and Set Data
        self.Canvas.ClearAll()

        #Reset variables for navigation
        self.mouseDown = False
        self.lastx = self.x = 0
        self.lasty = self.y = 0
        
        #Update Title and Data
        self.titleText.SetLabel(resultTitle)
        self.Layout()
        self.SetData()
        
        # -------------------------------- Show Window ------------------------------- #
        self.SetFocus()
        self.Canvas.ZoomToBB()
        self.Canvas.Zoom(0.8)
        
        # ---------------------------- Bind Canvas events ---------------------------- #
        #Bind events for node selection/hover
        #Must be done after the canvas is shown
        self.NodeObjects.Bind(FloatCanvas.EVT_FC_ENTER_OBJECT, self.OnOverPoints)
        self.NodeObjects.Bind(FloatCanvas.EVT_FC_LEAVE_OBJECT, self.OnLeavePoints)
        self.NodeObjects.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.OnClickPoints)
        

    # ---------------------------------------------------------------------------- #
    #                                Event Functions                               #
    # ---------------------------------------------------------------------------- #

    def OnOverPoints(self, obj):
        #Find out which point
        self.overPoints = True
        nodeID = obj.FindClosestPoint(obj.HitCoords)
        if (debugPrint): print("Mouse over point: %s" % nodeID)
        
        # --------------------------- Create hover elements -------------------------- #
        #Label Highlight
        self.lastHighlight = nodeID
        oldLabel = self.nodeLabels[nodeID]
        self.highlightedLabel = Text(" "+oldLabel.String+" ", 
                                     tuple(self.nodes[int(nodeID)]), 
                                     Size=self.nodeTextSize, 
                                     Position="cc", Color="background", BackgroundColor="nodeText", 
                                     Weight=wx.FONTWEIGHT_BOLD, InForeground=True)
        self.Canvas.AddObject(self.highlightedLabel)
        self.hoverName = oldLabel.String
        #Ring Highlight
        self.hoverRing = Point(tuple(self.nodes[int(nodeID)]), 
                               Diameter=self.nodeSize+self.selectionRingSize, Color="hoverNodeRing")
        self.NodeRing = self.Canvas.AddObject(self.hoverRing)
        
        self.Canvas.Draw(Force=True)

    def OnLeavePoints(self, obj):
        #Find out which point
        self.overPoints = False
        nodeID = obj.FindClosestPoint(obj.HitCoords)
        if (debugPrint): print("Mouse left point: %s" % nodeID)

        # ---------------------------- Hide hover elements --------------------------- #
        self.hoverName = ""
        self.hoverDescriptionBox.Hide()
        self.hoverDescription.Hide()
        try:
            self.Canvas.RemoveObject(self.highlightedLabel)
        except Exception: pass
        try:
            self.Canvas.RemoveObject(self.hoverRing)
        except Exception: pass
        
        
        self.Canvas.Draw() 

    def OnClickPoints(self, obj):
        #Find out which point
        nodeID = obj.FindClosestPoint(obj.HitCoords)
        if (debugPrint): print("Mouse left down on point: %s" % nodeID)
        
        # --------------------------- Create selection ring -------------------------- #
        try:
            self.Canvas.RemoveObject(self.thering)
        except Exception: pass
        self.thering = Point(tuple(self.nodes[int(nodeID)]), 
                             Diameter=self.nodeSize+self.selectionRingSize, 
                             Color="selectedNodeRing")
        self.NodeRing = self.Canvas.AddObject(self.thering)
        
        self.Canvas.Draw(Force=True)
        
        # --------------------------- Open Node Description -------------------------- #
        nodeName = self.nodeLabels[nodeID].String
        #Check if description window exists
        windowExists = False
        for descWindow in self.Canvas.GetChildren():
            if (descWindow.GetLabel() == nodeName):
                descWindow.Restore()
                descWindow.SetFocus()
                windowExists = True
                break
        if (windowExists == False):
            desc = self.descriptions[nodeName]['description']
            DescriptionFrame(parent=self.Canvas,
                            title=nodeName,
                            text=desc,
                            pos=self.ClientToScreen(obj.HitCoordsPixel))       
            
            
         
    def OnMouseDown(self, event):
        self.mouseDown=True
        self.x, self.y = self.lastx, self.lasty = event.Coords
        if (debugPrint): print(event.Coords)

    def OnMouseUp(self, event):
        self.mouseDown=False

    def OnMouseMotion(self, event):
        # ----------------------------- Status Bar Update ---------------------------- #
        self.SetStatusText(f"{event.Coords[0]:.3f}, {event.Coords[1]:.3f}",0)
        self.SetStatusText(f"{self.hoverName}",1)
        
        if (self.overPoints):
            # --------------------------- Create hover Description -------------------------- #
            textDesc = self.descriptions[self.nodeLabels[self.lastHighlight].String]['description']
            textDescList = textDesc.split("\n")
            offset = len(textDescList)
            if (self.compactHoverDesc):
                if (len(textDescList)>1):
                    textDesc = textDescList[0]+"\n..."
                    offset = 2
                else:
                    textDesc = textDescList[0]
                    offset = 1
            self.hoverDescription.SetText(textDesc)
            
            #Center Text
            te = wx.DC.GetMultiLineTextExtent(self.dc,textDesc)
            teWorld = self.Canvas.ScalePixelToWorld(te)
            
            newX , newY = (event.Coords[0] - teWorld[0]/2, event.Coords[1] - teWorld[1]-(teWorld[1]/offset)*2 )
            if (debugPrint): print(newX,newY,te,teWorld)
            self.hoverDescription.SetPoint((newX,newY))
            
            padding = 0.05
            if (debugPrint): print("Before",newX,newY,teWorld)
            boxX = (newX-padding)
            boxY = (newY+padding)
            boxH = (teWorld[0]+(padding*2))
            boxW = (teWorld[1]-(padding*2))
            if (debugPrint): print("After",boxX,boxY,(boxH,boxW))
            
            self.hoverDescriptionBox.SetShape((boxX,boxY),(boxH,boxW))
            self.hoverDescriptionBox.SetFillColor("background")
            self.hoverDescriptionBox.PutInBackground()
            self.hoverDescriptionBox.PutInForeground()
            self.hoverDescriptionBox.Show()
            
            self.hoverDescription.PutInBackground()
            self.hoverDescription.PutInForeground()
            self.hoverDescription.Show()
            
            self.Canvas.Draw()
        
        # --------------------------------- Move View -------------------------------- #
        if event.Dragging() and self.mouseDown:
            self.x, self.y = event.Coords
            self.Canvas.MoveImage((self.lastx-self.x,self.lasty-self.y),"World")

    def OnMouseWheel(self, event):
        canvasA = self.Canvas.ViewPortBB[0]
        canvasB = self.Canvas.ViewPortBB[1] 
        cur_xlim = [canvasA[0],canvasB[0]]
        cur_ylim = [canvasA[1],canvasB[1]]
        x_cursor = event.Coords[0] # get event x location
        y_cursor = event.Coords[1] # get event y location
        
        if(debugPrint): print("Current BB: ",cur_xlim,cur_ylim)
        if(debugPrint): print(event)

        if (event.GetWheelRotation() > 0):
            #zoom in
            scale_factor = 1 / self.zoomSpeed
        else:
            #zoom out
            scale_factor = self.zoomSpeed

        # -------------------------------- View scale -------------------------------- #
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        relx = (cur_xlim[1] - x_cursor)/(cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - y_cursor)/(cur_ylim[1] - cur_ylim[0])
        xBB = [x_cursor - new_width * (1-relx), x_cursor + new_width * (relx)]
        yBB = [y_cursor - new_height * (1-rely), y_cursor + new_height * (rely)]
        
        canvasA = [xBB[0],yBB[0]]
        canvasB = [xBB[1],yBB[1]]
        
        self.hoverDescriptionBox.Hide()
        self.hoverDescription.Hide()
        self.Canvas.ZoomToBB(NewBB=asBBox([canvasA,canvasB]))
        
    def OnClose(self, event):
        global CanvasFrame
        if (not isinstance(CanvasFrame,list)): CanvasFrame = None
        self.Destroy()


def hierarchy_pos(G, root=None, width=1.0, vert_gap=1.0, root_y=0.0, root_x=0.0, downDirection=True):
    """
    Recursive function that calculates the node positions of a tree DiGraph

    Args:
        G (networkx.DiGraph): The Directed Graph from networkx
        root (str, optional): The root of the tree Graph. Defaults to None.
        width (float, optional): The amount of space the Graph will take horizontally. Defaults to 1.0.
        vert_gap (float, optional): The vertical spaceing of the levels of the tree. Defaults to 1.0.
        root_y (float, optional): vertical location of root. Defaults to 0.
        root_x (float, optional): horizontal location of root. Defaults to 0.
        downDirection (bool, optional): The Direction of the tree. Defaults to True.

    Raises:
        TypeError: If the graph is not a tree

    Returns:
        dict: The dict of node positions
    """    
    
    #Checks if the graph is actually a tree
    if not nx.is_tree(G):
        raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

    #Finds root if not provided
    if root is None:
        if isinstance(G, nx.DiGraph):
            root = next(iter(nx.topological_sort(G)))  #allows back compatibility with nx version 1.11
        else:
            root = random.choice(list(G.nodes))

    #The actual recursive function
    def _hierarchy_pos(G, root, width=1.0, vert_gap=1.0, 
                       root_y=0.0, root_x=0.0, 
                       downDirection=True, pos=None, parent=None):
        """
        Internal recursive function

        Extra Args:
            pos (dict, optional): The dict of node positions. Defaults to None.
            parent (str, optional): The parent of this branch. Defaults to None.

        Returns:
            dict: The dict of node positions
        """        

        if pos is None:
            pos = {root:(root_x,root_y)}
        else:
            pos[root] = (root_x,root_y)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)  
        if len(children)!=0:
            dx = width/len(children) 
            next_x = root_x - width/2 - dx/2
            for child in children:
                next_x += dx
                if (downDirection):
                    new_root_y = root_y-vert_gap
                else:
                    new_root_y = root_y+vert_gap
                pos = _hierarchy_pos(G, child, width=dx, vert_gap=vert_gap, 
                                    root_y=new_root_y, root_x=next_x, 
                                    downDirection=downDirection, pos=pos, parent=root)
        return pos
    return _hierarchy_pos(G, root, width, vert_gap, root_y, root_x, downDirection)


def ShowUI(DG,query,argumentHolds,argumentIsFact,windowTitle,parent=None):
    """
    Opens/Updates the UI

    Args:
        DG (networkx.DiGraph): The Graph
        query (str): The query
        argumentHolds (bool): if the query/argument holds
        argumentIsFact (bool): if the query/argument is a fact
        windowTitle (str): The title of the window
        parent (object, optional): The parent window of the windows that will open
    """    
    loadConfig()
    
    #Get Node Positions
    global positions, descriptions, edges
    positions = hierarchy_pos(DG.reverse(), 
                              width=config.getfloat('TreeWidth'), 
                              vert_gap=config.getfloat('VerticalNodeDist'), 
                              downDirection=config.getboolean('TreeGrowDirectionDown') )
    descriptions = DG.nodes
    edges = DG.edges
    
    #Set Argument truth
    global holds, resultTitle
    holds = argumentHolds
    if (argumentIsFact):
        resultTitle = "Argument "+query+" is a Fact"
    elif (argumentHolds):
        resultTitle = "Argument "+query+" Holds"
    else:
        resultTitle = "Argument "+query+" does not Hold"
    
    global CanvasFrame      
    if (config.getboolean('multiWindow')):
        if (CanvasFrame is None): CanvasFrame = []
        CanvasFrame.append(FloatCanvasFrame(parent, title=windowTitle, size=(1280,720)))
    else:
        if (CanvasFrame is None):
            CanvasFrame = FloatCanvasFrame(parent, title=windowTitle, size=(1280,720))
        else:
            CanvasFrame.UpdateData()

def ShowUIDemo(id=1, DiGraph=None, windowTitle="Graph UI"):
    """
    Shows a Demo of the UI

    Args:
        id (int, optional): The id of the demo. Defaults to 1.
        DiGraph (networkx.DiGraph, optional) : A DiGraph. If given the "id" will be ignored
        windowTitle (str, optional): The title of the window.

    1 : MultiNode
    2 : MultiNode Sided
    3 : 2Node
    4 : Single Node.
    """    
    loadConfig()
    
    #Graph is given
    if (DiGraph != None): 
        DG = DiGraph
        
    #Multi Node
    elif (id==1):
        nodes_dictionary = [('D',{'description':"D Description"}),
            ('B',{'description':"B Description1\nB Description2"}),
            ('C',{'description':"C Description"}),
            ('A',{'description':"A Description1\nA Description2"}),
            ('X',{'description':"X Description1\nX Description2\nX Description3"}),
            ('Y',{'description':"Y Description1\nY Description2\nY Description3\nY Description4"}),
            ('Z',{'description':"Z Description1\nZ Description2\nZ Description3\nZ Description4\nZ Description5"}),
            ('R',{'description':"R Description1\nR Description2\nR Description3\nR Description4\nR Description5\nR Description6"})]
        DG = nx.DiGraph()
        DG.add_nodes_from(nodes_dictionary)
        DG.add_edge("X","B")
        DG.add_edge("Y","B")
        DG.add_edge("B","C")
        DG.add_edge("Z","A")
        DG.add_edge("R","A")
        DG.add_edge("A","C")
        DG.add_edge("C","D")
    
    #Multi Node Sided
    elif (id==2):
        nodes_dictionary = [('A',{'description':"A Description"}),('B',{'description':"B Description"}),
            ('C',{'description':"C Description"}),('D',{'description':"D Description"}),
            ('E',{'description':"E Description"}),('F',{'description':"F Description"}),
            ('G',{'description':"G Description"}),('H',{'description':"H Description"}),
            ('I',{'description':"I Description"}),]
        DG = nx.DiGraph()
        DG.add_nodes_from(nodes_dictionary)
        DG.add_edge("A","C")
        DG.add_edge("B","C")
        DG.add_edge("C","E")
        DG.add_edge("I","E")
        DG.add_edge("E","G")
        DG.add_edge("F","G")
        DG.add_edge("G","D")
        DG.add_edge("H","D")

    #Two Nodes Vertical
    elif (id==3):
        DG = nx.DiGraph()
        DG.add_nodes_from([('D',{'description':"D Description"}),('A',{'description':"A Description"})])
        DG.add_edge("A","D")

    #Single Node
    else:
        DG = nx.DiGraph()
        DG.add_nodes_from([('D',{'description':"D Description"})])

    
    
    #Get Node Positions
    global positions, descriptions, edges
    positions = hierarchy_pos(DG.reverse(),"D", 
                              width=config.getfloat('TreeWidth'), 
                              vert_gap=config.getfloat('VerticalNodeDist'), 
                              downDirection=config.getboolean('TreeGrowDirectionDown'))
    descriptions = DG.nodes
    edges = DG.edges
    
    #Set Argument truth
    global holds, resultTitle
    holds = True
    resultTitle = "This is a Demo!"
    
    app = wx.App(False)
    CanvasFrame = FloatCanvasFrame(None, title=windowTitle, size=(1280,720) )
    app.MainLoop()

def loadConfig():
    """
    Loads the config from the disk to the global variable config
    """     
    #Set global config
    global config
    config = configparser.ConfigParser()
    config.read(path+'/settings.ini')
    config = config['UserSettings']
    #Set global debugPrint
    global debugPrint
    debugPrint = config.getboolean('printDebug')


if __name__ == "__main__":
    ShowUIDemo(1)













