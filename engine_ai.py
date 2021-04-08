import numpy as np
import tensorflow.keras as keras
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2

# Custom module for miscellaneous utility classes to support a GUI.
from utils.folder_functions import UserPath
from utils.write_hdf5 import StreamToHDF5
from utils.data_functions import DataUtils
from arduino.pyArduino import Arduino

# Camera related imports
import pyrealsense2 as rs

# Servo Pin Numbers
STEERING_SERVO = 9
THROTTLE_SERVO = 10

# Layout files for GUI sub-panels
Builder.load_file('kvSubPanels/camctrls.kv')
Builder.load_file('kvSubPanels/vehiclestatus.kv')
Builder.load_file('kvSubPanels/pwmsettings.kv')
Builder.load_file('kvSubPanels/powercontrols.kv')
Builder.load_file('kvSubPanels/filediag.kv')
Builder.load_file('kvSubPanels/statusbar.kv')

"""
    Todo List:
    1) Figure out the message to the display part.

"""


class EngineApp(App):
    def __init__(self):
        """
            AI framework that defines the drive system.

            Please study the 'drive_loop' method first to determine
            how the primary systems are interconnected.

        """
        App.__init__(self)

        # Parameters
        self.rc_mode = None
        self.drive_loop_buffer_fps = None
        self.camera_buffer_fps = None
        self.arduino_board = None
        self.file_IO = None
        self.stream_to_file = None
        self.model = None
        self.image_buffer = None
        self.car_name = "miniAutonomous"
        self.data_utils = DataUtils()
        self.camera_real_rate = 0
        self.nn_image_width = 0
        self.nn_image_height = 0
        self.sequence_length = 0

        # RealSense camera pipeline
        self.rs_pipeline = rs.pipeline()
        self.rs_config = rs.config()

        # Arduino connected?
        self.board_available = False
        # Camera on?
        self.rs_is_on = False
        # Are we recording?
        self.record_on = False
        # Net loaded?
        self.net_loaded = False
        # Log folder selected?
        self.log_folder_selected = False
        # Was the car previously recording data
        self.previously_recording = False
        # Is the car speaking to you?
        # Just checking that you are reading the comments...

        # Set a variety of default values
        self._set_defaults()

    def _set_defaults(self):
        """
            Set default values for various numeric parameters.

        """
        # Set camera related defaults
        self.rs_frame_rate = 60
        # Set the desired rate of the drive loop
        self.drive_loop_rate = 40
        # Number of channels of input image
        self.color_depth = 3
        # Length of buffer reel (i.e. how many values are used in moving avg)
        self.moving_avg_length = 100
        # NN input parameters
        self.nn_image_width = 160
        self.nn_image_height = 120
        # For RNNs, define the sequence length
        self.sequence_length = 5

        # Creation of buffer arrays
        """
            These two buffers help provide a moving average of the frame rate
            at which the overall framework operates, (input image -> inference -> output command),
            and that at which the camera is operating, (basic FPS of camera). 
            These are important to determine if the vehicles drive system is operating
            at an optimal rate, which should be close to realtime, (~30 fps).
        """
        self.drive_loop_buffer_fps = np.full(self.moving_avg_length,
                                             1 * int(self.rs_frame_rate))
        self.camera_buffer_fps = np.full(self.moving_avg_length,
                                         1 * int(self.rs_frame_rate))

    def build(self):
        """
          This is the first method that Kivy calls to build the GUI.

          Please note:
           (i) User input for loading a file is tracked via 'file_IO' to keep a history
               of the prior use of the app and use those selections as the default
               selections for the current instance

          (ii) The main app class and the GUI class pass references of themselves to each
               other to facilitate exchange of parameters.
        """
        self.title = 'EngineAppGUI (ver0.0r210303)'
        self.icon = 'img/logoTitleBarV2_32x32.png'
        self.file_IO = UserPath('EngineApp.py')
        self.ui = EngineAppGUI(self)                                                                                    # noqa

        # Stream file object to record data
        self.stream_to_file = StreamToHDF5(self.nn_image_width,
                                           self.nn_image_height,
                                           self.ui.steering_max,
                                           self.ui.steering_min,
                                           self.ui.throttle_neutral,
                                           self.ui.throttle_max,
                                           self.ui.throttle_min)
        return self.ui

    def drive_loop(self, dt: int):
        """
          Main loop that drives the AI framework, from here forwards
          referred to as drive system. (Because that's how we roll.)

          This is the most critical method of the App class and should
          be the first lines of code studied if you wish to get a firm
          grip on the code base.
          
        Parameters
        ----------
        dt: (int) time step given at 1/dt
        """
        self.drive_loop_buffer_fps, fp_avg =\
            self.data_utils.moving_avg(self.drive_loop_buffer_fps, 1 / dt)

        # Create a message stream to inform the user of current status/performance
        self.root.vehStatus.loopFps.text = f'Primary Loop (FPS): {fp_avg:3.0f}'

        # Run the camera
        self.run_camera()

        # Display camera fps
        self.root.vehStatus.camFps.text = f'Camera Loop (FPS): {self.camera_real_rate:3.0f}'
        """
            Now that the camera is running, the image it produces is available
            to all methods via 'self.ui.primary_image'.
             
            This indicates we are using the same image to record or run inference
            on that the user sees from the UI.
        """

        # Check the desired mode
        """
            We are using the four channel options (TQi4ch)
        """
        mode_pwm = self.arduino_board.modeIn()
        # Set the vehicle to manual or autonomous
        if mode_pwm < 1500:
            drive_mode = 'Manual'
        else:
            drive_mode = 'Autonomous'
        # Display mode
        ui_messages = f', Mode: {drive_mode}={mode_pwm:3.0f}'

        # Are we recording?
        """
            NOTE: Here we are using a four channel transmitter/receiver,
            so the option to record from the camera has been separated from
            the drive mode. You can therefore record to create training
            data, (manual driving), or you can record to show the vehicle
            driving itself from the perspective of the vehicle.
        """
        record_pwm = self.arduino_board.recIn()
        if record_pwm < 1500:
            self.record_on = False
        else:
            self.record_on = True
        # Display record option
        ui_messages += f', Record Mode: {self.record_on}={record_pwm:3.0f}'

        # Drive the car
        if drive_mode == 'Manual':
            steering_output, throttle_output = self.drive_manual()
            ui_messages += f', Steering: {steering_output}, Throttle: {throttle_output}'
        # Or have the car drive itself
        else:
            # Check first if a network is loaded
            if self.net_loaded:
                steering_output, throttle_output = self.drive_autonomous()
                ui_messages += f', Steering: {steering_output}, Throttle: {throttle_output}'
            else:
                ui_messages = f'You need to load a network before driving autonomously!'
                steering_output, throttle_output = self.drive_manual()

        # Record data
        # @TODO: Set the width to 320, height 240... no resize here!
        if self.record_on and self.log_folder_selected:
            # Resize the image to be saved for training
            record_image = cv2.resize(self.ui.primary_image,
                                      (self.nn_image_width, self.nn_image_height))
            self.stream_to_file.log_queue.put((self.stream_to_file.frame_index,
                                               fp_avg,
                                               steering_output,
                                               throttle_output,
                                               record_image))
            self.stream_to_file.frame_index += 1
            # The vehicle is now recording
            self.previously_recording = True
        elif not self.record_on and self.previously_recording is True:
            # Close a file stream if one was open and the user requested it be closed
            self.stream_to_file.close_log_file()
            self.previously_recording = False

        # Send the message stream to the UI
        self.root.statusBar.lblStatusBar.text = ui_messages

    def drive_manual(self):
        """
            Manual driving option.

        Returns
        -------
        steering_output: (int) desired steering output
        throttle_output: (int) desired throttle output
        """
        # Steering
        steering_output = self.arduino_board.steerIn()
        # Clip to range if required
        steering_output = self.data_utils.chop_value(steering_output,
                                                     self.ui.steering_min,
                                                     self.ui.steering_max)
        self.arduino_board.Servos.write(STEERING_SERVO, steering_output)

        # Throttle
        throttle_output = self.arduino_board.throttleIn()
        throttle_output = self.data_utils.chop_value(throttle_output,
                                                     self.ui.throttle_min,
                                                     self.ui.throttle_max)
        self.arduino_board.Servos.write(THROTTLE_SERVO, throttle_output)
        return steering_output, throttle_output

    def drive_autonomous(self):
        """
            Drive the vehicle by doing things autonomously.

        Returns
        -------
        steering_output: (int) inference-based steering output
        throttle_output: (int) inference-based throttle output
        """
        # Resize the image to be compatible with neural network
        new_image = cv2.resize(self.ui.primary_image, (self.nn_image_width, self.nn_image_height))

        # Add it to the circular buffer for RNN processing
        input_tensor = np.expand_dims(self.data_utils.get_buffer(new_image), axis=0)

        # Do inference on the buffer of images
        drive_inference = self.model.predict(input_tensor)[0]
        """
            Model produces inferences from -100 to 100 for steering and 0 to 100 for throttle,
            so we need to rescale these to the current PWM ranges.
        """
        rescaled_steering = self.data_utils.map_function(drive_inference[0],
                                                         [-100, 100,
                                                         self.ui.steering_min,
                                                         self.ui.steering_max])
        rescaled_throttle = self.data_utils.map_function(drive_inference[1],
                                                         [0, 100,
                                                         self.ui.throttle_min,
                                                         self.ui.throttle_max])
        return rescaled_steering, rescaled_throttle

    def start_drive(self):
        """
            Turns the drive system on and off.
        """
        # Turn things OFF
        if self.root.powerCtrls.power.text == '[color=00ff00]Power ON[/color]':
            # Set scheduling
            Clock.unschedule(self.drive_loop)
            self.root.powerCtrls.power.text = 'Power OFF'

            # Camera
            if self.rs_is_on:
                try:
                    self.rs_pipeline.stop()
                except ValueError:
                    pass

            # Arduino
            if self.board_available:
                self.stop_arduino()

            # Close the log file if you are recording
            if self.record_on and self.log_folder_selected:
                self.stream_to_file.close_log_file()

        # Turn things ON
        else:
            # Camera
            self.rs_config.enable_stream(rs.stream.color,
                                         self.ui.image_width,
                                         self.ui.image_height,
                                         rs.format.bgr8, int(self.rs_frame_rate))
            self.rs_pipeline.start(self.rs_config)

            # Get initial frame and confirm result
            frames = self.rs_pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                self.rs_is_on = False
            else:
                self.rs_is_on = True

            # Start the Arduino
            if not self.board_available:
                self.start_arduino()

            # Initiate a thread for writing to the a data file
            self.stream_to_file.initiate_stream()

            """
                NOTE: This is the call that kicks off the primary drive loop
                and schedules it at a desired (what user wants) but not actual
                (what user gets) frequency.
            """
            # Schedule and start the drive loop
            if self.rs_is_on and self.board_available:
                Clock.schedule_interval(self.drive_loop, 1 / self.drive_loop_rate)
                self.root.powerCtrls.power.text = '[color=00ff00]Power ON[/color]'

    def select_model_file(self):
        """
            Help the user select the model HDF5 or the directory to which to store data.

        """
        # Filter for HDF5 model files
        self.file_IO.file_type = [('hdf5 files', '.h5'), ('all files', '.*')]
        self.file_IO.path_select(path_tag='EngineAppGUI')
        if self.file_IO.num_paths == 0:
            # User cancelled the selection
            self.root.statusBar.lblStatusBar.text = ' User cancelled selection'
        else:
            # The user selected an HDF5 file
            self.root.statusBar.lblStatusBar.text = ' File loaded !'
            # @TODO is currentPaths[0] the correct path to the DNN?
            self.root.fileDiag.lblDnnPath.text = self.file_IO.current_paths[0]
            self.root.fileDiag.selectDNN.text = 'Selected File'
            self.net_loaded = True

            # Load the network model now that it has been selected
            self.load_dnn()

    def load_dnn(self):
        """
            Load the Keras DNN model

        """
        try:
            self.model = keras.models.load_model(self.file_IO.current_paths[0])
            self.model.summary()

            # Define the network input image dimensions from the model's input tensor
            self.sequence_length = self.model.input.shape[1]
            self.nn_image_height = self.model.input.shape[2]
            self.nn_image_width = self.model.input.shape[3]

            # Create circular buffer for RNN network feed
            self.image_buffer = \
                self.data_utils.create_circular_buffer(self.sequence_length,
                                                       (self.nn_image_height,
                                                        self.nn_image_width,
                                                        self.color_depth))

        except ValueError:
            print('Selected file is not compatible with Keras load.')

    def select_log_folder(self):
        """"
            Select the folder to save log files to when creating training data.

        """
        self.stream_to_file.select_user_data_folder(self.stream_to_file.user_data_folder, 'select',
                                                    'miniCarData')
        self.ui.fileDiag.lblLogFolderPath.text = '  ' + self.stream_to_file.user_data_folder
        self.log_folder_selected = True

    def run_camera(self):
        """
            Capture an image from a Intel Real Sense Camera
        """
        self.data_utils.initiate_time()
        # Process a frame
        frames = self.rs_pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            self.rs_is_on = False

        # Take the image and make it visible in the UI and accessible to all methods
        self.ui.primary_image = np.asanyarray(color_frame.get_data())

        # Process it for display
        display_image = np.flipud(self.ui.primary_image)
        display_image = display_image[:, :, [2, 1, 0]]
        # Update the UI texture to display the image to the user
        self.ui.image_texture.blit_buffer(display_image.reshape(self.ui.image_number_pixels *
                                                                self.ui.image_width_factor))
        """
            This next command is required ot have the image refreshed and it refers to the
            canvas "camctrls.kv" file found in kvSubPanels.
        """
        self.ui.canvas.ask_update()

        # Compute the camera actual frame rate
        delta_fps = self.data_utils.get_timer()
        if delta_fps == 0:
            print('rsIntelDaq method: Imaged dropped')
            # Default is set to 30 in case of a frame drop
            delta_fps = 1 / 30
        self.camera_buffer_fps, fps_avg = self.data_utils.moving_avg(self.camera_buffer_fps,
                                                                     1 / delta_fps)
        self.camera_real_rate = round(fps_avg, 1)

    def start_arduino(self):
        try:
            # Set the serial rate
            self.arduino_board = Arduino(115200)
            self.board_available = True
        except ValueError:
            print('Issues connecting with the Arduino Mega. Please check.')
            self.board_available = False
            self.arduino_board = None

        if self.board_available:
            self.arduino_board.Servos.attach(STEERING_SERVO,
                                             min=self.ui.steering_min,
                                             max=self.ui.steering_max)
            self.arduino_board.Servos.attach(THROTTLE_SERVO,
                                             min=self.ui.throttle_min,
                                             max=self.ui.throttle_max)

    def stop_arduino(self):
        if self.board_available:
            self.arduino_board.Servos.detach(STEERING_SERVO)
            self.arduino_board.Servos.detach(THROTTLE_SERVO)
            self.arduino_board.close()
            self.board_available = False


class EngineAppGUI(GridLayout):
    # kivy texture instance to display images
    image_texture = ObjectProperty()

    def __init__(self, main_app_ref):
        """
          Object constructor method used to initiate the UI window.

          This will instantiate the "root" Kivy property and the name used here MUST
          match exactly the Kivy class name used in the engine.kv main file.

          Also pass as parameter the App object reference so that any App property or
          methods can easily be accessed in this class directly if needed.
        """
        # Instantiate the parent class
        GridLayout.__init__(self)

        # Property to access the App properties easily
        self.app = main_app_ref
        self.ui_window = Window
        self.ui_window.borderless = False

        # Display window for camera feed
        self.primary_image = []
        self.image_width_factor = 1

        # Set VGA resolution for the camera output window
        self.image_width = 320
        self.image_height = 240

        # Steering PWM settings, (done here to display to the user)
        self.steering_neutral = 1452
        self.steering_min = 970
        self.steering_max = 1944

        # Throttle PWM settings
        self.throttle_neutral = 1520
        self.throttle_min = 500
        self.throttle_max = 2500

        # Canvases default background to light blue
        self.ui_window.clear_color = ([.01, .2, .36, 1])
        self.ui_window.bind(on_request_close=self.ui_close_window)

        # Window initialization based on last instance of app use
        win_tmp = self.app.file_IO.apps_get_default('winTop')
        if win_tmp is not None:
            self.ui_window.top = win_tmp
        win_tmp = self.app.file_IO.apps_get_default('winLeft')
        if win_tmp is not None:
            self.ui_window.left = win_tmp
        win_tmp = self.app.file_IO.apps_get_default('winSize')
        if win_tmp is not None:
            self.ui_window.size = win_tmp
        else:
            self.ui_window.size = (1000, 500)

        # Create the original texture to display the image when the software is started.
        self.image_texture = Texture.create(size=(self.image_width * self.image_width_factor,
                                                  self.image_height),
                                            colorfmt='rgb', bufferfmt='ubyte')
        self.image_number_pixels = self.image_width * self.image_height * self.app.color_depth

    def ui_close_window(self, _):
        """
          This method is used to do some clean up just before the window is closed.

          Callback method that is bind to the "on_request_close", i.e., last method executed before
          the window is actually closed.
        """
        # Save the current window position so that the next window re-opens at the same position and
        # size that the user last left it
        self.app.file_IO.app_config['winTop'] = self.ui_window.top
        self.app.file_IO.app_config['winLeft'] = self.ui_window.left
        self.app.file_IO.app_config['winSize'] = self.ui_window.size
        self.app.file_IO.write_default_value()


if __name__ == "__main__":
    EngineApp().run()
