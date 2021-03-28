import numpy as np
import time


class GeneralUtils:
    def __init__(self):
        " Miscellaneous numeric utilities used in various parts of the code."
        self.timerStart = 0
        self.measTime = 0
        self.mAvgBuffer = []
        self.mAvgLength = 0
        # Circular buffer properties
        # self.circBuffer = []
        # self.circBufLength = 0
        # self.circIndex = 0

    def initiate_time(self):
        self.timerStart = time.time()

    def get_timer(self):
        return time.time() - self.timerStart

    @staticmethod
    def moving_avg(avg_buffer: np.array, new_value: int):
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
