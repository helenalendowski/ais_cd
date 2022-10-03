from rtlsdr import *
#from pylab import *
#from matplotlib import *

sdr = RtlSdr()

# configure device
sdr.sample_rate = 2.048e6
sdr.center_freq = 162e6
sdr.freq_correction = 60
sdr.gain = 'auto'

samples = sdr.read_samples(256*1024)
sdr.close()

