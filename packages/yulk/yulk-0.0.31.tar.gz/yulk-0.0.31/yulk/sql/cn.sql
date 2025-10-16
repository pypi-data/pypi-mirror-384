create schema IF NOT EXISTS cn; 
CREATE or replace MACRO cn.tab(name) AS TABLE (FROM read_parquet('http://file.yulk.net/cn/'|| name ||'.parquet'));

-- add ispos, istag,  of spacy 
CREATE or replace MACRO ispos(input) AS (SELECT input IN ('NOUN','ADJ','ADV','VERB','ADP','PROPN','PRON','X','DET','SPACE','SCONJ','INTJ','PUNCT','PART','CCONJ','NUM','SYM','AUX'));
CREATE or replace MACRO istag(input) AS (SELECT input IN ('JJ','JJR','RB','RBR','IN','CC','VBG','VBD','VBZ','VB','VBP','NN','NNS','DT','PRP','NNP','CD','TO','MD','PRP$','WDT','EX','RBS','JJS','SYM'));

CREATE or replace MACRO cn.get
(nameword) AS ( select v from cn.tab(str_split(nameword,':')[1]) where k = str_split(nameword,':')[-1] limit 1), 
(name, word) AS ( select v from cn.tab(name) where k = word limit 1) ;

CREATE or replace view cn.gram4 AS (FROM read_parquet('http://file.yulk.net/cn/gram4.parquet'));
