#!/usr/bin/env python3
import sys, subprocess, pathlib
import wx

from graphBuilder import processResult
from graphUI import ShowUI

# ---------------------------------- Globals --------------------------------- #
#Local path
path = str( pathlib.Path(__file__).parent.absolute() )

#Globals
window = None

# ---------------------------------------------------------------------------- #
#                                User Interface                                #
# ---------------------------------------------------------------------------- #


class PanelTitle(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.SetBackgroundColour('white')

        # Create some sizers
        mainSizer = wx.BoxSizer(orient=wx.VERTICAL)

        vBox = wx.BoxSizer(orient=wx.VERTICAL)

        hBox = wx.BoxSizer(orient=wx.HORIZONTAL)
        
        #Create all the required widgets
        self.title = wx.StaticText(self, label="Gorgias-Visual")
        self.title.SetFont(wx.Font(wx.FontInfo(12).Bold()))
        self.subtitle = wx.StaticText(self, label="It visualizes the output of Gorgias using a graph")
        
        

        #Create the GUI sections and assign the widgets
        #vBox (TITLE - TOP SECTION)
        vBox.AddSpacer(5)
        vBox.Add(self.title,0, border=5)
        vBox.Add(self.subtitle,0, border=5)
        vBox.AddSpacer(5)

        hBox.Add(vBox,1)
        #Create and add image
        try:
            image = wx.Image(path+"/icon.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            self.icon = wx.StaticBitmap(self, -1, image)
            hBox.Add(self.icon,0)
        except Exception:
            print("icon.png is missing",file=sys.stderr)

        #Add to mainSizer
        mainSizer.Add(hBox,0,flag=wx.EXPAND|wx.ALL, border=20)
        
        self.SetSizerAndFit(mainSizer)

class PanelData(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Create some sizers
        mainSizer = wx.BoxSizer(orient=wx.VERTICAL)

        vBox = wx.BoxSizer(orient=wx.VERTICAL)

        #Create all the required widgets
        self.file_category = wx.StaticText(self, label="Select .pl File")
        self.file_category.SetFont(wx.Font(wx.FontInfo(10).Bold()))
        self.file_title = wx.StaticText(self, label="File Path")
        self.file_description = wx.StaticText(self, label="ATTENTION: File path must contain only latin characters")
        self.file_description.SetForegroundColour("Grey")
        
        self.file_path = wx.TextCtrl(self)
        self.file_button = wx.Button(self,label="Browse")

        fileSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        fileSizer.Add(self.file_path,1,wx.EXPAND)
        fileSizer.Add(self.file_button,flag=wx.LEFT,border=8)

        self.query_category = wx.StaticText(self, label="Query Options")
        self.query_category.SetFont(wx.Font(wx.FontInfo(10).Bold()))
        self.query_title = wx.StaticText(self, label="Query")
        self.query_description = wx.StaticText(self, label="Example:\n fly(tweety)")
        self.query_description.SetForegroundColour("Grey")

        self.query_data = wx.TextCtrl(self)

        #Bind widgets to events
        self.Bind(wx.EVT_BUTTON, self.OnBrowseClick, self.file_button)


        #Create the GUI sections and assign the widgets
        #VBOX (SETTINGS - MID SECTION)
        vBox.Add(self.file_category,0,flag=wx.ALL,border=5)
        vBox.Add(wx.StaticLine(self,size = (250, 1),  style = wx.LI_HORIZONTAL),0,flag=wx.EXPAND|wx.ALL,border=0)
        vBox.Add(self.file_title,0,flag=wx.ALL,border=5)
        vBox.Add(self.file_description,0,flag=wx.ALL,border=5)
        vBox.Add(fileSizer,proportion=1,flag=wx.EXPAND|wx.ALL,border=5)

        vBox.AddSpacer(20)

        vBox.Add(self.query_category,0,flag=wx.ALL,border=5)
        vBox.Add(wx.StaticLine(self,size = (250, 1),  style = wx.LI_HORIZONTAL),0,flag=wx.EXPAND|wx.ALL,border=0)
        vBox.Add(self.query_title,0,flag=wx.ALL,border=5)
        vBox.Add(self.query_description,0,flag=wx.ALL,border=5)
        vBox.Add(self.query_data,proportion=1,flag=wx.EXPAND|wx.ALL,border=5)

        vBox.AddSpacer(20)
        
        #Add to mainSizer
        mainSizer.Add(wx.StaticLine(self,size = (250, 1),  style = wx.LI_HORIZONTAL),0,flag=wx.EXPAND|wx.ALL,border=0)
        mainSizer.Add(vBox,0,flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=20)

        self.SetSizerAndFit(mainSizer)

    def OnBrowseClick(self,event):
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.pl|*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            file = self.dirname.replace("\\","/")+'/'+self.filename
            self.file_path.SetValue(file)
        dlg.Destroy()
 
class PanelConsole(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Create some sizers
        mainSizer = wx.BoxSizer(orient=wx.VERTICAL)
        hBox = wx.BoxSizer(orient=wx.HORIZONTAL)

        #Create all the required widgets
        self.log = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH2)
        self.console_text = wx.StaticText(self, label="Console")
        self.console_text.SetFont(wx.Font(wx.FontInfo(8)))
        self.console_text.SetForegroundColour("Grey")
        self.console_clear_button = wx.Button(self,label="clear",size=(50,20))
        self.console_clear_button.SetFont(wx.Font(wx.FontInfo(8)))
        self.console_clear_button.SetForegroundColour("Grey")

        cosoleLineSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        cosoleLineSizer.Add(self.console_text)
        cosoleLineSizer.AddStretchSpacer(prop=1)
        cosoleLineSizer.Add(self.console_clear_button)

        #Bind widgets

        self.Bind(wx.EVT_BUTTON, self.OnClearClick,self.console_clear_button)
        
        #Create the GUI sections and assign the widgets
        #(CONSOLE)
        hBox.Add(self.log,proportion=1,flag=wx.EXPAND)

        #Add to mainSizer
        mainSizer.Add(wx.StaticLine(self,size = (250, 1),  style = wx.LI_HORIZONTAL),0,
                      flag=wx.EXPAND|wx.BOTTOM,border=5)
        mainSizer.Add(cosoleLineSizer,flag=wx.LEFT|wx.RIGHT|wx.EXPAND,border=10)
        mainSizer.Add(hBox,proportion=1,flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND,border=10)
        self.SetSizerAndFit(mainSizer)
        
        #Redirect output and errors to this console
        redir = RedirectText(self.log)
        redirError = RedirectTextError(self.log)
        sys.stdout = redir
        sys.stderr = redirError

    def OnClearClick(self,event):
        self.log.Clear()

class PanelButtons(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Create some sizers
        mainSizer = wx.BoxSizer(orient=wx.VERTICAL)

        vbox = wx.BoxSizer(orient=wx.VERTICAL)

        
        #Create all the required widgets
        self.run_button = wx.Button(self,label="Run")
        buttonSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        buttonSizer.AddStretchSpacer(prop=1)
        buttonSizer.Add(self.run_button,flag=wx.LEFT,border=8)
        buttonSizer.AddStretchSpacer(prop=1)

        self.Bind(wx.EVT_BUTTON, self.OnRunClick,self.run_button)

        #Create the GUI sections and assign the widgets
        #VBOX (START BUTTON - BOTTOM SECTION)
        vbox.Add(buttonSizer,proportion=1,flag=wx.EXPAND|wx.ALL,border=10)

        #Add to mainSizer
        mainSizer.Add(vbox,0,flag=wx.EXPAND|wx.ALL, border=10)
        
        self.SetSizerAndFit(mainSizer)

    def OnRunClick(self,event):
        
        #Get Values from fields
        query = self.GetParent().dataPanel.query_data.GetValue()  
        filename = self.GetParent().dataPanel.file_path.GetValue()
        
        if (filename == ""): 
            print("Select a .pl file")
        else:
            runProlog(filename,query)
        

# Main GUI
class MainFrame ( wx.Frame ):
    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = "Gorgias-Visual", 
                           pos = wx.DefaultPosition, size = wx.Size( 600,750 ))
        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        #Set icon
        try:
            icon = wx.Icon()
            icon.CopyFromBitmap(wx.Bitmap(path+"/icon.png", wx.BITMAP_TYPE_ANY))
            self.SetIcon(icon)
        except Exception:
            print("icon.png is missing",file=sys.stderr)


        self.SetBackgroundColour('LightGrey')
        frameSizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.SetSizer(frameSizer)
        self.Layout()

        #Create the Panels
        self.tittlePanel = PanelTitle(self)
        self.dataPanel = PanelData(self)
        self.consolePanel = PanelConsole(self)
        self.buttonPanel = PanelButtons(self)

        #Add panels to view
        frameSizer.Add(self.tittlePanel,flag=wx.EXPAND)
        frameSizer.Add(self.dataPanel,flag=wx.EXPAND)
        frameSizer.Add(self.consolePanel,1,flag=wx.EXPAND)
        frameSizer.Add(self.buttonPanel,flag=wx.EXPAND)
        
        self.Centre( wx.BOTH )
        self.SetMinSize((400,600))
        
    def OnClose(self, event):
        self.Destroy()

        
        


class RedirectText(object):
    def __init__(self,aWxTextCtrl):
        self.out = aWxTextCtrl

    def write(self,string):
        self.out.AppendText(string)

class RedirectTextError(object):
    def __init__(self,aWxTextCtrl):
        self.out = aWxTextCtrl

    def write(self,string):
        defaultStyle = self.out.GetDefaultStyle()
        self.out.SetDefaultStyle(wx.TextAttr(wx.RED))
        self.out.AppendText(string)
        self.out.SetDefaultStyle(defaultStyle)
        
# ---------------------------------------------------------------------------- #
#                                   Functions                                  #
# ---------------------------------------------------------------------------- #


def main():
    """
    Displays the main GUI
    """  
    global window  
    app = wx.App()
    window = MainFrame(None)
    window.Show(True)
    app.MainLoop()



def runProlog(file,query):
    """
    Creates a prolog.py subprocess that communicates with SWI-Prolog and gets back the result, 
    process it and opens the Graph UI

    Args:
        file (str): The path to the .pl file
        query (str): The query to run
    """    
    
    #Create process
    proc = subprocess.Popen([sys.executable or 'python', path+'/prolog.py', '-f' ,file.replace("\\","/"),'-q',query ] ,
                            stdout=subprocess.PIPE ,stderr=subprocess.PIPE )
    
    #Run process
    try:
        outs, errs = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        print("Error: Subprocess Timeout Expired",file=sys.stderr)
        proc.kill()
        #outs, errs = proc.communicate() #To flush the output. 
        #Disabled because it is very rare to happen and doesn't work correctly
        return
    out, err = outs.decode('utf-8') , errs.decode('utf-8')
    
    #Check the output of the process
    if(out != "" and not out.isspace()):
        #Returned a result. Not empty. Procede to proccess and display GUI
        DG, holds, isFact = processResult(query,out)
        ShowUI(DG,query,holds,isFact,"Gorgias Graph",parent=window)
        
    elif(type(errs) is not None):
        #Returned an error
        if(err == "" or err.isspace()): #Error is empty
            print("PROLOG response was empty. Check your input values.",file=sys.stderr)
        else:
            print("Error",err,file=sys.stderr)

    else: print("An Undefined error occurred",file=sys.stderr)


if __name__ == "__main__":
    main()