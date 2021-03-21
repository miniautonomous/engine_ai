import numpy as np
import os
import sys
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.clock import Clock

# Custom module for miscellaneous utility classes to support a GUI.
from utils.guiUtils import userPath
from utils.numeric_functions import GeneralUtils

# Camera related imports
import pyrealsense2 as rs
import cv2

# Layout files for GUI sub-panels
Builder.load_file('kvSubPanels/camera.kv')
Builder.load_file('kvSubPanels/vehiclestatus.kv')
Builder.load_file('kvSubPanels/pwmsettings.kv')
Builder.load_file('kvSubPanels/powercontrols.kv')
Builder.load_file('kvSubPanels/filediag.kv')
Builder.load_file('kvSubPanels/statusbar.kv')


class EngineApp(App):
    def __init__(self):
        """
            App back end to drive the AI framework.

        """
        App.__init__(self)

        # Parameter initialization
        self.arduino_board = None
        self.rc_mode = None
        self.camera_real_rate = 0
        self.drive_loop_buffer_fps = None
        self.camera_buffer_fps = None
        self.car_name = "miniAutonomous"
        self.net_loaded = False
        self.functional_utils = GeneralUtils()

    def build(self):
        """
          This is the first method that Kivy calls to build the GUI.

          Please note:
           (i) User input for loading a file is tracked via 'file_IO' to keep a history of the prior use of the app
               and use those selections as the default selections for the current instance

          (ii) The main app class and the GUI class pass references of themselves to each other to facilitate
               exchange of parameters.

          (iii) The Kivy "build" method is used here instead of the standard __init__ to define the various
                class properties
        """
        self.title = 'EngineAppGUI (ver0.0r210303)'
        self.icon = 'img/logoTitleBarV2_32x32.png'
        self.file_IO = userPath('engineApp.py')                                                                         # noqa
        self.ui = EngineAppGUI(self)                                                                                    # noqa
        return self.ui

    def drive_loop(self, dt: float):                                                                                    # noqa
        """
          Main loop that drives the AI framework, from here forwards
          referred to as drive system. (Because that's how we roll.)
          
        Parameters
        ----------
        dt: (float) time step given at 1/dt
        """
        print('hello:'+str(dt))

        # Drive the car yourself

        # Have the AI drive the car

        # Log data for training

    def start_drive(self):
        """
            Turns on the drive system.
        """
        if self.root.powerCtrls.power.text == '[color=00ff00]Power ON[/color]':
            # Turn things OFF
            Clock.unschedule(self.drive_loop)
            self.root.powerCtrls.power.text = 'Power OFF'
        else:
            # Turn things ON
            Clock.schedule_interval(self.drive_loop, 1 / 40)
            self.root.powerCtrls.power.text = '[color=00ff00]Power ON[/color]'

    def select_file(self):
        """
            Help the user select the model HDF5 or the directory to which to store data.

        """
        self.file_IO.fileType = [('text files', ('.txt', '.text')), ('all files', '.*')]
        self.file_IO.pathSelect(pathTag='EngineAppGUI')
        if self.file_IO.numPaths == 0:
            # User cancelled the selection
            self.root.statusBar.lblStatusBar.text = ' User cancelled selection'
        else:
            # The user selected an HDF5 file
            self.root.statusBar.lblStatusBar.text = ' File loaded !'
            self.root.fileDiag.lblFilePath.text = self.file_IO.currentPaths[0]
            self.root.fileDiag.selectButton.text = 'Selected File'

    def start_camera(self):
        """
            Capture an image from a Intel Real Sense Camera
        """
        self.functional_utils.initTimer()
        frames = self.ui.rsPipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            self.ui.rsIntelOn = False

        self.ui.imgMain = np.asanyarray(color_frame.get_data())
        # Process the image to display to the user
        display_image = np.flipud(self.ui.imgMain)
        display_image = display_image[:, :, [2, 1, 0]]
        # Update the UI texture to display the image to the user
        self.ui.imgTexture.blit_buffer(display_image.reshape(self.ui.imgNumPixels *
                                                             self.ui.imgWidthFactor))
        self.ui.canvas.ask_update()  # This is required to have the image refreshed and it
        # refers to the canvas "camera.kv" file
        # Compute the camera actual frame rate
        dtFps = self.uiUtils.getTimer()
        if dtFps == 0:
            print('rsIntelDaq method: Imaged dropped')
            dtFps = 1 / 30  # default the FPS to 30 in case a value does NOT get read
        self.camBufferFPS, fpsAvg = self.functional_utils.moving_avg(self.camBufferFPS, 1 / dtFps)
        self.camRealRate = round(fpsAvg, 1)

    @staticmethod
    def start_arduino(self):
        print('hello')


class EngineAppGUI(GridLayout):
    # kivy texture instance to display images
    imgTexture = ObjectProperty()

    def __init__(self, main_app_ref):
        """
          Object constructor method used to initiate the UI window.

          This will instantiate the "root" Kivy property and the name used here MUST match exactly the Kivy
          class name used in the engine.kv main file.

          Also pass as parameter the App object reference so that any App property or methods can
          easily be accessed in this class directly if needed.
        """
        # Instantiate the parent class
        GridLayout.__init__(self)

        # Property to access the App properties easily
        self.app = main_app_ref
        self.uiWindow = Window
        self.uiWindow.borderless = False

        # Display window for camera feed
        self.imgMain = []
        self.imgWidthFactor = 1
        self.imgNumPixes = None

        # Camera default
        self.rsPipeline = rs.pipeline()
        self.rsConfig = rs.config()

        # Canvases default background to light blue
        self.uiWindow.clear_color = ([.01, .2, .36, 1])
        self.uiWindow.bind(on_request_close=self.ui_close_window)

        # Window initialization based on last instance of app use
        win_tmp = self.app.file_IO.appsGetDflt('winTop')
        if win_tmp is not None:
            self.uiWindow.top = win_tmp
        win_tmp = self.app.file_IO.appsGetDflt('winLeft')
        if win_tmp is not None:
            self.uiWindow.left = win_tmp
        win_tmp = self.app.file_IO.appsGetDflt('winSize')
        if win_tmp is not None:
            self.uiWindow.size = win_tmp
        else:
            self.uiWindow.size = (1000, 500)

    def ui_close_window(self, _):
        """
          This method is used to do some clean up just before the window is closed.

          Callback method that is bind to the "on_request_close", i.e., last method executed before
          the window is actually closed.
        """
        # Save the current window position so that the next window re-opens at the same position and
        # size that the user last left it
        self.app.file_IO.appCfg['winTop'] = self.uiWindow.top
        self.app.file_IO.appCfg['winLeft'] = self.uiWindow.left
        self.app.file_IO.appCfg['winSize'] = self.uiWindow.size
        self.app.file_IO.appsWriteDfltVal()


if __name__ == "__main__":
    EngineApp().run()
