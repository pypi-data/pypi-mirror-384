-- last update: 2025.7.28 ;      ' en;', "'cn'",  ' cn.', '/cn/' ->  cn
create schema IF NOT EXISTS cn; 
CREATE or replace MACRO cn.tab(name) AS TABLE (FROM read_parquet('http://file.yulk.net/cn/'|| name ||'.parquet'));

-- add ispos, istag,  of spacy 
CREATE or replace MACRO ispos(input) AS (SELECT input IN ('NOUN','ADJ','ADV','VERB','ADP','PROPN','PRON','X','DET','SPACE','SCONJ','INTJ','PUNCT','PART','CCONJ','NUM','SYM','AUX'));
CREATE or replace MACRO istag(input) AS (SELECT input IN ('JJ','JJR','RB','RBR','IN','CC','VBG','VBD','VBZ','VB','VBP','NN','NNS','DT','PRP','NNP','CD','TO','MD','PRP$','WDT','EX','RBS','JJS','SYM'));

create OR REPLACE view cn.tok AS from cn.tab('tok');
create OR REPLACE view cn.snt AS from cn.tab('snt');
create OR REPLACE view cn.xtok AS from cn.tab('xtok');
create OR REPLACE view cn.attr AS from cn.tab('attr');
create OR REPLACE view cn.frame AS from cn.tab('frame');
create OR REPLACE view cn.term AS from cn.tab('termmap');
create OR REPLACE view cn.termmap AS from cn.tab('termmap');
create OR REPLACE view cn.formal AS from cn.tab('formal');
CREATE or replace view cn.svo AS from cn.tab('svo') ;
CREATE or replace view cn.vpx AS from cn.tab('vpx') ;
CREATE or replace view cn.vpat AS from cn.tab('vpat') ;
--create OR REPLACE view en.tokf AS from en.tab('tokf');

create OR REPLACE view cn.gram1 AS FROM cn.tab('gram1');
create OR REPLACE view cn.gram2 AS FROM cn.tab('gram2');
create OR REPLACE view cn.gram3 AS FROM cn.tab('gram3');
create OR REPLACE view cn.gram4 AS FROM cn.tab('gram4');
create OR REPLACE view cn.gram5 AS FROM cn.tab('gram5');
create OR REPLACE view cn.xgram2 AS FROM cn.tab('xgram2');
create OR REPLACE view cn.xgram3 AS FROM cn.tab('xgram3');
create OR REPLACE view cn.xgram4 AS FROM cn.tab('xgram4');
create OR REPLACE view cn.xgram5 AS FROM cn.tab('xgram5');

CREATE or replace MACRO cn.get
(nameword) AS ( select v from cn.tab(str_split(nameword,':')[1]) where k = str_split(nameword,':')[-1] limit 1), 
(name, word) AS ( select v from cn.tab(name) where k = word limit 1) ;

CREATE or replace macro cn.gram2(arr) AS table(
    SELECT * FROM cn.gram2 where 
	case when ispos(arr[1]) then pos1 =arr[1] when istag(arr[1]) then tag1 =arr[1] else lem1 = arr[1] END 
	and  
    case when ispos(arr[2]) then pos2 =arr[2] when istag(arr[2]) then tag2 =arr[2] else lem2 = arr[2] end
    order by cnt desc 
);
--from cn.gram2(string_split('as ADJ',' ') )
CREATE or replace macro cn.gram3(arr) AS table(
    SELECT * FROM cn.gram3 where 
	case when ispos(arr[1]) then pos1 =arr[1] when istag(arr[1]) then tag1 =arr[1] else lem1 = arr[1] END 
	and  
    case when ispos(arr[2]) then pos2 =arr[2] when istag(arr[2]) then tag2 =arr[2] else lem2 = arr[2] end
	and  
    case when ispos(arr[3]) then pos3 =arr[3] when istag(arr[3]) then tag3 =arr[3] else lem3 = arr[3] end
    order by cnt desc 
);
CREATE or replace macro cn.gram4(arr) AS table(
    SELECT * FROM cn.gram4 where 
	case when ispos(arr[1]) then pos1 =arr[1] when istag(arr[1]) then tag1 =arr[1] else lem1 = arr[1] END 
	and  
    case when ispos(arr[2]) then pos2 =arr[2] when istag(arr[2]) then tag2 =arr[2] else lem2 = arr[2] end
	and  
    case when ispos(arr[3]) then pos3 =arr[3] when istag(arr[3]) then tag3 =arr[3] else lem3 = arr[3] end
	and  
    case when ispos(arr[4]) then pos4 =arr[4] when istag(arr[4]) then tag4 =arr[4] else lem4 = arr[4] end
    order by cnt desc 
);
CREATE or replace macro cn.gram5(arr) AS table(
    SELECT * FROM cn.gram5 where 
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

--CREATE or replace macro cn.gramarr(arr) AS table( 
--	case 
--		when LEN(arr) = 2 then (FROM cn.gram2(arr))
--		when LEN(arr) = 3 then (FROM cn.gram3(arr))
--		when LEN(arr) = 4 then (FROM cn.gram4(arr))
--		when LEN(arr) = 5 then (FROM cn.gram5(arr))
--		ELSE (FROM cn.gram1(arr))
--	END 
--);

--CREATE or replace macro cn.gram(hyb) AS table( -- make ADJ use of
--    FROM cn.gramarr(string_split(trim(hyb), ' '))
--);

CREATE or replace MACRO cn.pos (input) AS ( select v from cn.termmap where k = concat(input, ':POS') limit 1)  ;
CREATE or replace MACRO cn.pos (input) AS table ( select x.* from (select unnest(map_entries(v)) x from cn.termmap where k = concat(input, ':POS')) );
CREATE or replace MACRO cn.lex (input) AS ( select v from cn.termmap where k = concat(input, ':LEX') limit 1)  ;
CREATE or replace MACRO cn.lex (input) AS table ( select x.* from (select unnest(map_entries(v)) x from cn.termmap where k = concat(input, ':LEX')) );
CREATE or replace MACRO cn.dobjvn (input) AS ( select v from cn.termmap where k = concat(input, ':dobjvn') limit 1)  ;
CREATE or replace MACRO cn.dobjvn (input) AS table ( select x.* from (select unnest(map_entries(v)) x from cn.termmap where k = concat(input, ':dobjvn')) );
CREATE or replace MACRO cn.dobjnv (input) AS ( select v from cn.termmap where k = concat(input, ':dobjnv') limit 1)  ;
CREATE or replace MACRO cn.dobjnv (input) AS table ( select x.* from (select unnest(map_entries(v)) x from cn.termmap where k = concat(input, ':dobjnv')) );

-- search vpats of the given frame, ie : charge.05 , added 2025.6.23
CREATE or replace MACRO cn.framevpats(input) AS (
with t as ( 
select vpat ,count(*) cnt from ( ( select unnest(v) vpat from cn.vpat where k in ( select k from cn.frame where contains(v, input ) ) ) ) 
where vpat like str_split(input,'.')[1] || ':%' 
group by vpat 
)
select map(list(vpat order by cnt desc), list(cnt  order by cnt desc)) from t 
);
--select cn.framevpats('charge.05') => {"charge:be VBN with":50,"charge:V N":38,}

-- co-occur lemma
CREATE or replace MACRO cn.lemmaco(input) AS table(
select lem, pos, count(*) cnt from cn.tok where 
pos in ('NOUN','VERB','ADJ','ADV') and lem != input and sid in (select distinct sid from cn.tok where lem = input)
group by lem,pos 
order by cnt desc ) ;

--CREATE or replace macro cn.gram2hyb(input) AS table(
--    WITH parts AS ( SELECT string_split(trim(input), ' ') AS arr)
--    SELECT * FROM cn.gram2 a,parts where 
--	case when ispos(arr[1]) then a.pos =arr[1] when istag(arr[1]) then a.tag =arr[1] else a.lem = arr[1] END 
--	and  case when ispos(arr[2]) then b.pos =arr[2] when istag(arr[2]) then b.tag =arr[2] else b.lem = arr[2] end
--);
--select lem_1, count(*) cnt from gram2hyb('as ADJ') group by lem_1 
CREATE or replace macro gram3hyb(input, cp:='cn') AS table(
    WITH parts AS ( SELECT string_split(trim(input), ' ') AS arr)
    SELECT * FROM query_table(cp ||'.gram3'),parts where  
	case when arr[1] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos =arr[1] when arr[1] IN ('JJ','RB','NN','NNS','VB') then tag =arr[1] else lem = arr[1] END 
	and  case when arr[2] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_1 =arr[2] when arr[2] IN ('JJ','RB','NN','NNS','VB') then tag_1 =arr[2] else lem_1 = arr[2] end
	and  case when arr[3] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_2 =arr[3] when arr[3] IN ('JJ','RB','NN','NNS','VB') then tag_2 =arr[3] else lem_2 = arr[3] end
);
CREATE or replace macro gram4hyb(input, cp:='cn') AS table(
    WITH parts AS ( SELECT string_split(trim(input), ' ') AS arr)
    SELECT * FROM query_table(cp ||'.gram4'),parts where  
	case when arr[1] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos =arr[1] when arr[1] IN ('JJ','RB','NN','NNS','VB') then tag =arr[1] else lem = arr[1] END 
	and  case when arr[2] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_1 =arr[2] when arr[2] IN ('JJ','RB','NN','NNS','VB') then tag_1 =arr[2] else lem_1 = arr[2] end
	and  case when arr[3] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_2 =arr[3] when arr[3] IN ('JJ','RB','NN','NNS','VB') then tag_2 =arr[3] else lem_2 = arr[3] END
	and  case when arr[4] IN ('ADJ','ADV','NOUN','VERB','ADP') then pos_3 =arr[4] when arr[4] IN ('JJ','RB','NN','NNS','VB') then tag_3 =arr[4] else lem_3 = arr[4] end
);
-- select lem_1, count(*) cnt from gram4hyb('make ADJ use of') group by lem_1 

CREATE or replace MACRO cn.lemcnt(input) AS ( ifnull( (select count(*) from cn.tok where lem = input), 0) );
CREATE or replace MACRO cn.verbcnt(input) AS ( ifnull( (select count(*) from cn.tok where lem = input AND pos ='VERB'), 0) ); 
CREATE or replace MACRO cn.nouncnt(input) AS ( ifnull( (select count(*) from cn.tok where lem = input AND pos ='NOUN'), 0) );
CREATE or replace MACRO cn.adjcnt(input) AS ( ifnull( (select count(*) from cn.tok where lem = input AND pos ='ADJ'), 0) );
CREATE or replace MACRO cn.advcnt(input) AS ( ifnull( (select count(*) from cn.tok where lem = input AND pos ='ADV'), 0) );

CREATE or replace MACRO cn.verbsum(input) AS ( SELECT v['_sum'] from cn.termmap where k = input || ':VERB' );

CREATE or replace MACRO cn.framecnt(input) AS ( ifnull( (select count(*) from cn.frame where contains(v, input)), 0) );
-- select *, framecnt(frame, db:='cn') cn , framecnt(frame, db:='cn') en, framecnt(frame, db:='spok') spok from frame.parquet where lem= 'charge' 

