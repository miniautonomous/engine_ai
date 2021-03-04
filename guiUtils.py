# Standard imports
import os
import platform
import json
import glob
import tkinter
import tkinter.filedialog as fileDiag
import tkinter.messagebox as messagebox
from tkfilebrowser import askopendirnames as multiDirs


class userPath(object):
  """
    Description:
      This class covers a bunch of generic file IO operations that the user generally
      needs in all GUI applications.
      
      1) Create and initialize an App initialization or configuration files where
         various default values (saved in a dictionary) are written to disk.
      2) opens a file dialog to allow the user to select a file or folder.  At the same
         time, it is use to track which folder was last  used to read or write files or
         select a folder for a given 'pathTag'.
         The purpose of this tracking is to avoid for the user to manually browse back to a
         given location to re-select the next file or select the same file at a later time.
      3) Miscellaneous methods to get file and folder lists.
      4) ...
  """

  def __init__(self, appModule=None): # Object constructor
    # Set some properties here to make sure that they are attached to this instance
    self.currentPaths = []     # List of ALL the desired full path to files
    self.numPaths = 0          # Number of paths in the tuple, same as len(currentPaths)
    self.histPaths = {}        # Dict used to save previously used "currentPaths" list
                               # property so they can easily be recalled when needed.
    self.appCfg = {}           # dict of all the various parameters, e.g., initial path
                               # which is used by the user based on the 'pathTag' key
    # NOTE: It is assumed here that an 'App' package base folder is one folder above
    #       this module location.  In other words, this module 'userUtils.py' is located
    #       in a sub-folder of the 'App' package, e.g., uiAPI or fAPI.  This implies that
    #       the 'App' configuration files where various default values are saved using
    #       the 'appCfg' property dictionary is also located in the base 'App' folder
    #       saved in the 'appFolder' property
    self.appModule = appModule
    self.appCfgFile = None     # This the full path of the file where the dictionary
                               # 'appCfg' is saved on disk.
    self.appFolder = None      # This is the base folder of the 'App'
    # Properties - that the user can customize prior to calling a method
    self.fileMultiSelect = False
    self.filePrompt = 'Please select a File:'
    self.fileType = [('all files', '.*')]
    # Default data folder path specified by the user
    self.userDataFolder = None
    # find the os type
    self.osType = platform.system()

    if self.appModule is not None:
      # Create if needed the initialization file of this class/module that contains the
      # dict 'appCfg'. This 'appCfg' dictionary keeps track of the last location that the user used.
      # The following guarantees that the initialization file is  available and has some default
      # values.
      # 1. Figure out the complete module path (the command below will retrieve the full path of
      # the App module)
      self.appCfgFile = os.path.abspath(self.appModule)
      # remove the ".py" extension
      self.appCfgFile, _ = os.path.splitext(self.appCfgFile)
      # This will get the path without filename (use os.path.join to add back filename).
      self.appFolder, _ = os.path.split(self.appCfgFile)
      if self.osType == 'Windows':
        self.appCfgFile += '_win.cfg'
      else:
        self.appCfgFile += '_lnx.cfg'

      # 2. Actually create the 'App' configuration file if needed
      if not os.path.isfile(self.appCfgFile):
        # Initialize the dictionary key associated with the default path
        self.appCfg['defaultPath'] = os.path.expanduser('~')
        self.appCfg['cfgFilePath'] = self.appCfgFile
        # Save the dictionary to init file.
        with open(self.appCfgFile, 'w') as tmpFile:
          json.dump(self.appCfg, tmpFile)
      else:
        # Simply read the file if it exist
        with open(self.appCfgFile) as tmpFile:
          self.appCfg = json.load(tmpFile)


  def storeCurrentPaths(self, keyName):
    """
      Method that adds a dictionary entry to the history property "histPaths" to save the
      object "currentPaths" property so it can be recalled later using that key.

    Arguments:
      keyName {[string]} -- [Dictionary key name use to save the "currentPaths"]
    """
    self.histPaths[keyName] = self.currentPaths


  def appsGetDflt(self, keyName):
    if keyName in self.appCfg.keys():
      keyValue = self.appCfg[keyName]
    else:
      keyValue = None
    return keyValue


  def appsWriteDfltVal(self):
    """
      Saves the appCfg property sorted dictionary to a text file.
    """
    if self.appModule is not None:
      with open(self.appCfgFile, 'w') as tmpFile:
        json.dump(self.appCfg, tmpFile, sort_keys=True)


  def readDict(self, dictPath):
     if os.path.isfile(dictPath):
      # Simply read the file if it exist and return its content
      with open(dictPath) as tmpFile:
        return json.load(tmpFile)


  def selUserDataFolder(self, folderPath, action='validate', pathTag='defaultPath'):
    """
      This method saves a valid path to a user folder in the object property
      "userDataFolder".  At a minimum, it puts the user home folder path in that
      object property.

      NOTE: Do not confuse with pathSelect!!! Actually this method is a "parent" and
            uses pathSelect method with the 'select' action.

      Currently supported action inputs:
        'validate'
        'confirm'
        'select'
    """
    if folderPath is None:
      folderPath = '' # Use an empty path to avoid error

    if action.lower() == 'validate':
      # Need to ensure the specified folder path is an existing directory
      if not os.path.isdir(folderPath):
        self.userDataFolder = os.path.expanduser('~') # Return the user home folder
      else:
        self.userDataFolder = folderPath # Folder exist, so simply return that
    elif action.lower() == 'confirm':
      if  not os.path.isdir(folderPath):
        # Folder not available, so query the user to confirm which folder to use.
        self.pathSelect(pathTag, 'dirSelect')
        # The file dialog above will save the path in the object property.
        if self.numPaths is not 0:
          self.userDataFolder = self.currentPaths[0]
        else:
          self.userDataFolder = os.path.expanduser('~') # Return the user home folder
      else:
        self.userDataFolder = folderPath # Folder exist, so simply return that
    elif action.lower() == 'select':
      # Open the file dialog (which will save the path in the object property).
      self.pathSelect(pathTag, 'dirSelect')
      if self.numPaths is not 0:
        self.userDataFolder = self.currentPaths[0]
      else:
        self.userDataFolder = os.path.expanduser('~') # Return the user home folder
    else:
      self.userDataFolder = None
      raise ValueError('Unsupported "action" input ', \
                       'method: userDfltFolder ', \
                       'class: userPath')


  def pathSelect(self, pathTag='defaultPath', pathType='fileRead'):
    """
    Method that uses the input parameter pathTag as a dictionary key so that previously
    selected path from an given application be re-used. Typically, the calling
    application "label" is used for this string so it is easy to recall.
    
    Keyword Arguments:
      pathTag {str} -- Can be any string, e.g. application name. 
                       (default: {'defaultPath'})
      pathType {str} -- String use to customize the file dialog option. The following
                        types are currently supported;
                          1) 'fileRead'
                          2) 'fileWrite'
                          3) 'dirSelect'
                        (default: {'fileRead'})
    Raises:
      ValueError -- [None]
    """

    if pathTag in self.appCfg.keys():
      initDir = self.appCfg[pathTag]
    else:
      initDir = self.appCfg['defaultPath']

    # Need to ensure initDir is a valid directory in case it has been
    # rename or delete or move.
    self.selUserDataFolder(initDir)
    initDir = self.userDataFolder

    diagOptions={} # Make sure we start with an empty dictionary
    diagOptions['title'] = self.filePrompt
    diagOptions['initialdir'] = initDir

    window = tkinter.Tk()
    window.wm_withdraw()
    #window.call('wm', 'attributes', '.', '-topmost', True)
    #window.lift()


    if pathType.lower() == 'fileread':
      diagOptions['filetypes'] = self.fileType
      if self.fileMultiSelect:
        self.currentPaths = fileDiag.askopenfilenames(**diagOptions)
        # save the current path in a list to be consistent/compatible
        self.currentPaths = list(self.currentPaths)
      else:
        # save the single path in a list directly to be consistent/compatible
        self.currentPaths = [fileDiag.askopenfilename(**diagOptions)]

    elif pathType.lower() == 'filewrite':
      diagOptions['filetypes'] = self.fileType
      # save the single path in a list directly to be consistent/compatible
      self.currentPaths = [fileDiag.asksaveasfilename(**diagOptions)]

    elif pathType.lower() == 'dirselect':
      # save the single path in a list directly to be consistent/compatible
      if self.fileMultiSelect:
        self.currentPaths = multiDirs(**diagOptions)
      else:
        self.currentPaths = [fileDiag.askdirectory(**diagOptions)]
    else:
      raise ValueError('Unsupported pathType input ', \
                       'method: pathSelect', \
                       ' class: userPath')
    # Make sure the user did NOT cancel and update the dictionary and
    # initialization file accordingly
    if any(map(len, self.currentPaths)):  # The user did NOT cancel,
                                          # so update accordingly
      self.numPaths = len(self.currentPaths)

      # find the base path of the file so it can be saved in the init file
      if pathType.lower() == 'dirselect': # For folder, keep the complete path
        self.appCfg[pathTag] = self.currentPaths[0]
      else: # For file, remove the file name
        self.appCfg[pathTag] = os.path.dirname(self.currentPaths[0])

    else: # User cancelled, simply default the numPath property
      self.numPaths = 0


  def userMsg(self, msg='Hello World'):
    window = tkinter.Tk()
    window.wm_withdraw()
    messagebox.showinfo('deepDSP', msg)


  def filePathsList(self, folderList, fileType='*.*'):
    """
      This method will retrieves the full path of all the files that matches the
      file type for all the folder listed.

      folderList => List of all the folder that will be query
      fileType => Desired file type

      The full file paths for all the files are saved in the "currentPaths"
      property of this class
    """
    # Make sure the current property is empty
    self.currentPaths = []
    for item in range(len(folderList)):
      tmp = glob.glob(folderList[item] + '/' + fileType)
      if len(tmp) == 0: # make sure the list is NOT empty
        print('No matching file found in => ' + folderList[item])
      else:
        self.currentPaths.extend(tmp)

    # Finally sort the list
    self.currentPaths.sort()
    # Update the associated property
    self.numPaths = len(self.currentPaths)


  def foldersList(self, basePath):
    """
      This method will retrieves the full path of all the folders located in the
      basePath.

      basePath => a path string the ENDS WITH a '/'

      The full sub-folder paths for all the folders are saved in the "currentPaths"
      property of this class
    """
    # Make sure the current property is empty
    # print(basePath)
    # print(type(basePath))
    if not basePath.endswith('/'):
      basePath = basePath + '/'
    self.currentPaths = glob.glob(basePath + '*/')

    # Finally sort the list
    self.currentPaths.sort()
    # Update the associated property
    self.numPaths = len(self.currentPaths)
    # Finally, make sure that they are properly build path string
    for iItem, pItem in enumerate(self.currentPaths):
      self.currentPaths[iItem] = os.path.normpath(pItem)


#======================================= Static Methods ===========================================#
def filePathsList(folderList, fileType='*.*'):
  """
    This method will retrieves the full path of all the files that matches the file type for all
    the folder listed.

    folderList => List of all the folder that will be query
    fileType => Desired file type

    The full file paths for all the files are returned
  """
  # Init local variable
  listPaths = []
  for item in range(len(folderList)):
    tmp = glob.glob(folderList[item] + '/' + fileType)
    if len(tmp) == 0: # make sure the list is NOT empty
      print('No matching file found in => ' + folderList[item])
    else:
      listPaths.extend(tmp)
  # Finally sort the list and return it
  return sorted(listPaths)
