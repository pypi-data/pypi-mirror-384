-- last update: 2025.8.23 ;      select * from 'http://file.yulk.net/yulk/en/termmap.parquet' where k = 'open:dobjvn' 
create schema IF NOT EXISTS en; 
CREATE or replace MACRO en.tab(name) AS TABLE (FROM read_parquet('http://file.yulk.net/en/'|| name ||'.parquet'));

-- add ispos, istag,  of spacy 
CREATE or replace MACRO ispos(input) AS (SELECT input IN ('NOUN','ADJ','ADV','VERB','ADP','PROPN','PRON','X','DET','SPACE','SCONJ','INTJ','PUNCT','PART','CCONJ','NUM','SYM','AUX'));
CREATE or replace MACRO istag(input) AS (SELECT input IN ('JJ','JJR','RB','RBR','IN','CC','VBG','VBD','VBZ','VB','VBP','NN','NNS','DT','PRP','NNP','CD','TO','MD','PRP$','WDT','EX','RBS','JJS','SYM'));

create OR REPLACE view en.tok AS from en.tab('tok');
create OR REPLACE view en.snt AS from en.tab('snt');
create OR REPLACE view en.xtok AS from en.tab('xtok');
create OR REPLACE view en.attr AS from en.tab('attr');
create OR REPLACE view en.frame AS from en.tab('frame');
create OR REPLACE view en.term AS from en.tab('termmap');
create OR REPLACE view en.termmap AS from en.tab('termmap');
CREATE or replace view en.svo AS from en.tab('svo') ;
CREATE or replace view en.vpx AS from en.tab('vpx') ;
CREATE or replace view en.vpat AS from en.tab('vpat') ;
create OR REPLACE view en.tokf AS from en.tab('tokf');

create OR REPLACE view en.gram1 AS FROM en.tab('gram1');
create OR REPLACE view en.gram2 AS FROM en.tab('gram2');
create OR REPLACE view en.gram3 AS FROM en.tab('gram3');
create OR REPLACE view en.gram4 AS FROM en.tab('gram4');
create OR REPLACE view en.gram5 AS FROM en.tab('gram5');
create OR REPLACE view en.xgram2 AS FROM en.tab('xgram2');
create OR REPLACE view en.xgram3 AS FROM en.tab('xgram3');
create OR REPLACE view en.xgram4 AS FROM en.tab('xgram4');
create OR REPLACE view en.xgram5 AS FROM en.tab('xgram5');

create OR REPLACE view en.formal AS from en.tab('formal');
CREATE or replace MACRO en.formal(input) AS ( select v from en.tab('formal') where k = input limit 1)  ;
create OR REPLACE view en.read AS from en.tab('read');
CREATE or replace MACRO en.read(input) AS ( select v from  en.tab('read') where k = input limit 1)  ;
-- select en.read('0000129b-6989-dd29-077f-9c4549691274')

CREATE or replace MACRO en.get
(nameword) AS ( select v from en.tab(str_split(nameword,':')[1]) where k = str_split(nameword,':')[-1] limit 1), 
(name, word) AS ( select v from en.tab(name) where k = word limit 1) ;

CREATE or replace macro en.gram2(arr) AS table(
    SELECT * FROM en.gram2 where 
	case when ispos(arr[1]) then pos1 =arr[1] when istag(arr[1]) then tag1 =arr[1] else lem1 = arr[1] END 
	and  
    case when ispos(arr[2]) then pos2 =arr[2] when istag(arr[2]) then tag2 =arr[2] else lem2 = arr[2] end
    order by cnt desc 
);
--from en.gram2(string_split('as ADJ',' ') )
CREATE or replace macro en.gram3(arr) AS table(
    SELECT * FROM en.gram3 where 
	case when ispos(arr[1]) then pos1 =arr[1] when istag(arr[1]) then tag1 =arr[1] else lem1 = arr[1] END 
	and  
    case when ispos(arr[2]) then pos2 =arr[2] when istag(arr[2]) then tag2 =arr[2] else lem2 = arr[2] end
	and  
    case when ispos(arr[3]) then pos3 =arr[3] when istag(arr[3]) then tag3 =arr[3] else lem3 = arr[3] end
    order by cnt desc 
);
CREATE or replace macro en.gram4(arr) AS table(
    SELECT * FROM en.gram4 where 
	case when ispos(arr[1]) then pos1 =arr[1] when istag(arr[1]) then tag1 =arr[1] else lem1 = arr[1] END 
	and  
    case when ispos(arr[2]) then pos2 =arr[2] when istag(arr[2]) then tag2 =arr[2] else lem2 = arr[2] end
	and  
    case when ispos(arr[3]) then pos3 =arr[3] when istag(arr[3]) then tag3 =arr[3] else lem3 = arr[3] end
	and  
    case when ispos(arr[4]) then pos4 =arr[4] when istag(arr[4]) then tag4 =arr[4] else lem4 = arr[4] end
    order by cnt desc 
);
CREATE or replace macro en.gram5(arr) AS table(
    SELECT * FROM en.gram5 where 
	case when ispos(arr[1]) then pos1 =arr[1] when istag(arr[1]) then tag1 =arr[1] else lem1 = arr[1] END 
	and  
    case when ispos(arr[2]) then pos2 =arr[2] when istag(arr[2]) then tag2 =arr[2] else lem2 = arr[2] end
	and  
    case when ispos(arr[3]) then pos3 =arr[3] when istag(arr[3]) then tag3 =arr[3] else lem3 = arr[3] end
	and  
    case when ispos(arr[4]) then pos4 =arr[4] when istag(arr[4]) then tag4 =arr[4] else lem4 = arr[4] END
	and  
    case when ispos(arr[5]) then pos5 =arr[5] when istag(arr[5]) then tag5 =arr[5] else lem5 = arr[5] end
    order by cnt desc 
);

CREATE or replace MACRO en.pos (input) AS ( select v from en.termmap where k = concat(input, ':POS') limit 1)  ;
CREATE or replace MACRO en.pos (input) AS table ( select x.* from (select unnest(map_entries(v)) x from en.termmap where k = concat(input, ':POS')) );
CREATE or replace MACRO en.lex (input) AS ( select v from en.termmap where k = concat(input, ':LEX') limit 1)  ;
CREATE or replace MACRO en.lex (input) AS table ( select x.* from (select unnest(map_entries(v)) x from en.termmap where k = concat(input, ':LEX')) );
CREATE or replace MACRO en.dobjvn (input) AS ( select v from en.termmap where k = concat(input, ':dobjvn') limit 1)  ;
CREATE or replace MACRO en.dobjvn (input) AS table ( select x.* from (select unnest(map_entries(v)) x from en.termmap where k = concat(input, ':dobjvn')) );
CREATE or replace MACRO en.dobjnv (input) AS ( select v from en.termmap where k = concat(input, ':dobjnv') limit 1)  ;
CREATE or replace MACRO en.dobjnv (input) AS table ( select x.* from (select unnest(map_entries(v)) x from en.termmap where k = concat(input, ':dobjnv')) );

-- search vpats of the given frame, ie : charge.05 , added 2025.6.23
CREATE or replace MACRO en.framevpats(input) AS (
with t as ( 
select vpat ,count(*) cnt from ( ( select unnest(v) vpat from en.vpat where k in ( select k from en.frame where contains(v, input ) ) ) ) 
where vpat like str_split(input,'.')[1] || ':%' 
group by vpat 
)
select map(list(vpat order by cnt desc), list(cnt  order by cnt desc)) from t 
);
--select en.framevpats('charge.05') => {"charge:be VBN with":50,"charge:V N":38,}

-- co-occur lemma
CREATE or replace MACRO en.lemmaco(input) AS table(
select lem, pos, count(*) cnt from en.tok where 
pos in ('NOUN','VERB','ADJ','ADV') and lem != input and sid in (select distinct sid from en.tok where lem = input)
group by lem,pos 
order by cnt desc ) ;

--CREATE or replace macro en.gram2hyb(input) AS table(
--  WITH parts AS ( SELECT string_split(trim(input), ' ') AS arr)
--    SELECT * FROM en.gram2 a,parts where 
--	case when ispos(arr[1]) then a.pos =arr[1] when istag(arr[1]) then a.tag =arr[1] else a.lem = arr[1] END 
--	and  case when ispos(arr[2]) then b.pos =arr[2] when istag(arr[2]) then b.tag =arr[2] else b.lem = arr[2] end
--);

--select lem_1, count(*) cnt from gram2hyb('as ADJ') group by lem_1 
CREATE or replace macro gram3hyb(input, cp:='en') AS table(
    WITH parts AS ( SELECT string_split(trim(input), ' ') AS arr)
    SELECT * FROM query_table(cp ||'.gram3'),parts where  
	case when arr[1] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos =arr[1] when arr[1] IN ('JJ','RB','NN','NNS','VB') then tag =arr[1] else lem = arr[1] END 
	and  case when arr[2] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_1 =arr[2] when arr[2] IN ('JJ','RB','NN','NNS','VB') then tag_1 =arr[2] else lem_1 = arr[2] end
	and  case when arr[3] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_2 =arr[3] when arr[3] IN ('JJ','RB','NN','NNS','VB') then tag_2 =arr[3] else lem_2 = arr[3] end
);
CREATE or replace macro gram4hyb(input, cp:='en') AS table(
    WITH parts AS ( SELECT string_split(trim(input), ' ') AS arr)
    SELECT * FROM query_table(cp ||'.gram4'),parts where  
	case when arr[1] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos =arr[1] when arr[1] IN ('JJ','RB','NN','NNS','VB') then tag =arr[1] else lem = arr[1] END 
	and  case when arr[2] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_1 =arr[2] when arr[2] IN ('JJ','RB','NN','NNS','VB') then tag_1 =arr[2] else lem_1 = arr[2] end
	and  case when arr[3] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_2 =arr[3] when arr[3] IN ('JJ','RB','NN','NNS','VB') then tag_2 =arr[3] else lem_2 = arr[3] END
	and  case when arr[4] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_3 =arr[4] when arr[4] IN ('JJ','RB','NN','NNS','VB') then tag_3 =arr[4] else lem_3 = arr[4] end
);
-- select lem_1, count(*) cnt from gram4hyb('make ADJ use of') group by lem_1 

CREATE or replace MACRO en.lemcnt(input) AS ( ifnull( (select count(*) from en.tok where lem = input), 0) );
CREATE or replace MACRO en.verbcnt(input) AS ( ifnull( (select count(*) from en.tok where lem = input AND pos ='VERB'), 0) ); 
CREATE or replace MACRO en.nouncnt(input) AS ( ifnull( (select count(*) from en.tok where lem = input AND pos ='NOUN'), 0) );
CREATE or replace MACRO en.adjcnt(input) AS ( ifnull( (select count(*) from en.tok where lem = input AND pos ='ADJ'), 0) );
CREATE or replace MACRO en.advcnt(input) AS ( ifnull( (select count(*) from en.tok where lem = input AND pos ='ADV'), 0) );

CREATE or replace MACRO en.verbsum(input) AS ( SELECT v['_sum'] from en.termmap where k = input || ':VERB' );

CREATE or replace MACRO en.framecnt(input) AS ( ifnull( (select count(*) from en.frame where contains(v, input)), 0) );
-- select *, framecnt(frame, db:='cn') cn , framecnt(frame, db:='en') en, framecnt(frame, db:='spok') spok from frame.parquet where lem= 'charge' 


