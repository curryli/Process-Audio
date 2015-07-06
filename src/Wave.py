# -*- coding: utf-8 -*-
import wave
import pylab as pl
import numpy as np

# ��WAV�ĵ�
f = wave.open(r"d:\10.wav", "rb")

# ��ȡ��ʽ��Ϣ
# (nchannels, sampwidth, framerate, nframes, comptype, compname)
params = f.getparams()
nchannels, sampwidth, framerate, nframes = params[:4]

# ��ȡ��������
str_data = f.readframes(nframes)
f.close()

#����������ת��Ϊ����
wave_data = np.fromstring(str_data, dtype=np.short)
wave_data.shape = -1, 2
wave_data = wave_data.T
time = np.arange(0, nframes) * (1.0 / framerate)

print wave_data
print '\n'
print len(wave_data[1])

# ���Ʋ���
pl.subplot(211) 
pl.plot(time, wave_data[0])
pl.subplot(212) 
pl.plot(time, wave_data[1], c="g")
pl.xlabel("time (seconds)")
pl.show()