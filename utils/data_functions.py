import numpy as np
import time


class GeneralUtils:
    def __init__(self):
        " Miscellaneous numeric utilities used in various parts of the code."
        self.timer_start = 0
        self.measure_time = 0
        self.mean_avg_buffer = []
        self.mean_avg_length = 0
        self.circular_buffer_length = 0
        self.circular_index = 0

    def initiate_time(self):
        self.timer_start = time.time()

    def get_timer(self):
        return time.time() - self.timer_start

    def create_circular_buffer(self, buffer_length: int, buffer_shape: tuple):
        """
            This method creates a circular buffer for RGB images, i.e., 3D data (width, height,
          channels).  It can be use for the image sequencing for reccurent DNN architectures.
          It uses a "main" buffer that is 2*bufSize and a slicing to get the correct values.

        Parameters
        ----------
        buffer_length: (int) buffer length
        buffer_shape: (tuple) shape of buffer
        """
        self.circBufLength = buffer_length
        # Create a buffer
        self.circBuffer = np.zeros((int(2 * self.circBufLength),
                                    int(buffer_shape[0]),
                                    int(buffer_shape[1]),
                                    int(buffer_shape[2])), np.uint8)
        self.circIndex = 0  # Make sure to reset the index

    def get_buffer(self, newData):
        """
          This method adds the new data to the main circBuffer, then does the slicing to
          return the desired sequence.  This acts as a RIGHT-to-LEFT FIFO buffe

        Parameters
        ----------
        newData

        Returns
        -------

        """
        tmpIdx = (self.circular_index % self.circular_buffer_length)
        self.circBuffer[tmpIdx, :, :, :] = newData
        self.circBuffer[tmpIdx + self.circular_buffer_length, :, :, :] = newData
        self.circular_index += 1
        return self.circBuffer[tmpIdx + 1:tmpIdx + 1 + self.circular_buffer_length, :, :, :]

    @staticmethod
    def moving_avg(avg_buffer: np.array, new_value: float):
        """
            Creates a moving average; used to give a stable value for things like
            drive loop and camera frame-rate estimation.

        Parameters
        ----------
        avg_buffer: (np.array) array of discrete rolling values
        new_value: (int) current onetime value to be included in rolling values array

        Returns
        -------
        avg_buffer: (np.array) array of discrete rolling values wiht new value included
        new_value: (flooat) mean value of current array
        """
        avg_buffer = np.insert(np.roll(avg_buffer, 1)[1:], 0, new_value)
        return avg_buffer, np.mean(avg_buffer)

    @staticmethod
    def map_function(input_value: int, map_ranges: list) -> int:
        """
          This methods takes an "inputVal" and returns the mapped value between the
          new range.  The mapRanges is a list of 4 values.

        Parameters
        ----------
        input_value: (int) actual PWM value
        map_ranges:
          mapRanges[0] => The minimum value of the "inputVal" range
          mapRanges[1] => The maximum value of the "inputVal" range
          mapRanges[2] => The minimum value of the mapped range
          mapRanges[3] => The maximum value of the mapped range

        Returns
        -------
        scaled_value = (int) resulting normalized value of the PWM
        """
        return ((input_value - map_ranges[0]) / (map_ranges[1] - map_ranges[0]) *
                (map_ranges[3] - map_ranges[2]) + map_ranges[2])

    @staticmethod
    def chop_value(input_value: int, min_value:int, max_value:int):
        """

        Parameters
        ----------
        input_value: (int) raw input value
        min_value: (int) defined minimum value
        max_value: (int) defined maximum value

        Returns
        -------
        input_value: (int) chopped value between min and max if input exceeds range
        """
        if input_value < min_value:
            input_value = min_value
        elif input_value > max_value:
            input_value = max_value
        return input_value
