-- independent of nothing else, 2025.2.25

CREATE or replace MACRO file_exists(filepath) AS ( EXISTS (from glob(filepath) limit 1) ); --/yulk/hub/parkv/eclist.parquet

CREATE or replace MACRO isalpha(w) AS (SELECT regexp_matches(w, '^[a-zA-Z]+$'));
CREATE or replace MACRO islower(w) AS (SELECT regexp_matches(w, '^[a-z]+$'));
CREATE or replace MACRO isupper(w) AS (SELECT regexp_matches(w, '^[A-Z]+$'));

CREATE or replace MACRO likely(a,b,c,d) AS (round(if( a/c > b/d,  a * log(a*(c+d)/(c*(a+b))) +    b * log(b*(c+d)/(d*(a+b))), -  a * log(a*(c+d)/(c*(a+b)))  -  b * log(b*(c+d)/(d*(a+b))) ),1) );
CREATE or replace MACRO likelihood(a,b,c,d) AS (round(if( a/c > b/d,  a * log(a*(c+d)/(c*(a+b))) +    b * log(b*(c+d)/(d*(a+b))), -  a * log(a*(c+d)/(c*(a+b)))  -  b * log(b*(c+d)/(d*(a+b))) ),1) );
CREATE or replace MACRO logdice(common, cnt1, cnt2) AS ( round(14 + log( 2 * common / (cnt1 + cnt2 )), 2) );
CREATE or replace MACRO loglike(a,b,c,d) AS (round(if( if(a,a,0.001)/c > if(b,b,0.001)/d,  if(a,a,0.001) * log(if(a,a,0.001)*(c+d)/(c*(if(a,a,0.001)+if(b,b,0.001)))) +    if(b,b,0.001) * log(if(b,b,0.001)*(c+d)/(d*(if(a,a,0.001)+if(b,b,0.001)))), -  if(a,a,0.001) * log(if(a,a,0.001)*(c+d)/(c*(if(a,a,0.001)+if(b,b,0.001))))  -  if(b,b,0.001) * log(if(b,b,0.001)*(c+d)/(d*(if(a,a,0.001)+if(b,b,0.001)))) ),2) );
CREATE or replace MACRO head(s, sepa:=':') AS (substr(s, 1, (strpos(s, sepa))-1));
CREATE or replace MACRO itemi(s, i, sepa:=':') AS ( select str_split(s, sepa)[i+1] );
CREATE or replace MACRO tail(s, sepa:=':') AS ( select str_split(s, sepa)[-1] );
CREATE or replace MACRO leftof(s, sepa:=':') AS ( select str_split(s, sepa)[1] );
CREATE or replace MACRO rightof(s, sepa:=':') AS ( select str_split(s, sepa)[-1] );
CREATE or replace MACRO among(snt, l, r) AS ( select str_split (str_split(snt, l)[-1], r)[1] );
CREATE or replace MACRO chunk(snt, sepa, idx) AS ( select str_split(snt, sepa)[idx] );
CREATE or replace MACRO mapsi(input) AS ( select map(list(x[1]), list(x[2]::int32)) from ( select unnest( [ string_split(pair,':') for pair in string_split(input,',')]) x ) );
-- select mapsi('mari:686,print:94')
CREATE or replace MACRO lastlem(s, sepa:='_') AS ( select str_split(s, sepa)[-1] );
CREATE or replace MACRO firstlem(s, sepa:='_') AS ( select str_split( str_split(s,' ')[1], sepa)[-1] );

-- add ispos, istag,  of spacy 
CREATE or replace MACRO ispos(input) AS (SELECT input IN ('NOUN','ADJ','ADV','VERB','ADP','PROPN','PRON','X','DET','SPACE','SCONJ','INTJ','PUNCT','PART','CCONJ','NUM','SYM','AUX'));
CREATE or replace MACRO istag(input) AS (SELECT input IN ('JJ','JJR','RB','RBR','IN','CC','VBG','VBD','VBZ','VB','VBP','NN','NNS','DT','PRP','NNP','CD','TO','MD','PRP$','WDT','EX','RBS','JJS','SYM'));

set VARIABLE map1 = map {'commercial':1,'wide':1,'popular':1,'much':1,'abundant':1,'beneficial':1,'reasonal':1,'helpful':1,'incredible':1,'excess':1,'careful':1,'creative':1,'clever':1,'significant':1,'scientific':1,'different':1,'sensible':26,'effective':10,'rational':10,'wise':9,'reasonable':7,'pleasurable':6,'appropriate':4,'efficient':4,'correct':4,'practical':4,'rosy':4,'promising':3,'active':3,'enough':3,'bad':3,'maximum':3,'full':3252,'good':1772,'well':223,'most':95,'positive':49,'great':43,'proper':36,'more':26,'goood':1,'valuable':1,'fancy':1,'less':1,'wrong':1,'expert':1,'legitimate':1,'major':1,'perfect':3,'big':2,'flexible':2,'free':2,'heavy':1,'cautious':1,'prudent':1,'fun':1,'economical':1,'complete':1,'further':1,'moderate':1,'apt':1,'current':1,'poor':1,'sufficient':1};
set VARIABLE map2 = map {'good':53,'full':44,'maximum':22,'well':18,'extensive':16,'more':11,'regular':9,'little':8,'great':8,'heavy':8,'considerable':6,'proper':5,'effective':4,'much':4,'frequent':4,'efficient':3,'optimum':3,'most':2,'excellent':2,'practical':2,'least':2,'brilliant':2,'sufficient':1,'special':1,'essential':1,'wide':1,'substantial':1,'satisfactory':1,'different':1,'uncompromising':1,'immediate':1,'worthwhile':1,'varied':1,'extraordinary':1,'occasional':1,'ingenious':1,'political':1,'limited':1,'heavy-handed':1,'careful':1,'positive':1,'productive':1,'intelligent':1,'active':1,'infrequent':1,'concrete':1,'devastating':1,'first':1,'ample':1,'infinite':1,'liberal':1,'wise':1,'systematic':1,'open':1};
--CREATE or replace MACRO mapkn(map1,map2) AS TABLE ( select distinct k word, COALESCE(map1[k],0) cnt1, COALESCE(map2[k],0) cnt2, sum(cnt1) over() as sum1, sum(cnt2) over() as sum2, loglike(cnt1,cnt2,sum1, sum2) kn  from ( select unnest(map_keys(map1) || map_keys(map2)) k) order by kn) ;
CREATE or replace MACRO mapjoin(map1,map2) AS TABLE ( select distinct k word, COALESCE(map1[k],0) cnt1, COALESCE(map2[k],0) cnt2 from ( select unnest(map_keys(map1) || map_keys(map2)) k) );
CREATE or replace MACRO mapkn(map1,map2) AS TABLE ( select *, sum(cnt1) over() as sum1, sum(cnt2) over() as sum2, loglike(cnt1,cnt2,sum1, sum2) kn, ROUND(100*cnt1/sum1,2) AS perc1, ROUND(100*cnt2/sum2,2) AS perc2 FROM mapjoin(map1,map2)  order by kn) ;
-- from  mapkn(get('kv','open:dobjvn','cn'),get('kv','open:dobjvn','en'));
-- from mapkn(dobjvn('open','cn') , dobjvn('open','en')  )

--select lemattr('open','dobjvn','en') , defined in nlp.sql
--CREATE or replace MACRO lemattrkn(lem, attr, src, tgt) AS TABLE (select *, sum(cnt1) over() as sum1, sum(cnt2) over() as sum2, loglike(cnt1,cnt2,sum1, sum2) kn from mapjoin(lemattr(lem, attr, src) , lemattr(lem,attr, tgt) ) order by kn );

CREATE or replace MACRO swap(s) AS (s[0:-3] || s[-1] || s[-2]) ;
--CREATE or replace MACRO dobjnv(lem, db:='en') AS TABLE ( SELECT substr(s, (strpos(s, ':') + 1)) word ,i cnt from ksi where cp =db and  k = len and s like 'dobjvn:%' order by cnt desc);
--CREATE or replace MACRO geti(_k, _s, db:='en') AS ( select first(i) from ksi where cp= db and k=_k and s = _s limit 1 );

CREATE or replace MACRO itemi(s, i, sepa:=':') AS ( select str_split(s, sepa)[i+1] );
CREATE or replace MACRO lastword(s, sepa) AS ( select str_split(s, sepa)[-1] ), (s) AS ( select str_split(s, ' ')[-1] ); -- last word of the chunk
CREATE or replace MACRO leftof(s, sepa:=':') AS ( select str_split(s, sepa)[1] );
CREATE or replace MACRO rightof(s, sepa:=':') AS ( select str_split(s, sepa)[-1] );
CREATE or replace MACRO tc(s) AS ( len(string_split(s,' ')) );;
create or replace macro cosine(vec1, vec2) as ( select list_cosine_similarity(vec1::json::float[], vec2::json::float[]) );

CREATE or replace MACRO sortmap(map1) AS (select map(list(key), list(value)) from ( select x.key as key, x.value::int as value from (select unnest(map_entries(map1)) x) order by value desc) );
--select  sortmap( map([100, 5], [42, 43]) ) -> {5=43, 100=42}
CREATE or replace MACRO unmap(map1) AS TABLE ( select x.* from ( select unnest( map_entries(map1)) x) );
-- from unmap( map([100, 5], [42, 43]) ), added 2025.3.4

CREATE or replace MACRO shortpos(s) AS ( map {'NOUN':'n', 'VERB':'v', 'ADP':'p', 'DET':'e', 'PRON':'r', 'ADJ':'a', 'AUX':'x', 'ADV':'d','CCONJ':'c', 'PART':'t','SCONJ':'s', 'INTJ':'i','PUNCT':'u','PROPN':'O', 'VBG':'g', 'VBN':'b','TO':'o'}[s] );
CREATE or replace MACRO latter(s, sepa:=':') AS (substr(s, (strpos(s, sepa)+1)));

CREATE or REPLACE MACRO ifelse(a, b, c) AS CASE WHEN a THEN b ELSE c END;
CREATE or replace MACRO vtype(m) AS ( SELECT typeof(m) );
--select vtype(MAP {'one':1});
CREATE or replace MACRO sumsi(m) AS ( list_aggregate(map_values(m),'sum') );
--select sumsi(map([100, 5], [42, 43]));

CREATE or replace MACRO clean(snt) AS ( SELECT regexp_matches(snt, '^[a-zA-Z \.,\!\?\-''"]+$') );
-- select clean('It is ok. 123') 
CREATE or replace MACRO cleanx(snt) AS ( SELECT regexp_matches(snt, '^[0-9a-zA-Z \.,\!\%\?\-''"]+$') );

CREATE or replace MACRO highlex(snt, lex) AS ( SELECT regexp_replace( snt, '(?i)(\b'||lex||'\b)',  '<b>\1</b>') ) ;
-- select highlex('The quick brown Duck jumps over the lazy Dog.','duck')
-- SELECT regexp_replace('The quick brown Duck jumps over the lazy Dog.',  '(?i)(\bduck|over\b)',    '<b>\1</b>', 'g');

CREATE or replace MACRO prefix(s) AS (select array_to_string(string_split(s, ':')[1:-2], ':')); -- select upper('one:two:three') -> one:two

-- CREATE or replace MACRO eclist(input) AS ( SELECT v from eclist where k = input limit 1 );
-- CREATE or replace MACRO lexlem(input) AS ( SELECT v from lexlem where k = input limit 1 );
-- CREATE or replace MACRO lemlex(input) AS ( SELECT v from lemlex where k = input limit 1 );