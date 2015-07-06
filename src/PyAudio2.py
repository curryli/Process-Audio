# -*- coding: utf-8 -*-
import pyaudio
import wave

chunk = 1024

wf = wave.open(r"d:\10.wav", 'rb')

p = pyaudio.PyAudio()

# 打开声音输出流
stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                channels = wf.getnchannels(),
                rate = wf.getframerate(),
                output = True)

NUM = int(wf.getframerate()/chunk * 15)

# 写声音输出流进行播放
while NUM:
    data = wf.readframes(chunk)
    if data == "": break
    stream.write(data)
    NUM -= 1

stream.close()
p.terminate()