import os
import platform
import json
import glob
import tkinter
import tkinter.filedialog as file_dialog
import tkinter.messagebox as messagebox
from tkfilebrowser import askopendirnames as multi_directories


class UserPath(object):
    def __init__(self, app_module=None):
        """
          This class covers a bunch of generic file IO operations that the user generally
          needs for various GUI applications.

        Primary functions:

          1) Create and initialize an App initialization or configuration files where
             various default values (saved in a dictionary) are written to disk.
          2) Opens a file dialog to allow the user to select a file or folder.  At the same
             time, it is use to track which folder was last  used to read or write files or
             select a folder for a given 'pathTag'. The purpose of this tracking is to avoid for
             the user to manually browse back to a given location to re-select the next file or
             select the same file at a later time.
          3) Miscellaneous methods to get file and folder lists.

              NOTE: It is assumed here that an 'App' package base folder is one folder above
              this module location.  In other words, this module 'folder_functions.py' is located
              in a sub-folder of the 'App' package, e.g., utils.  This implies that
              the 'App' configuration files where various default values are saved using
              the 'app_config' property dictionary is also located in the base 'App' folder
              saved in the 'appFolder' property
        """
        # Set some properties here to make sure that they are attached to this instance
        self.current_paths = []
        self.num_paths = 0
        self.historical_paths = {}
        self.app_config = {}
        self.app_module = app_module
        self.app_config_file = None
        self.app_folder = None      # This is the base folder of the 'App'

        # Properties
        self.file_multi_select = False
        self.file_prompt = 'Please select a File:'
        self.file_type = [('all files', '.*')]
        # Default data folder path specified by the user
        self.user_data_folder = None
        # find the os type
        self.os_type = platform.system()

        if self.app_module is not None:
            """
            Create if needed the initialization file of this class/module that contains the
            dict 'app_config'. This 'app_config' dictionary keeps track of the last location
            that the user used. The following guarantees that the initialization file is
            available and has some default values.
            """
            # 1. Figure out the complete module path
            self.app_config_file = os.path.abspath(self.app_module)
            self.app_config_file, _ = os.path.splitext(self.app_config_file)
            # @TODO: Ask Francois about this line of code
            self.app_folder, _ = os.path.split(self.app_config_file)
            # @TODO: Removed the windows option here
            self.app_config_file += '_lnx.cfg'

             # 2. Actually create the 'App' configuration file if needed
            if not os.path.isfile(self.app_config_file):
                # Initialize the dictionary key associated with the default path
                self.app_config['defaultPath'] = os.path.expanduser('~')
                self.app_config['cfgFilePath'] = self.app_config_file
                # Save the dictionary to init file.
                with open(self.app_config_file, 'w') as tmpFile:
                    json.dump(self.app_config, tmpFile)
            else:
                # Simply read the file if it exist
                with open(self.app_config_file) as tmpFile:
                    self.app_config = json.load(tmpFile)

    def store_current_paths(self, key_name:str):
        """
            Adds a dictionary entry to the history property "histPaths" to save the
            object "currentPaths" property so it can be recalled later.

        Parameters
        ----------
        key_name: (str) key name used to save current_paths
        """
        self.historical_paths[key_name] = self.current_paths

    def apps_get_default(self, key_name:str):
        """
          Returns a dictionary entry if it exists.

        Parameters
        ----------
        key_name: (str) key name

        Returns
        -------
        key_value: (str) dictionary entry
        """
        if key_name in self.app_config.keys():
            key_value = self.app_config[key_name]
        else:
            key_value = None
        return key_value

    def write_default_value(self):
        """
          Saves the app_config property dictionary to a text file.
        """
        if self.app_module is not None:
            with open(self.app_config_file, 'w') as tmp_file:
                json.dump(self.app_config, tmp_file, sort_keys=True)

    @staticmethod
    def read_dictionary(dictionary_path):
        """
          Read the path to where the a config dictionary is stored.

        Parameters
        ----------
        dictionary_path: (str) path that leads to a previosly written config.

        Returns
        -------
        app_config: (dict) the stored config dictionary
        """
        if os.path.isfile(dictionary_path):
            # Simply read the file if it exist and return its content
            with open(dictionary_path) as tmpFile:
                return json.load(tmpFile)

    @staticmethod
    def file_paths_list(folder_list: list, file_type: str= '*.*') -> list:
        # @TODO: Discuss this with Francois
        """
            This method will retrieves the full path of all the files that matches the file type for all
            the folder listed.

        Parameters
        ----------
        folder_list: (list) lists all folders available with given file type
        file_type: (str) file type being searched for by user

        Returns
        -------
        list_paths: (list) current list of paths for given file type
        """
        list_paths = []
        for item in range(len(folder_list)):
            tmp = glob.glob(folder_list[item] + '/' + file_type)
            if len(tmp) == 0:
                print('No matching file found in => ' + folder_list[item])
            else:
                list_paths.extend(tmp)
        return sorted(list_paths)

    def select_user_data_folder(self, folder_path: str, action: str='validate', path_tag: str='default_path'):
        """
            This method saves a valid path to a user selected folder in the object property
            "user_data_folder".  At a minimum, it puts the user home folder path in that
            object property.

        Parameters
        ----------
        folder_path: (str) path to folder to save
        action: (str) type of action requested by user (options are 'validate', 'confirm' and 'select'
        path_tag: (str) tag to label path with

        Returns
        -------
        """
        if folder_path is None:
            folder_path = ''

        # Ensure a specified folder path exists, if not, return user's home directory
        if action.lower() == 'validate':
            if not os.path.isdir(folder_path):
                self.user_data_folder = os.path.expanduser('~')
            else:
                self.user_data_folder = folder_path

        # Confirm a folder is available, if not query the user to confirm which folder to use
        elif action.lower() == 'confirm':
            if  not os.path.isdir(folder_path):
                self.pathSelect(path_tag, 'dirSelect')
                if self.num_paths is not 0:
                    self.user_data_folder = self.current_paths[0]
                else:
                    self.user_data_folder = os.path.expanduser('~')
            else:
                self.user_data_folder = folder_path

        # Open the file dialog (which will save the path in the object property).
        elif action.lower() == 'select':
            self.pathSelect(path_tag, 'dirSelect')
            if self.num_paths is not 0:
                self.user_data_folder = self.current_paths[0]
            else:
                self.user_data_folder = os.path.expanduser('~') # Return the user home folder

        # Unsupported action
        else:
            self.user_data_folder = None
            raise ValueError('Unsupported "action" input ', \
                   'method: select_user_data_folder ', \
                   'class: UserPath')


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

    if pathTag in self.app_config.keys():
      initDir = self.app_config[pathTag]
    else:
      initDir = self.app_config['defaultPath']

    # Need to ensure initDir is a valid directory in case it has been
    # rename or delete or move.
    self.select_user_data_folder(initDir)
    initDir = self.user_data_folder

    diagOptions={} # Make sure we start with an empty dictionary
    diagOptions['title'] = self.file_prompt
    diagOptions['initialdir'] = initDir

    window = tkinter.Tk()
    window.wm_withdraw()
    #window.call('wm', 'attributes', '.', '-topmost', True)
    #window.lift()


    if pathType.lower() == 'fileread':
      diagOptions['filetypes'] = self.file_type
      if self.file_multi_select:
        self.current_paths = file_dialog.askopenfilenames(**diagOptions)
        # save the current path in a list to be consistent/compatible
        self.current_paths = list(self.current_paths)
      else:
        # save the single path in a list directly to be consistent/compatible
        self.current_paths = [file_dialog.askopenfilename(**diagOptions)]

    elif pathType.lower() == 'filewrite':
      diagOptions['filetypes'] = self.file_type
      # save the single path in a list directly to be consistent/compatible
      self.current_paths = [file_dialog.asksaveasfilename(**diagOptions)]

    elif pathType.lower() == 'dirselect':
      # save the single path in a list directly to be consistent/compatible
      if self.file_multi_select:
        self.current_paths = multi_directories(**diagOptions)
      else:
        self.current_paths = [file_dialog.askdirectory(**diagOptions)]
    else:
      raise ValueError('Unsupported pathType input ', \
                       'method: pathSelect', \
                       ' class: userPath')
    # Make sure the user did NOT cancel and update the dictionary and
    # initialization file accordingly
    if any(map(len, self.current_paths)):  # The user did NOT cancel,
                                          # so update accordingly
      self.num_paths = len(self.current_paths)

      # find the base path of the file so it can be saved in the init file
      if pathType.lower() == 'dirselect': # For folder, keep the complete path
        self.app_config[pathTag] = self.current_paths[0]
      else: # For file, remove the file name
        self.app_config[pathTag] = os.path.dirname(self.current_paths[0])

    else: # User cancelled, simply default the numPath property
      self.num_paths = 0

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
    self.current_paths = []
    for item in range(len(folderList)):
      tmp = glob.glob(folderList[item] + '/' + fileType)
      if len(tmp) == 0: # make sure the list is NOT empty
        print('No matching file found in => ' + folderList[item])
      else:
        self.current_paths.extend(tmp)

    # Finally sort the list
    self.current_paths.sort()
    # Update the associated property
    self.num_paths = len(self.current_paths)


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
    self.current_paths = glob.glob(basePath + '*/')

    # Finally sort the list
    self.current_paths.sort()
    # Update the associated property
    self.num_paths = len(self.current_paths)
    # Finally, make sure that they are properly build path string
    for iItem, pItem in enumerate(self.current_paths):
      self.current_paths[iItem] = os.path.normpath(pItem)
