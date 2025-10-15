# 2025.10.13  pip install pandas,  python -m spacy download en_core_web_sm  ,  python -m spacy download zh_core_web_sm 
import requests,os,fire # fire>=0.7.1  wget>=3.2
host	= 'file.yulk.net'
root	= os.path.dirname(os.path.abspath(__file__)) #D:\cikuu\mod\yulk

def download_with_wget(url, local_filename):
	import wget
	try:
		if os.path.exists(local_filename):
			os.remove(local_filename)
		print ("Start to download: ",  url , flush=True) 
		wget.download(url, local_filename)
		print(f"\nDone: {local_filename}")
	except Exception as e:
		print(f"\nFailed: {e}", url, local_filename)

# python __main__.py par lemword
par		= lambda name : download_with_wget(f"http://{host}/yulk/par/{name}.parquet", root +f"/par/{name}.parquet")
park	= lambda name : download_with_wget(f"http://{host}/yulk/park/{name}.parquet", root +f"/park/{name}.parquet")
parkv	= lambda name : download_with_wget(f"http://{host}/yulk/parkv/{name}.parquet", root +f"/parkv/{name}.parquet")
en		= lambda name : download_with_wget(f"http://{host}/yulk/en/{name}.parquet", root +f"/en/{name}.parquet") # support 'all' 
cn		= lambda name : download_with_wget(f"http://{host}/yulk/cn/{name}.parquet", root +f"/cn/{name}.parquet")
pycode	= lambda name : download_with_wget(f"http://{host}/yulk/pycode/{name}.py", root +f"/pycode/{name}.py")
sql		= lambda name : download_with_wget(f"http://{host}/yulk/sql/{name}.sql", root +f"/sql/{name}.sql")
walk	= lambda : download_with_wget(f"http://{host}/yulk/walk.py", root +f"/walk.py")
init	= lambda : download_with_wget(f"http://{host}/yulk/__init__.py", root +f"/__init__.py")
main	= lambda : download_with_wget(f"http://{host}/yulk/__main__.py", root +f"/__main__.py")
duckinit= lambda : download_with_wget(f"http://{host}/yulk/duckinit.py", root +f"/duckinit.py")

def update(name='filelist.txt'): # python -m yulk update
	for line in requests.get(f"http://{host}/yulk/{name}").text.strip().split('\n'):  # pycode/init.py
		try:
			line = line.strip()
			if not line: continue 
			print (line, flush=True)
			download_with_wget(f"http://{host}/yulk/{line}", root + f"/yulk/{line}")
		except Exception as e:
			print(f"\nFailed: {e}", line, root)

if __name__ == "__main__": 	
	fire.Fire()
