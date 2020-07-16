##############################################################################
from multiprocessing import Process
import subprocess
import hashlib
import random
import glob
import time
import math
import sys
import os

# capture start time for stats
start = time.time()

MAXPROCESSES = 4

def worker(fuzzfiledata: bytearray, fuzzcase: int):
	# make sure our data is what we expect
	assert isinstance(fuzzfiledata, bytearray)
	assert isinstance(fuzzcase, int)

	# make random changes to the data
	fuzzdatalen = len(fuzzfiledata)
	endIndex = random.randint(1, fuzzdatalen-1)
	startIndex = random.randint(0, endIndex)
	for i in range(startIndex, endIndex):
		fuzzfiledata[i] = random.randint(0, 255)

	# write out the modified file to disk
	fuzzfile = "tmpfuzzfile{}".format(fuzzcase)
	with open(fuzzfile, "wb+") as f:
		f.write(fuzzfiledata)

	# start a process running the mutated file
	completedProc = subprocess.run(["./objdump", "-x", fuzzfile], \
		stdout=subprocess.DEVNULL, \
		stderr=subprocess.DEVNULL)

	# log the end time for stats
	elapsed = time.time() - start

	# print out stats
	fcps = float(fuzzcase)/elapsed
	print(f"[{elapsed:10.4f}] | Case {fuzzcase:10d} | Retcode {completedProc.returncode} | fcps {fcps:10.4f}")

	# log the crash if we get a SIGSEV
	if completedProc.returncode == -11:
		crashFilename = ""
		crashFilename += "./crashes/"
		crashFilename += hashlib.md5(fuzzfiledata).hexdigest()
		with open(crashFilename, "wb+") as f:
			f.write(fuzzfiledata)

	# remove the file after we're done with it
	os.remove(fuzzfile)

def main():
	# load the corpus into ram
	# using a set to automatically reduce dupes
	corpusDir = b"./corpus/*"
	corpus = set()
	for filename in glob.glob(corpusDir):
		with open(filename, 'rb') as f:
			corpus.add(f.read())
	
	# converting corpus back into a list for easier access
	corpus = list(map(bytearray, corpus))

	# loop until keyboard interrupt running one fuzz case per loop
	fuzzcase = 0
	try:
		processes = []
		while True:
			# wait if we have maxed out our processes
			if len(processes) >= MAXPROCESSES:
				for process in processes:
					process.join()
					processes.remove(process)
			# continue when available
			else:
				# offload the fuzzing into another process
				cur_p = Process(target=worker, args=(corpus[random.randint(0, len(corpus)-1)], fuzzcase))
				
				# start our process
				cur_p.start()
				
				# increment our fuzz case
				fuzzcase += 1

				# add the current process into our lsit
				processes.append(cur_p)


	except KeyboardInterrupt:
		print("\r[*] Exiting...")


if __name__ == '__main__':
	if sys.version_info < (3, 0):
		raise NotImplementedError("This script requires Python3")
	main()