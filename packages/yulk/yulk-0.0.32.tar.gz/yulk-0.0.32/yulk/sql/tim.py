# 2025.10.15, profile 
import requests,os,math,itertools,importlib,hashlib,json,fileinput, duckdb, fire,time
loadfile	= lambda filename : ''.join(fileinput.input(files=(filename)))

def run(filename): 
	print ( 'started:', filename, flush=True)
	start = time.time()
	content = loadfile( filename)
	duckdb.execute(content)
	print( filename,  round(time.time() - start, 2), flush=True)

if __name__ == "__main__": 
	fire.Fire(run)

'''
d:\cikuu\mod\yulk\sql>python tim.py init.sql
started: init.sql
init.sql 15.88

d:\cikuu\mod\yulk\sql>python tim.py http.sql
started: http.sql
http.sql 0.37
'''