from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
# Custom module for miscellaneous utility classes to support a GUI.
from guiUtils import userPath

Builder.load_file('kvSubPanels/camera.kv')        # Layout file for GUI sub-panel
Builder.load_file('kvSubPanels/vehiclestatus.kv')        # Layout file for GUI sub-panel
Builder.load_file('kvSubPanels/powercontrols.kv') # Layout file for GUI sub-panel
Builder.load_file('kvSubPanels/filediag.kv')      # Layout file for GUI sub-panel
Builder.load_file('kvSubPanels/statusbar.kv')     # Layout file for GUI sub-panel

#======================================== APP class ===============================================#
class engineApp(App):
  """
    Python Kivy App class

    The Kivy class is defined in the engine.kv Kivy file (NOTE: Kivy filename must be ALL lower case and not include the "App" postfix of this class name). 

    The Kivy "build" method is used here instead of the standard __init__ to define the various
    class properties
  """
  def build(self):
    """
    This is the first method that Kivy calls to build the GUI.
    """
    self.title = 'EngineAppGUI (ver0.0r210303)'
    self.icon = 'miniAutoLogoV2_32x32.jpg'
    # This initialization file is used to keep the last file/folder the user has used so it can be
    # re-open easily the next time the user user wants to select a file.  It also saves the
    # location and size of the UI window when it was closed so the next time the UI is opened it
    # opens at the same location/size.
    self.fileIO = userPath('engineApp.py')
    # Instantantiate a EngineAppGUI object for the GUI and at the same time also send the
    # reference to this main app object to the EngineAppGUI object so that properties from both
    # classes can easily be access from each other.
    # NOTE: This will assign the GUI object to the Kivy "self.root" property, i.e., use
    #       "self.root" to access all Kivy layouts/widgets/classes.  It is the Kivy "root rule".
    return EngineAppGUI(self)


  def selectFile(self):
    self.fileIO.fileType = [('text files', ('.txt', '.text')), ('all files', '.*')]
    self.fileIO.pathSelect(pathTag='EngineAppGUI')
    if self.fileIO.numPaths == 0: # User cancelled the selection
      self.root.statusBar.lblStatusBar.text = ' User cancelled selection'
    else: # The user selected an HDF5 file
      self.root.statusBar.lblStatusBar.text = ' File loaded !'
      # self.ui.ids.kvLytStatusBar.ids.kvLblStatusBar.text = ' File loaded !'
      self.root.fileDiag.lblFilePath.text = self.fileIO.currentPaths[0]
      self.root.fileDiag.selectButton.text = 'Selected File'


#======================================== GUI class ===============================================#
class EngineAppGUI(GridLayout):
  """
  This will instantiate the "root" Kivy property and the name used here MUST match exactly the Kivy
  class name used in the engine.kv main file.
  """
  imgTexture = ObjectProperty()   # kivy texture instance to display images

  def __init__(self, mainAppRef):
    """
      Object constructor method used to initiate the UI window.

      Also pass as parameter the App object reference so that any App property or methods can
      easily be accessed in this class directly if needed.
    """
    GridLayout.__init__(self)    # instantiate the parent class
    self.app = mainAppRef        # Property to access the App properties easily, e.g., 
                                 # the initialization file where last window properties are saved.
    #------------------------------------ GUI Window properties -----------------------------------#
    # Set the base window properties. Note that Kivy will automatically use this new Window object
    self.uiWindow = Window
    self.uiWindow.borderless = False
    # Canvases default background to light blue
    self.uiWindow.clearcolor = ([.01, .2, .36, 1])
    self.uiWindow.bind(on_request_close=self.uiCloseWindow)
    # Adjust the overall window location & size if the various parameters are available in the
    # initialization file
    winTmp = self.app.fileIO.appsGetDflt('winTop')
    if winTmp is not None:
      self.uiWindow.top = winTmp
    winTmp = self.app.fileIO.appsGetDflt('winLeft')
    if winTmp is not None:
      self.uiWindow.left = winTmp
    winTmp = self.app.fileIO.appsGetDflt('winSize')
    if winTmp is not None:
      self.uiWindow.size = winTmp
    else:
      # If the size is NOT available, then default it to the following
      self.uiWindow.size = (1000, 500)


  def uiCloseWindow(self, notUsed):
    """
      This method is used to do some clean up just before the window is closed.

      Callback method that is bind to the "on_request_close", i.e., last method executed before
      the window is actually closed.
    """
    # Save the current window position so that the next window re-opens at the same position and
    # size that the user last left it
    self.app.fileIO.appCfg['winTop'] = self.uiWindow.top
    self.app.fileIO.appCfg['winLeft'] = self.uiWindow.left
    self.app.fileIO.appCfg['winSize'] = self.uiWindow.size
    self.app.fileIO.appsWriteDfltVal()


#========================================== GUI launch ============================================#
if __name__ == "__main__":
  engineApp().run()
