import threading
import queue
import h5py
import time
import os

from .folder_functions import UserPath


class StreamToHDF5(UserPath):
    def __init__(self,
                 image_width: int,
                 image_height: int,
                 steering_max: int,
                 steering_min: int,
                 throttle_neutral: int,
                 throttle_max: int,
                 throttle_min: int,
                 file_version_number: int=1.0,
                 f_name_suffix: str= '_'):
        """
          This class stream to disk "frames" (i.e., groups) of data sets using a queue.

        Parameters
        ----------
        image_width: (int) image width
        image_height: (int) image height
        steering_max: (int) steering max value
        steering_min: (int) steering min value
        throttle_neutral: (int) neutral throttle value
        throttle_max: (int) maximum throttle value
        throttle_min: (int) minimum throttle value
        file_version_number: (float) version of the file format
        f_name_suffix: (str) suffix of file name
        """
        UserPath.__init__(self, 'miniCar.py')
        # Make sure to have a valid value
        self.select_user_data_folder('', 'validate')

        # Set image dimensions for class usage
        self.image_width = image_width
        self.image_height = image_height

        # Set the current file version
        self.fileVersionNum = file_version_number

        # Suffix added at the end of the file name
        self.fNameSuffix = f_name_suffix

        # Set the steering attributes
        self.steerMax = steering_max
        self.steerMin = steering_min
        # Set the throttle attributes
        self.throttle_neutral = throttle_neutral
        self.throttle_max = throttle_max
        self.throttle_min = throttle_min

        # Set a lock for control of write function
        self.lock = threading.Lock()

        # Log file
        self.log_file = None

        # Do we have a thread actively running
        self.thread_running = False

        # Frame indexing within queue
        self.frame_index = 0
        # Create a queue for storing images and driver input
        self.log_queue = queue.Queue()

    def initiate_stream(self):
        """
            Initiate a thread to stream data to a file.
        """
        # Create a thread to do actual writing
        self.thread_write = threading.Thread(name='WriteHDF5',
                                             target=self.write_queue_threading, args=( ))
        self.thread_write.setDaemon(True)
        self.thread_write.start()
        self.thread_running = True

    def write_queue_threading(self):
        """
            Threaded method that de-queue data and saves it to disk.
        """
        # Acquire a lock
        self.lock.acquire()
        print('We are about to start the threading!')
        # @TODO: Let's keep an eye on this threading stuff: might not work on Jetson
        try:
            while self.thread_running:
                # Get the current data frame from the queue
                log_data = self.log_queue.get()
                # Each frame of data is a separate group
                current_frame = str(log_data[0]).zfill(6)
                # Save every 20000 frames to a separate file
                if not (log_data[0]%20000) == 0:
                    self.write_data(current_frame,  log_data)
                # Create a new file
                else:
                    self.create_new_file()
                    # Write the first frame of the new log file
                    self.write_data(current_frame,  log_data)
        finally:
            # Release the lock
            self.lock.release()
            print('Threading has been stopped')

    def create_new_file(self):
        """
            Method that creates a new HDF5 logging file where miniCar
            data and saved to disk.
        """
        # Create name string for log file
        date = time.strftime('%y%m%d')
        clock = time.strftime('%H%M%S')
        descriptor = '_miniCar'
        file_path = os.path.join(self.user_data_folder, date + '_' + clock + descriptor + \
                                 self.fNameSuffix + '.hdf5')
        # Open up an HDF5 to store data
        self.log_file = h5py.File(file_path, 'w')
        # Set storage attributes
        if self.fileVersionNum == 1.0:
            # This version is for miniCar
            self.log_file.attrs['fileVersion'] = 'miniCarDataV1.0'
        elif self.fileVersionNum == 1.1:
            # This version is for miniCar
            self.log_file.attrs['fileVersion'] = 'miniCarDataV1.1'
        else:
            raise ValueError('Unknown HDF5 file version? ',
                             'method: create_new_file',
                             'class: streamToDiskHDF5')
        self.log_file.attrs['imgHeight'] = str(self.image_height)
        self.log_file.attrs['imgWidth'] = str(self.image_width)
        self.log_file.attrs['steerMax'] = str(self.steerMax)
        self.log_file.attrs['steerMin'] = str(self.steerMin)
        self.log_file.attrs['throttleMax'] = str(self.throttle_max)
        self.log_file.attrs['throttleMin'] = str(self.throttle_min)
        self.log_file.attrs['throttleNeutral'] = str(self.throttle_neutral)

    def write_data(self,  current_frame: int,  log_data: list):
        """
            Method that writes the de-queued "frame" data to an HDF5
            group in the file.

        Parameters
        ----------
        current_frame: (int) frame number that is being written
        log_data: (list) array of data being written to given group
        """
        frame_name = 'frame_'+ str(current_frame)
        self.log_file.create_group(frame_name)

        # Within each frame/group, each entry is it's own dataset
        self.log_file.create_dataset(frame_name+'/frame', data=log_data[0])
        self.log_file.create_dataset(frame_name+'/loop_frame_rate', data=log_data[1])
        self.log_file.create_dataset(frame_name+'/steering', data=log_data[2])
        self.log_file.create_dataset(frame_name+'/throttle', data=log_data[3])
        self.log_file.create_dataset(frame_name+'/image', data=log_data[4])

    def close_log_file(self):
        """
          Method that stops the threading and close the file.
        """
        self.thread_running = False
        self.log_file.close()
