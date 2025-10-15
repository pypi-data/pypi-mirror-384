
-- for cikuu/mod/yulk/yulkinit.sql, 2025.10.11

INSTALL http_client FROM community;
LOAD http_client;
INSTALL spatial; -- add suport for st_read 
LOAD spatial;

--INSTALL webmacro FROM community;
--LOAD webmacro;
--SELECT load_macro_from_url('http://file.yulk.net/sql/util.sql'); 

-- http://yulk.net/xgetcloze?snt=It%20*%20ok.  
create or replace macro xget(name, val, fld:='snt') as ( select http_get('http://yulk.net/xget' || name || '?' || fld || '=' || val)->>'body' );  -- return varchar/jsonstr

-- http://yulk.net/xgetcloze?snt=It%20*%20ok.&topk=20  | select http_get('http://yulk.net/xgetcloze?snt=It * ok.&topk=20')->>'body'
create or replace macro cloze(snt, topk:=10) AS TABLE (
with t as  ( select http_get('http://yulk.net/xgetcloze?snt=' || snt || '&topk=' || topk)->>'body' as jsonstr ) 
select x.* from ( SELECT value::struct(word varchar, score float) x FROM t, json_each(jsonstr) )
);  -- from cloze('It * ok.') 
create or replace macro clozemap(snt, topk:=10) AS (select http_get('http://yulk.net/xgetcloze?snt=' || snt || '&topk=' || topk)->>'body' as jsonstr ); 
create or replace macro cloze(snt, topk:=10) AS (select map_from_entries (clozemap(snt, topk:=topk)::JSON::struct(word varchar, score float)[]) v ); 

create or replace macro paraphrase(snt) AS TABLE (  --select xget('paraphrase', 'it is useful.')
with t as ( select xget('paraphrase', snt) jsonstr )
select x.* from ( SELECT value::struct(id int, snt varchar) x FROM t, json_each(jsonstr) )
);  -- from paraphrase('it is useful.')  select *, cola(snt) from paraphrase('it is useful.')

create or replace macro cola(snt) as ( select xget('cola',snt) );
create or replace macro enzh(snt) as ( select element_at( xget('enzh',snt)::JSON::map(varchar, varchar), snt)[1] ); --select enzh('It is great.') 
create or replace macro segchs(snt) as ( select (http_get('http://yulk.net/segchs~'||snt)->>'body')::varchar[] ); 

create schema IF NOT EXISTS en; 
create schema IF NOT EXISTS cn; 
-- assuming dobjnv ( key, label, cn, en, keyness) exists 
--CREATE OR REPLACE VIEW en.dobjnv AS (SELECT key, label, en AS cnt, keyness FROM dobjnv WHERE en > 0 ORDER BY cnt desc);
--CREATE OR REPLACE VIEW cn.dobjnv AS (SELECT key, label, cn AS cnt, keyness FROM dobjnv WHERE cn > 0 ORDER BY cnt desc);

-- 15 seconds needed of following lines
--create OR REPLACE view spellerr as (from read_parquet('http://file.yulk.net/yulk/parkv/spellerr.parquet'));
--create OR REPLACE view gramcnt as (from read_parquet('http://file.yulk.net/yulk/parkv/gramcnt.parquet'));
--create OR REPLACE view gramtag as (from read_parquet('http://file.yulk.net/yulk/parkv/gramtag.parquet'));
--create OR REPLACE view snt as (from read_parquet('http://file.yulk.net/yulk/parkv/snt.parquet'));
--create OR REPLACE view wordsim as (from read_parquet('http://file.yulk.net/yulk/parkv/wordsim.parquet'));
--create OR REPLACE view vec as (from read_parquet('http://file.yulk.net/yulk/parkv/vec.parquet'));
