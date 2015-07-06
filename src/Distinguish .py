# coding=utf-8
import numpy as np
import pylab as pl
import scipy.signal as signal
import wave,time, threading, os
import cPickle as pickle
import Queue, multiprocessing

#Overlap frmate depth
DEFAULT_OVERLAP = 16
#How many data in fft process 
DEFAULT_FFT_SIZE = 8192
#sub-fingerprint depth
FIN_BIT = 32


#######################################################
#    search function                                                                                                    
#######################################################
def find_match(sdata, fdata, window_size, framerate):
	confidence = 0
	next_section_begain = 0
	matched_time_point = []

	len_f  = len(fdata)
	len_sf = len(sdata)
	#interval of time 
	NO_OVERLAP_TIME = round(DEFAULT_FFT_SIZE/(float(framerate) * DEFAULT_OVERLAP),4)

	#Arithmetic sequence tolerance uplimit and down limit
	up_limit = NO_OVERLAP_TIME*window_size + 0.05
	dw_limit = NO_OVERLAP_TIME*window_size - 0.05

	for a in range(0, len_f/window_size):
		block_dis_buffer = []
		for b in range(next_section_begain, len_sf - window_size):
			#calculate the distant of each subfingerprint between two songs in a search-window
			D = (fdata[(a*window_size) : (a+1)*window_size]) ^ (sdata[b : b+window_size])
			#get distant of two search-windows
			block_dis_buffer.append(np.sum([hamming_weight(long(d)) for d in D]))

		#get the most similar block sequence
		min_seq = np.argmin(block_dis_buffer)

		#if the number of similar sub-fingerprint in this block is more than 70%, that is to say it is similar
		if block_dis_buffer[min_seq] < FIN_BIT*window_size*0.4:
			#get the similar time in source file
			matched_time_point.append((next_section_begain + min_seq + 1) * NO_OVERLAP_TIME)
			if window_size > 10:
				if a > 5:
					if (min_seq - min_seq0) > 0:
						next_section_begain = next_section_begain + min_seq
					else:
						next_section_begain = min_seq0
		min_seq0 = min_seq
	# print "matched time point:",matched_time_point

	#because the search window is cetain, so the match time also should have a certain distance
	for i in range(1, len(matched_time_point)):
		di = matched_time_point[i] - matched_time_point[i-1]
		if dw_limit <= di <= up_limit:
			confidence += 1

	return round(float(confidence)/((len_f/window_size)-1), 3)

def recognize(fdata,channels,framerate):
	if len(fdata) < 200:
		DEFAULT_SEARCH_WIN = 4
	else:
		DEFAULT_SEARCH_WIN = 32
	
	#load the fingerprint info of audio which saved in .pkl
	try:
		catalog_file = open('AudioFingerCatalog.pkl', 'rb')
		catalog_info = pickle.load(catalog_file)
	except EOFError:
		print "Error: No data saved in pkl file. please fisrtly save the fingerprint of the source audio."
		return 0

	match_audio = None
	max_confidence = 0
	
	#load the data
	if channels:
		source_data = open('AudioFingerDataC1.pkl','rb')
	else:
		source_data = open('AudioFingerDataC0.pkl','rb')

	for ID in catalog_info:
		confidence = find_match(pickle.load(source_data), fdata, DEFAULT_SEARCH_WIN, framerate)
		if confidence > max_confidence:
			match_audio = catalog_info[ID]
			max_confidence = confidence
	
	source_data.close()
	catalog_file.close()

	if match_audio == None:
		return "Not Found"
	else:
		return match_audio, max_confidence

###########################################################
#   Get audio fingerprint
###########################################################
def fft_transformation(data, band):
	#hanning window to smooth the edge
	xs = np.multiply(data, signal.hann(DEFAULT_FFT_SIZE, sym=0))
	#fft transfer
	xf = np.fft.rfft(xs)
	
	#200HZ ~ 2000HZ, 51 * 35Hz(size) , scale: 44100/16384 = 2.7
	xfp = (20*np.log10(np.clip(np.abs(xf), 1e-20, 1e100))[74:740])
	
	return [np.sum(np.abs(xfp[n*band : (n+1)*band])) for n in range(FIN_BIT+1)]

def get_finger(data,framerate):
	st = 0
	en = DEFAULT_FFT_SIZE
	length = len(data)
	band = int((1800/(FIN_BIT+1))/(framerate/DEFAULT_FFT_SIZE))
	fs= []
	while (length - en) > DEFAULT_FFT_SIZE:
		#frame size = DEFAULT_FFT_SIZE, one frame time: 0.37s
		fs.append(fft_transformation( data[st:en], band))
		st = st + DEFAULT_FFT_SIZE/DEFAULT_OVERLAP
		en = st + DEFAULT_FFT_SIZE
	
	fin = []
	for n in range(1,len(fs)):
		sub_fin = ""
		for m in range(FIN_BIT):
 			if fs[n][m] - fs[n][m+1] - (fs[n-1][m]-fs[n-1][m+1]) > 0:
 				sub_fin = sub_fin + "1"
 			else:
 				sub_fin = sub_fin + "0"
 		sub_fin = int(sub_fin,2)
 		fin.append(sub_fin)

 	del fs[:]
 	return np.array(fin, dtype=np.uint32)   
  
###########################################################
# save fingerprint and file information
# format {ID: filename}
###########################################################
def save_infomation(audio_name):
	#{ID: filename}
	try:
		catalog_file = open('AudioFingerCatalog.pkl', 'ab+')
		catalog_info = pickle.load(catalog_file)
	except EOFError:
		catalog_info = {}
	for ID in catalog_info:
		if catalog_info[ID] == audio_name: 
				print "File '%s' had been saved before." % audio_name
				return 0
	ID = len(catalog_info)
	catalog_file = open('AudioFingerCatalog.pkl', 'wb')
	catalog_info.update({ID : audio_name})
	pickle.dump(catalog_info, catalog_file)
	catalog_file.close()
	return 1


#AudioFingerDataC1.pkl save right channel(1), the AudioFingerDataC0.pkl save the left channel(0)
#format array()
def save_data(audio_name, fdata, channels):
	try:
		if channels:
			file = "AudioFingerDataC1.pkl"
		else:
			file = "AudioFingerDataC0.pkl"
		pkl_data = open(file, 'ab+')
		pickle.dump(fdata, pkl_data)
	finally:
		pkl_data.close()
	print "save Audio-Fingerprint Done"




def audio_analysis(filename, data, framerate,channels, re):
	print "Channel: %s"%channels
	#detect_broken_frame(data, channels)
	fingerprint = get_finger(data, framerate)
	
	save_data(filename, fingerprint, channels)

    
def audio(filename, re):
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
	if save_infomation(filename) == 0:
		print " "
		return 0
    
    
    
	#data
	wave_data = np.fromstring(str_data, dtype = np.short)
	wave_data.shape = -1,2
	wave_data = wave_data.T #transpose

   
	channel1 = multiprocessing.Process(target = audio_analysis, args = (filename, wave_data[0],framerate, 0, re ))
	channel1.start()
	channel2 = multiprocessing.Process(target = audio_analysis, args = (filename, wave_data[1],framerate, 1, re ))
	channel2.start()
	channel1.join()
	channel2.join()


	print "Finished time: %4f"%(time.time()-start)



  


  
if __name__ == "__main__":
	current_directory = os.path.dirname(os.path.abspath(__file__))    
	main_path = os.path.dirname(current_directory)
	main_path = main_path.replace('\\','/')
	
	dir_audio1 = main_path + '/sample/23.wav'
	print dir_audio1

	audio(dir_audio1,0)
   