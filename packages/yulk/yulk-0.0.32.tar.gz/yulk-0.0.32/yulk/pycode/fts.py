# added 2025.10.16
import os,builtins,json, shutil
from whoosh.index import create_in,open_dir
from whoosh.fields import *
from whoosh.query import Term
from whoosh.qparser import QueryParser
from collections import Counter
import pandas as pd

fts_folder	= 'indexfts' 
schema		= Schema(sid=ID(stored=True), snt=TEXT(stored=True), terms=KEYWORD)

## used by search 
def getix(name):
	if not hasattr(getix, name):  
		#yulkroot = os.path.dirname(os.path.abspath(yulk.__file__))
		setattr(getix, name,  open_dir(f'{root}/{name}/{fts_folder}') )
	return getattr(getix, name)

def fts(q, field:str='snt', name:str='en', **kwargs): 
	ix = getix(name)  #open_dir(f'/yulk/{name}/{fts_folder}') #getix(name) 
	with ix.searcher() as searcher:
		query = QueryParser(field, ix.schema).parse(q)
		results = searcher.search(query, limit=int(kwargs.get('limit',10)))
		df = pd.DataFrame( [{"sid": hit['sid'], "snt":hit['snt']} for hit in results ] )
		df.attrs.update( {"size":len(results), "runtime": results.runtime, "q": q, "name":name, "limit": kwargs.get('limit',10) })
	return df
sntso = lambda lex, name='en', **kwargs:  fts(lex, field='snt', name=name, **kwargs)

def termso(term, field:str='terms', name:str='en', **kwargs):
	ix = getix(name) 
	with ix.searcher() as searcher:
		results = searcher.search( Term(field,term), limit=int(kwargs.get('limit',10)) ) #'open:dobjvn:door'
		df = pd.DataFrame( [{"sid": hit['sid'], "snt":hit['snt']} for hit in results ] )
		df.attrs.update( {"size":len(results), "runtime": results.runtime, "term": term, "name":name, "limit": kwargs.get('limit',10) })
		#res =	{"size":len(results), "runtime": results.runtime, "term": term, "name":name, "limit": kwargs.get('limit',10), "data": { hit['sid']:hit['snt'] for hit in results} }
	return df

def phraseso(q, name:str='en', **kwargs):
	ix = getix(name) 
	with ix.searcher() as searcher:
		parser = QueryParser("snt", ix.schema)
		query = parser.parse(f'"{q}"')
		results = searcher.search( query , limit=int(kwargs.get('limit',10))) 
		#res =	{"size":len(results), "runtime": results.runtime, "q": q, "name":name, "limit": kwargs.get('limit',10), "data": { hit['sid']:hit['snt'] for hit in results} }
		df = pd.DataFrame( [{"sid": hit['sid'], "snt":hit['snt']} for hit in results ] )
		df.attrs.update( {"size":len(results), "runtime": results.runtime, "q": q, "name":name, "limit": kwargs.get('limit',10) })
	return df

def docfreq(*args, field:str='terms', name:str='en'):
	ix = getix(name) 
	with ix.reader() as reader:
		total_docs = reader.doc_count()
		res = [{ "term": term, "freq": reader.doc_frequency(field, term), 'totalsnt':total_docs} for term in args]
	return pd.DataFrame(res)
lexfreq		= lambda *args, name='en': docfreq(*args, field='snt', name=name)

def mfso(lex, *cplist, field='snt'):
	rows = []
	for cp in cplist: 
		ix = getix(cp) 
		with ix.reader() as reader:
			rows.append( {"name": cp, "freq":reader.doc_frequency(field, term), "mf": round( 1000000 * reader.doc_frequency(field, term)/(reader.doc_count()+0.001), 1)} ) 
	return pd.DataFrame(rows)

def prefixso(prefix, field:str='terms', name:str='en', **kwargs): # prefix= open:dobjvn:
	if not prefix: return pd.DataFrame()
	ix = getix(name) 
	with ix.reader() as reader:
		res = {term.decode()[len(prefix):] : info.doc_frequency() for term, info in reader.iter_prefix(field, prefix=prefix)}
	return pd.DataFrame( Counter(res).most_common(), columns=['term','freq'])

def hello_fts():
	if not os.path.exists("indexdir"):   os.mkdir("indexdir")
	schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)
	builtins.ix = create_in("indexdir", schema)
	writer = ix.writer()
	writer.add_document(title=u"First document", path=u"/a",
						 content=u"This is the first document we've added!")
	writer.add_document(title=u"Second document", path=u"/b",
						 content=u"The second one is even more interesting!")
	writer.commit()
	with ix.searcher() as searcher:
		query = QueryParser("content", ix.schema).parse("first")
		results = searcher.search(query)
		print(results[0])

def test_so():
	from whoosh.index import open_dir
	ix = open_dir("indexdir")  
	with ix.reader() as reader:
		field_reader = reader.field("content")  
		all_terms = list(field_reader.lexicon())
		for term in field_reader.lexicon():
			print(term)
		doc_freq = reader.doc_frequency("content", b"python")  
		print(f"Term 'python' appears in {doc_freq} documents.")

if __name__ == "__main__": 
	pass
	
'''
>>> type(results[0])
<class 'whoosh.searching.Hit'>
>>> results[0]['sid']
'e4659251-121d-2401-9fd4-d6b0255fa839'
>>> results[0]['snt']
"And they're open for almost seven days yeah on Saturdays they're open I think  they don't open on the Sunday until ten o'clock."
'''