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
        self.circBuffer = []
        self.circBufLength = 0
        self.circIndex = 0

    def initTimer(self):
        self.timerStart = time.time()

    def getTimer(self):
        return time.time() - self.timerStart

    @staticmethod
    def moving_avg(avg_buffer, new_value):
        avg_buffer = np.insert(np.roll(avg_buffer, 1)[1:], 0, new_value)
        return avg_buffer, np.mean(avg_buffer)
