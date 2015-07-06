# -*- coding: utf-8 -*-

import pylab as pl
import numpy as np
import wave,time,threading, os
import multiprocessing

def detect_broken_frame(data, channel):
	FLAG = 0
	DETECT_WIN = 512
	VAR_THRESHOLD = 1000

	for i in range(len(data)/DETECT_WIN):
		var = int(np.var(data[i*DETECT_WIN:(i+1)*DETECT_WIN]))         #?????
		if i != 0:
			distance = abs(var - var0)
			#print "distance %10d"%distance," %10d"%var," time",((i+1)*DETECT_WIN)/float(44100)
			if FLAG == 0:
				if (distance > VAR_THRESHOLD) and (var < 90) :
					FLAG = 1
			elif FLAG == 1:
				if (distance > VAR_THRESHOLD) and (var0 < 90):
					FLAG = 0
					print "+--------------- "
					print "| Channel: %s"%channel, "," , "detect a broken frame in time ",((i+1) * DETECT_WIN)/float(44100)
					print "+--------------- "
		var0 = var

        
def audio(filename):
	start = time.time()
	#open wav file
	wf = wave.open(filename, 'rb')
	#get the information from the file
	params = wf.getparams()
	nchannels, sampwidth, framerate, nframes = params[:4]
	#get data
	str_data = wf.readframes(nframes)
	wf.close()

	filename = os.path.basename(filename)
	print filename

	#data
	wave_data = np.fromstring(str_data, dtype = np.short)
	wave_data.shape = -1,2
	wave_data = wave_data.T #transpose
	time1 = np.arange(0, nframes) * (1.0 / framerate)
    
    
    
    # »æÖÆ²¨ÐÎ
	pl.subplot(211) 
	pl.plot(time1, wave_data[0])
	pl.subplot(212) 
	pl.plot(time1, wave_data[1], c="g")
	pl.xlabel("time (seconds)")
	pl.show()
	print " "
    
    
    
	channel1 = multiprocessing.Process(target = detect_broken_frame, args = (wave_data[0],0,))
	channel1.start()
	channel2 = multiprocessing.Process(target = detect_broken_frame, args = (wave_data[1],1,))
	channel2.start()
	channel1.join()
	channel2.join()

	print "Finished time: %4f"%(time.time()-start)



  


  
if __name__ == "__main__":
	current_directory = os.path.dirname(os.path.abspath(__file__))    
	main_path = os.path.dirname(current_directory)
	main_path = main_path.replace('\\','/')
	
	dir_audio = main_path + '/sample/23.wav'
	print dir_audio

	audio(dir_audio)
   