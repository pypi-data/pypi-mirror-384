# 2025.10.15, profile 
import os,math,itertools,importlib,hashlib,json,fileinput, fire,time
loadfile	= lambda filename : ''.join(fileinput.input(files=(filename)))

def run(filename): 
	print ( 'started:', filename, flush=True)
	start = time.time()
	content = loadfile( filename)
	exec(content)
	print( filename,  round(time.time() - start, 2), flush=True)

if __name__ == "__main__": 
	fire.Fire(run)

'''

'''