# 2025.10.12  nlp doc api func list ,  return doc/df | pip install thinc==8.3.4
import spacy,json, builtins, os,requests,time,sys, traceback,math,platform,zlib,re ,hashlib
from spacy.tokens import Doc
from spacy.matcher import Matcher,DependencyMatcher
from collections import Counter  
from types import MethodType
import pandas as pd  
sntmd5	= lambda text: hashlib.md5(text.strip().encode("utf-8")).hexdigest()
sptoks	= lambda sp: ' '.join([f"{t.text.replace(' ','-')}_{t.tag_}_{t.ent_type_}_{t.dep_}{t.head.i}_{t.pos_}_{t.lemma_}"  if t.ent_type_.startswith('NP') else f"{t.text}_{t.tag_}_{t.dep_}_{t.pos_}_{t.lemma_}" for t in sp]) 
toks	= lambda doc:	[ {"i": t.i, "lex":t.text, "lem":t.lemma_, "pos": t.pos_, "tag":t.tag_, 'textws':t.text_with_ws, "dep":t.dep_, "headi":t.head.i, "glem": t.head.lemma_, "gpos": t.head.pos_, "gtag": t.head.tag_} for t in ( parse(doc) if isinstance(doc, str) else doc) ]
docdf	= lambda doc:  pd.DataFrame(toks(doc) ) # add attrs, later , to store json, and np list

def parse(snt, model=os.getenv('spacy_model','en_core_web_sm')): 
	if not hasattr(parse, 'nlp') : setattr(parse, 'nlp',  spacy.load( model ) )  
	return parse.nlp(snt)
def sntbr(text:str="She has ready. It are ok.", **kwargs): 
	from spacy.lang import en
	if not hasattr(sntbr, 'inst'):
		sntbr.inst = en.English()
		sntbr.inst.add_pipe("sentencizer")
	doc		= sntbr.inst(text)
	return  [ sp.text.strip() for i,sp in enumerate(doc.sents) ] if 'raw' in kwargs else pd.DataFrame( [ {"i": i, "snt": sp.text.strip()} for i,sp in enumerate(doc.sents) ])
def snts(text:str="She has ready. It are ok.", **kwargs): 
	from spacy.lang import en
	if not hasattr(snts, 'inst'):
		snts.inst = en.English()
		snts.inst.add_pipe("sentencizer")
	doc		= snts.inst(text)
	return  pd.DataFrame([ {"i":i, "snt": sp.text.strip(), "tc": len(sp), } for i,sp in enumerate(doc.sents) ]) if 'df' in kwargs  else [ sp.text.strip() for i,sp in enumerate(doc.sents) ] 

np			= lambda snt: pd.DataFrame([ {"np": np.text, "start":np.start, "end": np.end, "tc": np.end - np.start }  for np in parse(snt).noun_chunks])
ROOT		= lambda snt: next(iter([ t.lemma_ for t in parse(snt) if t.dep_ == 'ROOT']), None) #next(iter(lst), None)
totoken		= lambda t : {"text":t.text, "lem":t.lemma_, "pos":t.pos_,"tag":t.tag_, "dep":t.dep_, "textws":t.text_with_ws, "i":t.i, "headi":t.head.i}
oneself		= {"himself": "_oneself",  "herself":"_oneself",  "myself":"_oneself",  "yourself":"_oneself",  "itself":"_oneself",  "ourselves":"_oneself",  "yourselves":"_oneself",  "themselves":"_oneself", "he":"_sb", "she":"_sb","we":"_sb","they":"_sb","I":"_sb","you":"_sb","us":"_sb","his":"_one's",  "one's":"_one's",} # her, her pat, like her 
postag		= lambda snt_or_doc:  "_^ " + ' '.join([ f"{t.text}_{t.pos_}_{t.tag_}" if t.pos_ in ('PROPN','NUM','X','SPACE','PUNCT') else f"{t.text}_{t.lemma_}_{t.pos_}_{t.tag_}{oneself.get(t.text.lower(), '')}"  for t in _parse(snt_or_doc)]) 
skenp_tok	= lambda t: ( pair := f"_{t.lemma_}_{t.pos_}_NP_{t.dep_}{t.head.i}" if (t.ent_type_ == 'NP' and t.lemma_ not in ('that','which')) else f"_{t.pos_}_{t.tag_}_{t.dep_}{t.head.i}" if t.pos_ in ('PROPN','NUM','X','SPACE','PUNCT') else f"{t.text if t.text in ('I') else t.text.lower()}_{t.lemma_}_{t.pos_}_{t.tag_}{oneself.get(t.text.lower(), '')}_{t.dep_}{t.head.i}", 	pair + t.ent_id_ if (t.ent_id_.startswith("_CL") and not 'ROOT' in t.ent_id_) else pair )[-1]
es_skenp	= lambda doc: ( merge_np(doc) , attach_cl(doc),  "_^ " + ' '.join([ skenp_tok(t) for t in doc]) )[-1]
syntactic_depth = lambda token: 1 if not list(token.children) else  1 + max(syntactic_depth(child) for child in token.children)
depth			= lambda doc: syntactic_depth([t for t in doc if t.head == t][0])
#depth			= lambda snt,**kwargs: syntactic_depth([t for t in (_parse(snt) if isinstance(snt, str) else snt) if t.head == t][0])
#avg_sentence_len = len(text.split()) / len(list(doc.sents)) 
# Lexile 200L-1600L  Lexile = 500 + 20 * awl - 50 * ast
awc			= lambda doc: ( arr:= [len(t.text) for t in doc if not t.is_punct], 0 if not arr else sum(arr)/len(arr))[-1] 
ast			= lambda doc: ( arr:= [len(sent) for sent in doc.sents], 0 if not arr else sum(arr)/len(arr))[-1]
max_depth	= lambda doc: (
				roots := [t for t in doc if t.head == t],
				max(syntactic_depth(root) for root in [t for t in doc if t.head == t] ) if roots else 0 )[-1]
lexile		= lambda doc: 500 + 20 * awc(doc) - 50 * ast(doc)
lattice		= lambda doc:	[ {"i": t.i, "lex":t.text, "lem":t.lemma_, "pos": t.pos_, "p":shortpos(t.pos_), "tag":t.tag_, 'textws':t.text_with_ws, "dep":t.dep_, "headi":t.head.i, "glem": t.head.lemma_, "gpos": t.head.pos_, "gp":shortpos(t.head.pos_),  "gtag": t.head.tag_} for t in ( parse(doc) if isinstance(doc, str) else doc) ]
docdf		= lambda doc:  pd.DataFrame(lattice(doc) ) # add attrs, later , to store json, and np list
txtdf		= lambda doc:  pd.DataFrame([ {"i": t.i, "lex":t.text, "lem":t.lemma_, "pos": t.pos_, "tag":t.tag_, "dep":t.dep_, "headi":t.head.i, "glem": t.head.lemma_, "gpos": t.head.pos_,  "gtag": t.head.tag_, "sntbeg":t.sent.start, 'textws':t.text_with_ws} for t in ( parse(doc) if isinstance(doc, str) else doc) ])
token		= lambda text,name='en_core_web_sm':  pd.DataFrame( [{"sid":sntmd5(t.sent.text), 'i':t.i, "lex":t.text, "lem":t.lemma_, "pos":t.pos_, "tag":t.tag_, "dep":t.dep_, "headi":t.head.i, "glem":t.head.lemma_, "gpos":t.head.pos_, "gtag":t.head.tag_, 'ent':t.ent_type_ } for t in  parse(text, model=name) ])  if isinstance(text,str) else pd.concat([token(s) for s in text], ignore_index=True)

parsezh		= lambda text: parse(text, model='zh_core_web_sm')
segzh		= lambda text: [t.text for t in parse(text, model='zh_core_web_sm')] if isinstance(text, str) else [ segzh( str(s)) for s in text ]
shortpos	= lambda pos:	{"NOUN":'n', "VERB":'v', "ADP":'p', "DET":'e', "PRON":'r', "ADJ":'a', "AUX":"x", "ADV":'d',"CCONJ":'c', "PART":'t',"SCONJ":'s', "INTJ":'i','PUNCT':'u','PROPN':'O', 'VBG':'g', 'VBN':'b','TO':'o'}.get(pos,'?')  # dobjvn 
highlex		= lambda lex, snt, **kwargs: re.sub(rf"\b({lex})\b", r"<b>\1</b>" if 'html' in kwargs else r"**\1**", snt, flags=re.I) 
highterm	= lambda term='open:dobjvn:door', snt="I opened the door.", sepa=':': highlex('|'.join([lemlex(t) for t in term.strip().split(sepa)]), snt)

def merge_np(doc):
	with doc.retokenize() as retokenizer:
		try:
			[retokenizer.merge(np, attrs={"tag": np.root.tag, "dep": np.root.dep, "ent_type": "NP", "lemma":doc[np.end-1].lemma} )  for np in doc.noun_chunks]
		except Exception as e:
			print ( "merge_np ex:", e)
	return doc

def merge_pnp(doc):  # in spite of , 2023.9.22
	if not hasattr(merge_pnp, 'matcher'):
		merge_pnp.matcher = spacy.matcher.PhraseMatcher(doc.vocab) 
		merge_pnp.matcher.add("pnp", [parse(s) for s in 'in spite of,with regard to,in addition to,on behalf of'.split(',') ])
	with doc.retokenize() as retokenizer:
		for sp in merge_pnp.matcher(doc, as_spans=True):
			try:
				retokenizer.merge(sp, attrs={"pos": doc[sp.start].pos, "tag": doc[sp.start].tag, "dep": doc[sp.start].dep, "lemma":sp.text.lower(), "ent_type": "pnp"})
			except Exception as e:
				print ( "merge_pnp ex:", e , sp)
	return doc

def ofNP(doc): # after NP is merged
	if not hasattr(ofNP, 'matcher'):
		ofNP.matcher = spacy.matcher.Matcher(doc.vocab)
		ofNP.matcher.add("np-of-np", [[{"ENT_TYPE": "NP"}, {"LEMMA":"of"},{"ENT_TYPE": "NP"}], [{"ENT_TYPE": "NP"}, {"LEMMA":"of"},{"POS": "NOUN"}]], greedy ='LONGEST')
	return [ doc[start].lemma_.lower() +":"+ doc[end-1].lemma_.lower() + ':' +doc[start:end].text.lower() for name, start, end in ofNP.matcher(doc) ]

## phrase
vp_span		= lambda doc,ibeg,iend: doc[ibeg].lemma_ + " " + doc[ibeg+1:iend].text.lower()
def kp_span(doc, start, end, name):  
	if name in ('vp','vprt'):		return (doc[start].lemma_,doc[start].pos_, vp_span(doc,start,end) )
	elif name.startswith("be_") :	return (doc[start+1].lemma_,doc[start+1].pos_,vp_span(doc,start,end))
	elif name in ('ap','pp'):		return (doc[end-1].lemma_,doc[end-1].pos_,doc[start:end].text.lower())
	elif name in ('vend'):			return (doc[end-1].lemma_,doc[end-1].pos_,vp_span(doc,start,end))
	elif name in ('vp*','bap'):		return (doc[start+1].lemma_,doc[start+1].pos_,vp_span(doc,start,end))  # be _VBN of 
	else:							return (doc[start].lemma_,doc[start].pos_,doc[start:end].text.lower())

phrase_pattern = { #with t as (SELECT regexp_extract(skenp, '(\S+_ADV )+\S+_ADJ') x from snt where x != '') select regexp_extract(x, '([a-z]+)_ADJ$',1) adj, regexp_replace(x, '_\S+','','g') from t;
	"vend":[[{"POS": {"IN": ["AUX","VERB"]}},{"POS": {"IN": ["ADV"]}, "OP": "*"}, {"POS": {"IN": ["ADJ","VERB"]}, "OP": "*"},{"POS": {"IN": ["PART","ADP","TO"]}, "OP": "*"},{"POS": 'VERB'}]], # could hardly wait to meet
	"vp":  [[{'POS': 'VERB',"TAG": {"NOT_IN": ["VBN"]}},{"POS": {"IN": ["DET","ADP","ADV", "ADJ"]}, "OP": "*"},{"POS": 'NOUN'}, {"POS": {"IN": ["ADP","TO"]}, "OP": "*"}], [{'POS': 'VERB'},{"POS": {"IN": ["DET","ADP","ADJ","TO","PART"]}, "OP": "*"},{"POS": 'VERB'}], [{'POS': 'VERB',"TAG": {"NOT_IN": ["VBN"]}},{"POS": {"IN": ["ADP","ADV"]}, "OP": "+"}]], # vpg, insist on VBG
	"vp*":  [[{"POS": {"IN": ["AUX"]}}, {"TAG": 'VBN'}, {"POS": {"IN": ["PREP", "ADP",'PART']}}]], # She was convicted of shoplifting.
	"pp":  [[{'POS': 'ADP'},{"POS": {"IN": ["DET","NUM","ADJ",'PUNCT','CONJ']}, "OP": "*"},{"POS": {"IN": ["NOUN","PART"]}, "OP": "+"}]],    #in spite of sports
	"ap":  [[{"POS": {"IN": ["ADV"]}, "OP": "+"}, {"POS": 'ADJ'}]],  
	"vprt":	[[{"POS": 'VERB', "TAG": {"NOT_IN": ["VBN"]}}, {"POS": {"IN": ["PREP", "ADP",'TO']}, "OP": "+"}]],   # look up /look up from,  computed twice
	"bap": [[{'LEMMA': 'be'},{"TAG": {"IN": ["JJ","VBN"]}}, {"POS": {"IN": ["PREP", "ADP",'PART']}}]],   # be angry with
} #for name, ibeg,iend in matcher(doc) : print(spacy.nlp.vocab[name].text, doc[ibeg:iend].text)

def phrase(doc): # added 2023.4.18, [{'type': 'ap', 'lem': 'good', 'chk': 'too good', 'pos': 'ADJ', 'name': 'AP', 'start': 2, 'end': 4}]
	arr = []
	if not hasattr(phrase, 'matcher'):
		phrase.matcher = Matcher(doc.vocab)
		[ phrase.matcher.add(name, rules,  greedy ='LONGEST')  for name, rules in phrase_pattern.items()] 
	for name, start, end in phrase.matcher(doc):
		try:
			name = doc.vocab[name].text
			lem, pos, chk =  kp_span(doc,start,end, doc.vocab[name].text)
			name = name.replace('*','') 
			arr.append({"type":name, "lem":lem, "pos":pos, "chk":chk,  "ibeg":start, "iend":end}) #[{'type': 'vp', 'lem': 'keep', 'pos': 'VERB', 'chk': 'keep in touch with', 'ibeg': 1, 'iend': 5}, {'type': 'vprt', 'lem': 'keep', 'pos': 'VERB', 'chk': 'keep in', 'ibeg': 1, 'iend': 3}, {'type': 'pp', 'lem': 'in', 'pos': 'ADP', 'chk': 'in touch', 'ibeg': 2, 'iend': 4}]
			#arr.append(f"{lem}:{name}:{chk}") # keep:vp:keep in touch with
		except Exception as e:
			print ( "match ex:", e , start, end, doc)
	return pd.DataFrame(arr)

## vpat 
class POSTAG:
	V		= {"POS": 'VERB'}
	VERB	= {"POS": 'VERB', "TAG": {"NOT_IN": ["VBN"]}}
	BE		= {'LEMMA': 'be'}
	IN		= {'TAG': 'IN'}
	RP		= {'TAG': 'RP'}
	SCONJ   = {'POS': 'SCONJ'}  # whether to go 
	WRB     = {'TAG': 'WRB'} # know how to go
	TO		= {'LEMMA': 'to'}
	HAVE	= {'LEMMA': 'have'}
	THAT	= {'LEMMA': 'that'}
	NP		= {"ENT_TYPE":"NP"}
	PRON	= {"POS":"PRON"}
	ADP		= {"POS":"ADP"}
	ADJ		= {"POS":"ADJ"}
	ADV		= {"POS":"ADV"}
	DET		= {"POS":"DET"}
	NN		= {"TAG":"NN"}
	NNS		= {"TAG":"NNS"}
	VB		= {"TAG":"VB"}
	VBG		= {"TAG":"VBG"}
	VBN		= {"TAG":"VBN"}
	ADPTO	= {"POS": {"IN": ["PART","ADP","TO"]}}

vpattern= {  # I have to remind myself constantly that I am really in AD 3008 .  | _V _NP _ADV _mark 
 	"VERB_dobj":		[[POSTAG.VERB,{"DEP":"dobj", "ENT_TYPE":"NP"}]] ,
	'VERB_VBG':			[[POSTAG.VERB,{"TAG":"VBG","DEP":"xcomp"}] ],# enjoy/VERB _VBG
	'VERB_TO_VB':		[[POSTAG.VERB,POSTAG.TO,POSTAG.VB] ], # agree to disagree
 	'VERB_TO_HAVE_VBN':		[[POSTAG.VERB,POSTAG.TO,POSTAG.HAVE,POSTAG.VBN] ],  # pretend to have done, 2023.10.23
	'VERB_TO_BE_VBN':		[[POSTAG.VERB,POSTAG.TO,POSTAG.BE,POSTAG.VBN] ],#She asked to be given more work to do.
	'VERB_TO_BE_ADJ':		[[POSTAG.VERB,POSTAG.TO,POSTAG.BE,POSTAG.ADJ] ],
	'VERB_TO_BE_NP':		[[POSTAG.VERB,POSTAG.TO,POSTAG.BE,POSTAG.NP] ], # 2023.10.23
	'VERB_TO_BE_VBG':		[[POSTAG.VERB,POSTAG.TO,POSTAG.BE,POSTAG.VBG] ],
	'VERB_NP_TO_VB':		[[POSTAG.VERB,POSTAG.NP,POSTAG.TO,POSTAG.VB] ],	#I believe him to go.
	'VERB_NP_TO_BE':		[[POSTAG.VERB,POSTAG.NP,POSTAG.TO,POSTAG.BE] ],	#I believe him to be ready.
	'VERB_IN_NP_TO_BE':		[[POSTAG.VERB,POSTAG.IN,POSTAG.NP,POSTAG.TO,POSTAG.BE] ], #I'll arrange for you to come.
	'VERB_IN_NP_TO_VB':		[[POSTAG.VERB,POSTAG.IN,POSTAG.NP,POSTAG.TO,POSTAG.VB] ], # 2023.10.4
	'VERB_ADP_NP':		[[POSTAG.VERB,POSTAG.ADP,POSTAG.NP] ],
	'VERB_ADP_NP_TO_BE_VBN':	[[POSTAG.VERB,POSTAG.ADP,POSTAG.NP,POSTAG.TO,POSTAG.BE,POSTAG.VBN] ], #the teacher insisted on all the compositions to be handed in on monday. | added 2023.9.6
	'VERB_ADP_NP_TO_BE_ADJ':	[[POSTAG.VERB,POSTAG.ADP,POSTAG.NP,POSTAG.TO,POSTAG.BE,POSTAG.ADJ] ],
	'VERB_ADP_NP_TO_BE_NP':		[[POSTAG.VERB,POSTAG.ADP,POSTAG.NP,POSTAG.TO,POSTAG.BE,POSTAG.NP] ],
	'V_IN_TO_VB':			[[POSTAG.V,POSTAG.IN,POSTAG.TO,POSTAG.VB] ],	#She has not decided whether to go or not.
	'V_WRB_TO_VB':			[[POSTAG.V,POSTAG.WRB,POSTAG.TO,POSTAG.VB] ], # how to go 
	'V_NP_TO_VB':			[[POSTAG.V,POSTAG.NP,POSTAG.TO,POSTAG.VB] ],
	'V_NP_VB':			[[POSTAG.V,POSTAG.NP,POSTAG.VB] ],
	'V_NP_VBG':			[[POSTAG.V,POSTAG.NP,POSTAG.VBG] ], 	#The rain stopped me coming.
	'VERB_NP_TO_BE_VBN':		[[POSTAG.VERB,POSTAG.NP,POSTAG.TO,POSTAG.BE,POSTAG.VBN] ],
	'VERB_NP_TO_BE_ADJ':		[[POSTAG.VERB,POSTAG.NP,POSTAG.TO,POSTAG.BE,POSTAG.ADJ] ],
	'VERB_NP_TO_BE_NP':			[[POSTAG.VERB,POSTAG.NP,POSTAG.TO,POSTAG.BE,POSTAG.NP] ],
	"VERB_NP_NP":		[[POSTAG.VERB,POSTAG.NP,POSTAG.NP]], # give me a book, dative 
	"VERB_PRON_NP":		[[POSTAG.VERB,POSTAG.PRON,POSTAG.NP]],
	"VERB_NP_ADJ":		[[POSTAG.VERB,POSTAG.NP,POSTAG.ADJ]], # keep the box open
	"VERB_NP_VBN":		[[POSTAG.VERB,POSTAG.NP,POSTAG.VBN]],    
	"VERB_NP_ADV":		[[POSTAG.VERB,POSTAG.NP,POSTAG.ADV]] , # have a look around
	"be_ADV_ADJ_IN_NP":		[[POSTAG.BE,POSTAG.ADV,POSTAG.ADJ,POSTAG.IN,POSTAG.NP]], # It is less voluntary than the forced wait.
	"be_ADV_ADJ_IN":		[[POSTAG.BE,POSTAG.ADV,POSTAG.ADJ,POSTAG.IN]],
	"be_ADJ_TO_VB":		[[POSTAG.BE,POSTAG.ADJ,POSTAG.TO,POSTAG.VB]],
	"be_ADJ_TO_BE_VBN":	[[POSTAG.BE,POSTAG.ADJ,POSTAG.TO,POSTAG.BE,POSTAG.VBN]],
	"be_ADJ_ADP_NP":	[[POSTAG.BE,POSTAG.ADJ,POSTAG.ADP,POSTAG.NP]],
	"be_ADJ_ADP_VBG":	[[POSTAG.BE,POSTAG.ADJ,POSTAG.ADP,POSTAG.VBG]],
	"be_VBN_ADP":		[[POSTAG.BE,POSTAG.VBN,POSTAG.ADP]],     #skenp:_be consider/VBN _ADP   ~ => consider/
	"be_VBN_to":		[[POSTAG.BE,POSTAG.VBN,POSTAG.TO]],  # be forced to
	"be_VBN_that":		[[POSTAG.BE,POSTAG.VBN,POSTAG.THAT]],
	"VERB_ADV_ADP_VBG": [[POSTAG.VERB,POSTAG.ADV,POSTAG.ADP,POSTAG.VBG]] , # look forward to doing
	"VERB_ADV_ADP_NP":	[[POSTAG.VERB,POSTAG.ADV,POSTAG.ADP,POSTAG.NP]] , # look forward to _NP
	"VERB_ADP_ADP_NP":	[[POSTAG.VERB,POSTAG.ADP,POSTAG.ADP,POSTAG.NP]] , # look up from _NP
	"VERB_ADP_ADP_VBG":	[[POSTAG.VERB,POSTAG.ADP,POSTAG.ADP,POSTAG.VBG]] , 
	"VERB_ADP_VBG":		[[POSTAG.VERB,POSTAG.ADP,POSTAG.VBG]], # insist on _VBG
	"VERB_ADP_NP":		[[POSTAG.VERB,POSTAG.ADP,POSTAG.NP]] , # turn off the radio 
	"VERB_NP_ADP_VBG":	[[POSTAG.VERB,POSTAG.NP,POSTAG.ADP,POSTAG.VBG]] , # stop _NP from _VBG 
	"VERB_NN_ADP_NP":	[[POSTAG.VERB,POSTAG.NN,POSTAG.ADP,POSTAG.NP]] , # make use of , pay attention to
	"VERB_NP_ADP_NP":	[[POSTAG.VERB,POSTAG.NP,POSTAG.ADP,POSTAG.NP]] , # Over the next few days, they prepared desserts for their guests.
	"VERB_NN_ADP_VBG":	[[POSTAG.VERB,POSTAG.NN,POSTAG.ADP,POSTAG.VBG]] , # make use of , pay attention to
	"VERB_ADJ_NN_ADP":	[[POSTAG.VERB,POSTAG.ADJ,POSTAG.NN,POSTAG.ADP]] , # pay close attention to
	"VERB_ADP_NP_ADP_NP":[[POSTAG.VERB,POSTAG.ADP,POSTAG.NP,POSTAG.ADP,POSTAG.NP]] , # vary from A to B 
	"VERB_NP_ADP_NN":	[[POSTAG.VERB,POSTAG.NP,POSTAG.ADP,POSTAG.NN]] , # take _NP into account
	"V_NP_RP_IN":	[[POSTAG.V,POSTAG.NP,POSTAG.RP,POSTAG.IN]] , 
	"V_RP_IN":	[[POSTAG.V,POSTAG.RP,POSTAG.IN]] ,
	"VERB_ADP_NN_ADP":	[[POSTAG.VERB,POSTAG.ADP,POSTAG.NN,POSTAG.ADP]] , # keep in touch with
}

def vpat(doc): 
	def tok(doc, i, start, arr):
		if i == start and doc[i].lemma_ != 'be':	 return 'V' # doc[i].lemma_ 
		if doc[i].tag_ in ( 'NN', 'NNS') and not ' ' in doc[i].text and arr[i - start] in ( 'NN', 'NNS') : return doc[i].text.lower() # keep in touch with 
		if doc[i].lemma_ in ( 'be', 'have') : return doc[i].lemma_ # added 2023.10.24
		if doc[i].tag_ in ( 'VBG', 'VBN',"VB") : return  doc[i].tag_
		if doc[i].pos_ in ( 'ADJ') : return doc[i].text.lower() if doc[i-1].lemma_ == 'be' else doc[i].pos_  # assume: ADJ not in the first 
		if doc[i].ent_type_ == 'NP' : return 'N'
		return doc[i].text.lower()

	if not hasattr(vpat, 'matcher'):
		vpat.matcher = Matcher(doc.vocab)
		[ vpat.matcher.add(name, rules,  greedy ='LONGEST')  for name, rules in vpattern.items()] 
	rows = []
	for name, start, end in vpat.matcher(doc):
		try:
			offset	= 1 if doc[start].lemma_ == 'be' else 0 
			vpatchk = " ".join([ tok(doc,i,start, doc.vocab[name].text.split('_') )   for i in range(start, end) ])
			rows.append({"lem":doc[start+offset].lemma_, "type":"vpat", "chunk":vpatchk})
			rows.append({"lem":doc[start+offset].lemma_, "type":"vpos", "chunk":doc.vocab[name].text})
		except Exception as e:
			print ( "match ex:", e , start, end, doc)
	for t in doc: #	#I believe him to go. => ccomp, to be removed later
		if t.dep_ == 'ccomp' and t.pos_ == 'VERB' and t.head.pos_ == 'VERB' and t.head.tag_ != 'VBN' : #The forced wait makes people passive.
			rows.append({"lem":t.head.lemma_, "type":"vpat", "chunk":f"{t.head.lemma_} CLccomp"})
			rows.append({"lem":t.head.lemma_, "type":"vpos", "chunk":"VERB CLccomp"})
	return pd.DataFrame(rows)

## from exchunk 
class Chunkex:
	NP_start= {"ENT_TYPE": "NP", "IS_SENT_START": True}
	VERB	= {"POS": {"IN": ["VERB"]}}
	VBN		= {"TAG": {"IN": ["VBN"]}}
	NOUN	= {"POS": {"IN": ["NOUN"]}}
	DET		= {"POS": {"IN": ["DET"]}}
	TO		= {"TAG": {"IN": ["TO"]}}
	BE		= {"LEMMA": "be"}
	NN		= {"TAG": {"IN": ["NN"]}}
	JJ		= {"TAG": {"IN": ["JJ"]}}
	ADP		= {"POS": {"IN": ["ADP"]}}
	PUNCT	= {"IS_PUNCT": True}
def chunkex(doc):
	if not hasattr(chunkex, 'matcher'): 
		chunkex.matcher	= Matcher(doc.vocab)  # :1 , verb's offset 
		chunkex.matcher.add("1:JJ:pay attention to", [[Chunkex.VERB,Chunkex.NOUN,Chunkex.ADP]]) # make use of , pay attention to -> pay _jj attention to 
		chunkex.matcher.add("1:RB:is pretty/destroyed", [[Chunkex.BE,Chunkex.JJ],[Chunkex.BE,Chunkex.VBN]])
		chunkex.matcher.add("2:RB:finished homework", [[Chunkex.VERB,Chunkex.NOUN,Chunkex.PUNCT]])
		chunkex.matcher.add("3:RB:solve the problem", [[Chunkex.VERB,Chunkex.DET,Chunkex.NOUN,Chunkex.PUNCT]])
		chunkex.matcher.add("1:RB:to open the door", [[Chunkex.TO,Chunkex.VERB,Chunkex.DET,Chunkex.NOUN],[Chunkex.TO,Chunkex.VERB,Chunkex.NOUN],[Chunkex.TO,Chunkex.VERB,{"POS":"PRP$"}]])  
		chunkex.matcher.add("2:JJ:make it *dead simple to", [[Chunkex.VERB,{"LEMMA": "it"},Chunkex.JJ,Chunkex.TO]]) #It will make it *dead simple to utilize the tools.
	rows = []
	for name, ibeg, iend in chunkex.matcher(doc):
		offset, tag = doc.vocab[name].text.split(':')[0:2]
		offset = int(offset) 
		rows.append( { "pattern": " ".join( doc[i].text.lower() if i - ibeg != offset else  tag + " " + doc[i].text.lower() for i in range(ibeg, iend)), "tag":tag, "index": offset  })
	for np in doc.noun_chunks:
		if doc[np.start].pos_ == 'DET' : 
			if len(np) == 2  and doc[np.start+1].pos_ == 'NOUN': 
				rows.append( {"pattern": doc[np.start].text.lower() + " JJ " +  doc[np.start+1].text.lower(), "tag":'JJ' , "index":1 } ) 
			elif len(np) == 3  and doc[np.start+1].tag_ == 'JJ'  and doc[np.start+2].pos_ == 'NOUN': 
				rows.append( {"pattern": doc[np.start].text.lower() + " RB " +  doc[np.start+1:np.start+3].text.lower(), "tag":'RB' , "index":1 } ) 
	return pd.DataFrame(rows)

def rooti(doc): 
	for t in doc : 
		if t.dep_ == 'ROOT': return t.i 
	return -1
def merge_npi(doc): # updated 2024.10.3
	with doc.retokenize() as retokenizer:
		try:
			[retokenizer.merge(np, attrs={"tag": "NP", "dep": np.root.dep, "ent_type": f"NP{np.end-np.start}", "lemma":doc[np.end-1].lemma} )  for np in doc.noun_chunks]
		except Exception as e:
			print ( "merge_npi ex:", e)
	return doc
def cls(doc): # added 2024.12.19
	res = {} # ibeg -> [ibeg,iend, type, cl]
	for v in [t for t in doc if (t.pos_ == 'VERB' or t.lemma_ == 'be') and t.dep_ != 'ROOT' ] : # non-root,  v.headi = ROOT
		try:
			children = list(v.subtree)
			start = children[0].i  	
			end = children[-1].i + 1
			if v.dep_ not in ('xcomp') and end - start > 1 :
				res[start] = [start, end, 'CL' + v.dep_,  doc[start:end].text, v.head.i ]
		except Exception as e:
			print ( "merge_clause ex:", e, v )
	return res
def merge_beacomp(doc): # updated 2025.2.2
	with doc.retokenize() as retokenizer:
		try:
			[retokenizer.merge(doc[t.head.i:t.i+1], attrs={"pos":'VERB', "tag": t.tag, "dep": t.head.dep, "ent_type": f"beAdj", "lemma":t.head.lemma_ + ' '+ t.text} )  for t in doc if t.dep_ == 'acomp' and t.pos_ == 'ADJ' and t.head.i + 1 == t.i and t.head.lemma_ =='be']
		except Exception as e:
			print ( "merge_acomp ex:", e)
	return doc
def merge_prt(doc, func=None):  #func=lambda v, p: None
	'''I turn off the radio. => turn_off , added 2023.1.13'''
	if not hasattr(merge_prt, 'matcher'):
		merge_prt.matcher = spacy.matcher.Matcher(doc.vocab)
		merge_prt.matcher.add("prt", [[{"POS":"VERB","TAG": {"NOT_IN": ["VBN"]}}, {"POS":"ADP", "DEP":"prt"}]], greedy ='LONGEST')
	with doc.retokenize() as retokenizer:
		for name, start, end in merge_prt.matcher(doc):
			try:
				attrs = {"pos": doc[start].pos, "tag": doc[start].tag, "dep": doc[start].dep, "lemma":doc[start].lemma_ + " " + doc[start+1].lemma_, "ent_type": "vprt"}
				if func: func(doc[start], doc[start+1]) # notify 
				retokenizer.merge(doc[start : end], attrs=attrs)
			except Exception as e:
				print ( "merge_prt ex:", e , start, end)
	return doc
def join_prt(doc):  
	'''I turn off the radio. => turn_off , added 2025.10.2 '''
	if not hasattr(join_prt, 'matcher'):
		join_prt.matcher = spacy.matcher.Matcher(doc.vocab)
		join_prt.matcher.add("prt", [[{"POS":"VERB","TAG": {"NOT_IN": ["VBN"]}}, {"POS":"ADP", "DEP":"prt"}]], greedy ='LONGEST')
	with doc.retokenize() as retokenizer:
		for name, start, end in join_prt.matcher(doc):
			try:
				attrs = {"pos": doc[start].pos, "tag": doc[start].tag, "dep": doc[start].dep, "lemma":doc[start].lemma_ + "_" + doc[start+1].lemma_, "ent_type": "vprt"}
				retokenizer.merge(doc[start : end], attrs=attrs)
			except Exception as e:
				print ( "merge_prt ex:", e , start, end)
	return doc
def merge_vtov(doc):  
	if not hasattr(merge_vtov, 'matcher'):
		merge_vtov.matcher = spacy.matcher.Matcher(doc.vocab)
		merge_vtov.matcher.add("vtov", [[{"POS":"VERB","TAG": {"NOT_IN": ["VBN"]}},{"LEMMA":"to"}, {"TAG":"VB", "DEP":"xcomp"}]], greedy ='LONGEST')
	with doc.retokenize() as retokenizer:
		for name, start, end in merge_vtov.matcher(doc):
			try:
				attrs = {"pos": doc[start].pos, "tag": doc[start].tag, "dep": doc[start].dep, "lemma":doc[start].lemma_ + " to " + doc[start+2].lemma_, "ent_type": "vtov"}
				retokenizer.merge(doc[start : end], attrs=attrs)
			except Exception as e:
				print ( "merge_vtov ex:", e , start, end)
	return doc
def merge_vvbg(doc):  
	if not hasattr(merge_vvbg, 'matcher'):
		merge_vvbg.matcher = spacy.matcher.Matcher(doc.vocab)
		merge_vvbg.matcher.add("vtov", [[{"POS":"VERB","TAG": {"NOT_IN": ["VBN"]}},{"TAG":"VBG", "DEP":"xcomp"}]], greedy ='LONGEST')
	with doc.retokenize() as retokenizer:
		for name, start, end in merge_vvbg.matcher(doc):
			try:
				attrs = {"pos": doc[start].pos, "tag": doc[start].tag, "dep": doc[start].dep, "lemma":doc[start].lemma_ + " " + doc[start+1].text.lower(), "ent_type": "vvbg"}
				retokenizer.merge(doc[start : end], attrs=attrs)
			except Exception as e:
				print ( "merge_vvbg ex:", e , start, end)
	return doc

def xtok(texts, model='en_core_web_sm'):
	if not isinstance(texts, list): texts = [texts]
	rows = []
	for text in list(texts):
		try:
			doc = parse(text, model=model)
			merge_npi(doc)
			merge_beacomp(doc)
			merge_prt(doc) 
			merge_vvbg(doc)
			merge_vtov(doc)
			rows.extend( [{'sid': sntmd5(t.sent.text) ,'i':t.i ,'lex':"_" + t.pos_ if t.pos_ in ('PROPN','NUM','X') else t.text.lower() ,'lem':"_" + t.pos_ if t.pos_ in ('PROPN','NUM','X') else t.lemma_ ,'pos': t.pos_ ,'tag':t.tag_ ,'dep': t.dep_,'headi': t.head.i ,'glem': t.head.lemma_,'gpos': t.head.pos_ ,'gtag': t.head.tag_,'ent': t.ent_type_ if t.ent_type_ else ''} for t in doc])
		except Exception as e:
			print ( "xtok ex:", e, text)
	return pd.DataFrame(rows)

def clause(doc): # subtree of a verb is the clause , https://subscription.packtpub.com/book/data/9781838987312/2/ch02lvl1sec13/splitting-sentences-into-clauses | 2024.4.17
	''' [{'lem': 'be', 'chk': 'which is tedious', 'dep': 'relcl', 'pos': 'AUX', 'tag': 'VBZ', 'glem': 'book', 'gpos': 'NOUN', 'head': 3, 'start': 4, 'end': 7, 'i': 5, 'idx': 19}] '''
	if isinstance(doc, str) : doc = parse(doc) 
	arr = []
	for v in [t for t in doc if ( t.pos_ == 'VERB' or ( t.lemma_ == 'be' and t.tag_ not in ('VBN','VBG') )) and t.dep_ != 'ROOT'  and t.dep_ not in ('xcomp','auxpass') ] : # non-root /and t.tag_ != 'VBN' and len(t.subtree) > 1
		try:
			children = list(v.subtree)
			start = children[0].i  	
			end = children[-1].i 
			arr.append( {"lem":v.lemma_, "clause": doc[start:end+1].text, "dep": v.dep_, "pos":v.pos_, "tag": v.tag_,  "glem": v.head.lemma_,"gpos": v.head.pos_,"gtag": v.head.tag_,  }) # S.advcl ,  S.conj  "head": v.head.i, "start":start, "end": end+1, "i": v.i, "idx":v.idx, "tags":'-'.join([t.tag_ for t in doc[start:end+1]]),
		except Exception as e:
			print ( "walk_cl ex:", e, v, doc.text, flush=True)
	return pd.DataFrame(arr)

if __name__ == "__main__":
	pass # print ( parse("What I said is ok."))
