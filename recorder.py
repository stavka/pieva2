#!/usr/bin/env python

import numpy
import pyaudio
import alsaaudio
import threading
from collections import deque

from bibliopixel.animation import BaseMatrixAnim
import bibliopixel.colors as colors
from bibliopixel.led import *


class Recorder(object):
    def __init__(self):
        self.killRecording=False
        self.setup()

    def setup(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def getAudio(self):
        raise NotImplementedError()

    def normalize(self):
        raise NotImplementedError()

    def record(self):
        while True:
            if self.killRecording:
                break
            self.getAudio()

    def start(self):
        self.t = threading.Thread(target=self.record)
        self.t.start()

    def end(self):
        self.killRecording=True

    def piff(self, val, chunk_size, sample_rate):
        return int(chunk_size * val / sample_rate)

    def calculate_levels(self, frequency_limits, outbars):
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
            matrix[i] = numpy.log10(numpy.sum(power[self.piff(frequency_limits[i][0], self.buffersize, self.RATE)
                                              :self.piff(frequency_limits[i][1], self.buffersize, self.RATE):1]))

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


class AlsaRecorder(Recorder):
    RATE = 16000

    def setup(self):
        self.aa = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL)
        self.aa.setchannels(1)
        if self.aa.setrate(self.RATE) != self.RATE:
            raise Exception("Could not set rate to %s" % self.RATE)
        self.buffersize = self.aa.setperiodsize(341)

        self.audio = numpy.empty((self.buffersize), dtype=numpy.int16)

    def close(self):
        self.aa.close()

    def getAudio(self):
        l, data = self.aa.read()
        if l:
            self.audio = numpy.fromstring(data, dtype=numpy.int16)

    def normalize(self, value, sensitivity):
        return (value - 2) / float(sensitivity * 5)


class PyAudioRecorder(Recorder):
    RATE = 48000

    def setup(self):
        self.buffersize=2048
        self.p = pyaudio.PyAudio()
        self.inStream = self.p.open(format=pyaudio.paInt16,channels=1,rate=self.RATE,input=True, output=False,frames_per_buffer=self.buffersize)

        self.audio=numpy.empty((self.buffersize),dtype=numpy.int16)

    def close(self):
        self.p.close(self.inStream)

    def getAudio(self):
        try:
            audioString=self.inStream.read(self.buffersize)
            self.audio = numpy.fromstring(audioString,dtype=numpy.int16)
        except IOError as e:
            print "PyAudioRecorder getAudio() IOError: %s" % e

    def normalize(self, value, sensitivity):
        return (value - 10.2) / float(sensitivity)


class BaseEQAnim(BaseMatrixAnim):
    def __init__(self, recorder, led, minFrequency, maxFrequency, sensitivity):
        super(BaseEQAnim, self).__init__(led)
        self.rec = recorder
        self.rec.start()
        self.colors = [colors.hue_helper(y, self.height, 0) for y in range(self.height)]
        self.frequency_limits = self.rec.calculate_channel_frequency(minFrequency, maxFrequency, self.width)
        self.sensitivity = sensitivity

    def endRecord(self):
        self.rec.end()


class EQ(BaseEQAnim):
    def step(self, amt = 1):
        self._led.all_off()
        eq_data = self.rec.calculate_levels(self.frequency_limits, self.width)
        for x in range(self.width):
            # normalize output
            height = self.rec.normalize(eq_data[x], self.sensitivity)
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
        height = self.rec.normalize(eq_data[x], self.sensitivity)
        if height < .05:
            height = .05
        elif height > 1.0:
            height = 1.0

        numPix = int(round(height*(self.height/2)))

        for y in range(self.height):
            if y < int(numPix):
                self._led.drawCircle(self.width/2, self.height/2, y, self.colors[y*2])

        self._step += amt
