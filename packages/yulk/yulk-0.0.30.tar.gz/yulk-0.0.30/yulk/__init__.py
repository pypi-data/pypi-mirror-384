# 2025.10.15
import requests,os,math,json,builtins,hashlib,duckdb,warnings,sys, traceback,fileinput
import pandas as pd
import marimo as mo
import altair as alt
import plotly.express as px
import matplotlib.pyplot as plt

builtins.duckdb = duckdb
builtins.pd		= pd
builtins.json	= json
builtins.os		= os
builtins.root	= os.path.dirname(os.path.abspath(__file__))  #if __file__ else  'd:/cikuu/mod/yulk'
builtins.requests = requests
builtins.mo		= mo
builtins.px		= px
builtins.plt	= plt
builtins.alt	= alt
warnings.filterwarnings("ignore")

loadfile	= lambda filename : ''.join(fileinput.input(files=(filename)))
sql			= lambda q: duckdb.sql(q).fetchdf()
parkv		= lambda name, k: ( res:=duckdb.sql(f'''select value from read_parquet('http://file.yulk.net/parkv/{name}.parquet') where key ='{k.replace("'","''")}' limit 1''').fetchone(), res[0] if res else None)[-1] if isinstance(k, str) else [ parkv(name,s) for s in k]
park		= lambda name, k: ( res:=duckdb.sql(f'''select exists (from read_parquet('http://file.yulk.net/park/{name}.parquet') where key ='{k.replace("'","''")}' limit 1)''').fetchone(), res[0] if res else None)[-1] if isinstance(k, str) else [ park(name,s) for s in k]
par			= lambda name, k: duckdb.sql(f'''from read_parquet('http://file.yulk.net/par/{name}.parquet') where key ='{k.replace("'","''")}' ''').fetchdf()
parlike		= lambda name, k: duckdb.sql(f'''from read_parquet('http://file.yulk.net/par/{name}.parquet') where key like '{k.replace("'","''")}%' ''').fetchdf()
wgettext	= lambda filename, **kwargs:	requests.get(f"http://{kwargs.get('host','file.yulk.net')}/{kwargs.get('folder','py')}/{filename}").text
wgetjson	= lambda filename, **kwargs:	requests.get(f"http://{kwargs.get('host','file.yulk.net')}/{kwargs.get('folder','json')}/{filename}").json()
jsongz		= lambda name:	json.loads(zlib.decompress(requests.get(f'http://file.yulk.net/json/{name}.json.gz').content, 16 + zlib.MAX_WBITS).decode('utf-8')) 

def cache(name): 
	if not hasattr(cache, name):  # wgetjson('stop.json') 
		dic = wgetjson(name) if '.' in name else jsongz(name)
		if name.endswith('set'): dic = set(dic)  # stopset, awlset 
		setattr(cache, name, dic)
	return getattr( cache, name)

def bncsum(): # assume: bnc function exists 
	if not hasattr(bncsum, 'sum'): bncsum.sum = bnc('_sum') 
	return bncsum.sum
logbnc	= lambda word, wordcnt, wordsum: likelihood(wordcnt, bnc(word), wordsum, bncsum()) # * tup, or a row 
bnckn	= lambda row:	likelihood( int(row[1]), bnc(str(row[0])), int(row[2]), bncsum()) # assuming first 3 columns is : (word, cnt, wordsum) , row is a tuple or list

if not hasattr(builtins, 'stopset') : 
	builtins.stopset	= lambda word:	word in cache('stopset') if isinstance(word, str) else [ stopset(w) for w in word] 
	builtins.awlset		= lambda word:	word in cache('awlset') if isinstance(word, str) else [ awlset(w) for w in word] 
	builtins.wordidf	= lambda word:	cache('wordidf').get(word, 0) if isinstance(word, str) else [ wordidf(w) for w in word]  # pandas.core.series.Series
	duckdb.create_function('stopset', stopset , [str], bool)
	duckdb.create_function('awlset', awlset , [str], bool)
	duckdb.create_function('wordidf', wordidf , [str], float)
	duckdb.create_function('logbnc', logbnc, [str,int,int], float)

	# first run, later can be overwrite macro
	for file in [file for _root, dirs, files in os.walk(f"{root}/sql",topdown=False) for file in files if file.endswith(".sql") and not file.startswith("_") ]:
		try:  #'util','yulkinit'
			duckdb.execute(loadfile(f'{root}/sql/{file}'))
		except Exception as e:
			print (">>Failed to loadsql:",e, file)
			exc_type, exc_value, exc_obj = sys.exc_info() 	
			traceback.print_tb(exc_obj)

	### walk, assuming 'root' exists in builtins
	for file in [file for _root, dirs, files in os.walk(f"{root}/park",topdown=False) for file in files if file.endswith(".parquet") and not file.startswith("_") ]:
		name = file.split('.')[0]  # wordlist
		setattr(builtins,name , lambda term, prefix=name: ( duckdb.sql(f"select exists (select * from '{root}/park/{prefix}.parquet' where key = '{term}' limit 1)").fetchone()[0] if not "'" in term else False) if isinstance(term, str) else [ duckdb.sql(f"select exists (select * from '{root}/park/{prefix}.parquet' where key = '{w}' limit 1)").fetchone()[0] for w in term])
		setattr(builtins,f"is{name}", getattr(builtins, name))  # isawl = awl 
		duckdb.sql(f"CREATE or replace MACRO {name}(w) AS ( select exists (select * from '{root}/park/{file}' where key = w limit 1) )")
		duckdb.sql(f"CREATE or replace view {name} AS ( from '{root}/park/{name}.parquet')")

	for file in [file for _root, dirs, files in os.walk(f"{root}/parkv",topdown=False) for file in files if file.endswith(".parquet") and not file.startswith("_") ]:
		name = file.split('.')[0]  # idf  
		f	 =  lambda term, prefix=name: (row[0] if not "'" in term and (row:=duckdb.sql(f"select value from '{root}/parkv/{prefix}.parquet' where key = '{term}' limit 1").fetchone()) else None ) if isinstance(term, str) else [ (row[0] if (row:=duckdb.sql(f"select value from '{root}/parkv/{prefix}.parquet' where key = '{w}' limit 1").fetchone()) else None ) for w in term]  # idf(['one','two']) 
		setattr(builtins,name , f)
		duckdb.sql(f"CREATE or replace MACRO {name}(w) AS ( select value from '{root}/parkv/{file}' where key = w limit 1 )")
		duckdb.sql(f"CREATE or replace view {name} AS ( from '{root}/parkv/{name}.parquet')")

	for file in [file for _root, dirs, files in os.walk(f"{root}/par",topdown=False) for file in files if file.endswith(".parquet") and not file.startswith("_") ]:
		name = file.split('.')[0]  # first column must be 'key' , ie: ce.parquet 
		duckdb.sql(f"CREATE or replace view {name} AS ( from '{root}/par/{file}' )")
		setattr(builtins,name ,	lambda term, prefix=name: duckdb.sql(f"select * from '{root}/par/{prefix}.parquet' where key = '{term}'").df() if not "'" in term else pd.DataFrame([]) )

	for cp in ('en','cn'): 
		duckdb.execute(f"create schema IF NOT EXISTS {cp}")
		setattr(builtins, cp, type(cp, (object,), {'name': cp}) ) # make 'en' as a new class, to attach new attrs later , such en.pos
		x = getattr(builtins, cp) # en.dobjvn('open') -> (label, cnt, keyness)  
		for rel in ('dobjnv','dobjvn','amodan','amodna','advmodvd','advmoddv','advmodad','advmodda','nsubjvn','nsubjnv','conjvv','lempos'): 
			duckdb.execute(f"CREATE OR REPLACE VIEW {cp}.{rel} AS (SELECT key, label, {cp} AS cnt, keyness FROM '{root}/par/{rel}.parquet' WHERE cnt > 0 ORDER BY cnt desc)") #duckdb.execute(f"CREATE OR REPLACE VIEW en.{name} AS (SELECT key, label, en AS cnt, keyness FROM '{root}/par/{name}.parquet' WHERE en > 0 ORDER BY cnt desc)")
			setattr(x, rel, lambda lem, dep=rel,db=cp:  duckdb.sql(f"select label, {db} as cnt, keyness from '{root}/par/{dep}.parquet' where key = '{lem}' and cnt > 0 order by cnt desc").df() if not "'" in lem else pd.DataFrame([]) )
		for name in ('gram2','gram3','gram4','gram5','xgram2','xgram3','xgram4','xgram5','formal','frame','read','snt','svo','termmap','terms','tok','vpat','xtok'):
			if os.path.exists(f"{root}/{cp}/{name}.parquet"): # local version will overwrite the online version
				duckdb.execute(f"create OR REPLACE view {cp}.{name} AS FROM read_parquet('{root}/{cp}/{name}.parquet')")

	if os.path.exists(f"{root}/par/ce.parquet"):
		duckdb.execute(f"create OR REPLACE view ce as (from read_parquet('{root}/par/ce.parquet'))")
		duckdb.execute(f"create OR REPLACE view c as (select key, label, cn as cnt from read_parquet('{root}/par/ce.parquet') where cnt > 0 order by cnt desc)")
		duckdb.execute(f"create OR REPLACE view e as (select key, label, en as cnt from read_parquet('{root}/par/ce.parquet') where cnt > 0 order by cnt desc)")
	else: 
		duckdb.execute("create OR REPLACE view ce as (from read_parquet('http://file.yulk.net/yulk/par/ce.parquet'))")
		duckdb.execute("create OR REPLACE view c as (from read_parquet('http://file.yulk.net/yulk/par/c.parquet'))")
		duckdb.execute("create OR REPLACE view e as (from read_parquet('http://file.yulk.net/yulk/par/e.parquet'))")

	### walk pycode/*.py,   loadsql in pycode/walk.py 
	for file in [file for _root, dirs, files in os.walk(f"{root}/pycode",topdown=False) for file in files if file.endswith(".py") and not file.startswith("_") ]:
		try:
			dic = {}
			compiled_code = compile( loadfile(f'{root}/pycode/{file}'), f'{root}/pycode/{file}', 'exec') 
			exec(compiled_code,dic)
			[setattr(builtins, name, obj) for name, obj in dic.items() if not name.startswith("_") and not '.' in name and callable(obj)] # latter will overwrite former
			#name = file.split('.')[0]   #mod = getattr( __import__('pycode.'  + name), name) #  __import__('os')  =  import os  #mod = __import__(f'pycode.{name}', fromlist=['*'])
			#[ setattr(builtins, k, getattr(mod, k)) for k in dir(mod) if not k.startswith("_")  and callable( getattr(mod, k) )] 
		except Exception as e:
			print (">>load pycode ex:", name, '|',  e, flush=True)
			exc_type, exc_value, exc_obj = sys.exc_info() 	
			traceback.print_tb(exc_obj)

[setattr(builtins, k, f) for k, f in globals().items() if not k.startswith("_") and not '.' in k and not hasattr(builtins,k) and callable(f) ]
if __name__ == "__main__": 	pass 
