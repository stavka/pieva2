#!/usr/bin/env python

import numpy
import pyaudio
import threading
from collections import deque

from bibliopixel.animation import BaseMatrixAnim
import bibliopixel.colors as colors
from bibliopixel.led import *

class Recorder:
    """Simple, cross-platform class to record from the microphone."""

    def __init__(self):
        """minimal garb is executed when class is loaded."""
        self.RATE=48000
        self.BUFFERSIZE=2048 #2048 is a good chunk size
        self.secToRecord=.1
        self.threadsDieNow=False
        self.newAudio=False
        self.maxVals = deque(maxlen=500)

    def setup(self):
        """initialize sound card."""
        #TODO - windows detection vs. alsa or something for linux
        #TODO - try/except for sound card selection/initiation

        self.buffersToRecord = 1

        self.p = pyaudio.PyAudio()
        self.inStream = self.p.open(format=pyaudio.paInt16,channels=1,rate=self.RATE,input=True, output=False,frames_per_buffer=self.BUFFERSIZE)

        self.audio=numpy.empty((self.buffersToRecord*self.BUFFERSIZE),dtype=numpy.int16)

    def close(self):
        """cleanly back out and release sound card."""
        self.p.close(self.inStream)

    ### RECORDING AUDIO ###

    def getAudio(self):
        """get a single buffer size worth of audio."""
        audioString=self.inStream.read(self.BUFFERSIZE)
        return numpy.fromstring(audioString,dtype=numpy.int16)

    def record(self,forever=True):
        """record secToRecord seconds of audio."""
        while True:
            if self.threadsDieNow: break
            for i in range(self.buffersToRecord):
                self.audio[i*self.BUFFERSIZE:(i+1)*self.BUFFERSIZE]=self.getAudio()
            self.newAudio=True
            if forever==False: break

    def continuousStart(self):
        """CALL THIS to start running forever."""
        self.t = threading.Thread(target=self.record)
        self.t.start()

    def continuousEnd(self):
        """shut down continuous recording."""
        self.threadsDieNow=True

    ### MATH ###
    def piff(self, val, chunk_size, sample_rate):
        '''Return the power array index corresponding to a particular frequency.'''
        return int(chunk_size * val / sample_rate)

    def calculate_levels(self, frequency_limits, outbars):
        '''Calculate frequency response for each channel defined in frequency_limits

        Initial FFT code inspired from the code posted here:
        http://www.raspberrypi.org/phpBB3/viewtopic.php?t=35838&p=454041

        Optimizations from work by Scott Driscoll:
        http://www.instructables.com/id/Raspberry-Pi-Spectrum-Analyzer-with-RGB-LED-Strip-/
        '''

        data = self.audio

        # if you take an FFT of a chunk of audio, the edges will look like
        # super high frequency cutoffs. Applying a window tapers the edges
        # of each end of the chunk down to zero.
        window = numpy.hanning(len(data))
        data = data * window

        # Apply FFT - real data
        fourier = numpy.fft.rfft(data)

        # Remove last element in array to make it the same size as chunk_size
        fourier = numpy.delete(fourier, len(fourier) - 1)

        # Calculate the power spectrum
        power = numpy.abs(fourier) ** 2

        matrix = numpy.zeros(outbars)
        for i in range(outbars):
            # take the log10 of the resulting sum to approximate how human ears perceive sound levels
            matrix[i] = numpy.log10(numpy.sum(power[self.piff(frequency_limits[i][0], self.BUFFERSIZE, self.RATE)
                                              :self.piff(frequency_limits[i][1], self.BUFFERSIZE, self.RATE):1]))

        return matrix

    def calculate_channel_frequency(self, min_frequency, max_frequency, width ):
        '''Calculate frequency values for each channel, taking into account custom settings.'''

        # How many channels do we need to calculate the frequency for
        channel_length = width

        print("Calculating frequencies for %d channels." % (channel_length))
        octaves = (numpy.log(max_frequency / min_frequency)) / numpy.log(2)
        octaves_per_channel = octaves / channel_length
        frequency_limits = []
        frequency_store = []

        frequency_limits.append(min_frequency)
        for i in range(1, width + 1):
            frequency_limits.append(frequency_limits[-1]
                                    * 10 ** (3 / (10 * (1 / octaves_per_channel))))
        for i in range(0, channel_length):
            frequency_store.append((frequency_limits[i], frequency_limits[i + 1]))
            print("channel %d is %6.2f to %6.2f " %( i, frequency_limits[i], frequency_limits[i + 1]))


        return frequency_store


class BaseEQAnim(BaseMatrixAnim):
    def __init__(self, led, minFrequency, maxFrequency, sensitivity):
        super(BaseEQAnim, self).__init__(led)
        self.rec = Recorder()
        self.rec.setup()
        self.rec.continuousStart()
        self.colors = [colors.hue_helper(y, self.height, 0) for y in range(self.height)]
        self.frequency_limits = self.rec.calculate_channel_frequency(minFrequency, maxFrequency, self.width)
        self.sensitivity = sensitivity

    def endRecord(self):
        self.rec.continuousEnd()


class EQ(BaseEQAnim):
    def step(self, amt = 1):
        self._led.all_off()
        eq_data = self.rec.calculate_levels(self.frequency_limits, self.width)
        for x in range(self.width):
            # normalize output
            height = (eq_data[x] - 10.2) / float(self.sensitivity)
            if height < .05:
                height = .05
            elif height > 1.0:
                height = 1.0

            numPix = int(round(height*(self.height+1)))

            for y in range(self.height):
                if y < int(numPix):
                    self._led.set(x, self.height - y - 1, self.colors[y])

        self._step += amt


class BassPulse(BaseEQAnim):
    def step(self, amt = 1):
        self._led.all_off()
        eq_data = self.rec.calculate_levels(self.frequency_limits, self.width)

        # only take bass values and draw circles with that value
        # normalize output
        height = (eq_data[0] - 9.0) / float(self.sensitivity)
        if height < .05:
            height = .05
        elif height > 1.0:
            height = 1.0

        numPix = int(round(height*(self.height/2)))

        for y in range(self.height):
            if y < int(numPix):
                self._led.drawCircle(self.width/2, self.height/2, y, self.colors[y*2])

        self._step += amt
