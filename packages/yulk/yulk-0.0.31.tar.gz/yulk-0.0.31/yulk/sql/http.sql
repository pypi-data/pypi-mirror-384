-- last update: 2025.8.23, cp from duck/initsql/nlp.sql 
INSTALL http_client FROM community;
LOAD http_client;

-- http://yulk.net/xgetcloze?snt=It%20*%20ok.  
create or replace macro xget(name, val, fld:='snt') as ( select http_get('http://yulk.net/xget' || name || '?' || fld || '=' || val)->>'body' );  -- return varchar/jsonstr
create or replace macro xtext(name, val) AS ( select xget(name, val, fld:='text') ); -- http://yulk.net/xgetdsk?text=it+is+ok.
create or replace macro parseto(snt, chain) as ( select http_get('http://yulk.net/xgetparse?snt='|| snt || '&chain=' || chain)->>'body' ); -- lemmas/phrase/chunkex

-- select parseto('I pay attention to the box.','chunkex') | {"tag":"JJ","index":1,"pattern":"pay JJ attention to"}
create or replace macro chunkex(snt) AS TABLE (
with t as ( select parseto(snt,'chunkex') jsonstr )
select x.* from ( SELECT value::struct(tag varchar, index int, pattern varchar) x FROM t, json_each(jsonstr) )
);  -- select * from chunkex('I pay attention to the box.')  | select *, gramtag(pattern) as cand from chunkex('I pay attention to the box.') 

-- http://yulk.net/xgetcloze?snt=It%20*%20ok.&topk=20  | select http_get('http://yulk.net/xgetcloze?snt=It * ok.&topk=20')->>'body'
create or replace macro cloze(snt, topk:=10) AS TABLE (
with t as  ( select http_get('http://yulk.net/xgetcloze?snt=' || snt || '&topk=' || topk)->>'body' as jsonstr ) 
select x.* from ( SELECT value::struct(word varchar, score float) x FROM t, json_each(jsonstr) )
);  -- from cloze('It * ok.') 
create or replace macro clozemap(snt, topk:=10) AS (select http_get('http://yulk.net/xgetcloze?snt=' || snt || '&topk=' || topk)->>'body' as jsonstr ); 
create or replace macro cloze(snt, topk:=10) AS (select map_from_entries (clozemap(snt, topk:=topk)::JSON::struct(word varchar, score float)[]) v ); 

-- select xget('parse', 'It is ok.') -- [{"i":0,"lex":"It","lem":"it","pos":"PRON","p":"r","tag":"PRP","textws":"It ","dep":"nsubj","headi":1,"glem":"be","gpos":"AUX","gp":"x","gtag":"VBZ"}
create or replace macro parse(snt) AS ( select xget('parse', snt) );
create or replace macro parse(snt) AS TABLE (
with t as ( select xget('parse', snt) jsonstr )
select x.* from ( SELECT value::struct(i int, lex varchar, lem varchar, pos varchar, p varchar, tag varchar, textws varchar, dep varchar, headi int, glem varchar, gpos varchar, gp varchar, gtag varchar) x FROM t, json_each(jsonstr) )
);  -- from parse('It is ok.') 

create or replace macro paraphrase(snt) AS TABLE (  --select xget('paraphrase', 'it is useful.')
with t as ( select xget('paraphrase', snt) jsonstr )
select x.* from ( SELECT value::struct(id int, snt varchar) x FROM t, json_each(jsonstr) )
);  -- from paraphrase('it is useful.')  select *, cola(snt) from paraphrase('it is useful.')

create or replace macro gec(snt) AS TABLE (
with t as ( select xget('gec', snt) jsonstr )
SELECT key, trim(value,'"') as value FROM t, json_each(jsonstr) 
);  --from gec('it are ok.|She has ready')  
create or replace macro gec(snt) AS (
with t as ( select xget('gec', snt) jsonstr )
SELECT trim(value,'"') as value FROM t, json_each(jsonstr) 
); -- select gec('it are ok.')  

create or replace macro aes(text) AS TABLE (
with t as ( select xtext('aes', text) jsonstr )
SELECT key, value FROM t, json_each(jsonstr) 
);   --from aes('it are ok. She has ready')  

create or replace macro dsk(text) AS TABLE (
with t as ( select xtext('dsk', text) jsonstr )
SELECT key, value FROM t, json_each(jsonstr) 
);   -- from dsk('it are ok. She has ready')    (snt,doc,kw,info -> ) 
create or replace macro dskdim(text) AS TABLE (
with t as (  select value as dims from dsk(text)  where key = 'doc' )
select key, value from t, json_each(t.dims)
); -- from dskdim('It is ok.') 
create or replace macro dskinfo(text) AS TABLE (
with t as (  select value as val from dsk(text)  where key = 'info' )
select key, value from t, json_each(t.val)
) ; --from dskinfo('It is ok.') 
create or replace macro dsksnt(text) AS TABLE (
with t as ( select value as val from dsk(text)  where key = 'snt' )
select key, value->'meta'->>'snt' snt, value from t, json_each(t.val)
) ; -- from dsksnt('It is ok. She has ready.') 
create or replace macro dskfeedback(text) AS TABLE (
with t as ( select key as sid, snt, value->'feedback' fd from dsksnt(text)  )
select sid, snt, key as kp, value from t, json_each(t.fd)
) ; --from dskfeedback('It is ok. She has ready.') 

-- last update : 2025.6.3    from parse('It is ok.')    " NOT work 
--create or replace macro parse(snt) AS ((http_get('http://yulk.net/parse~'||snt)->>'body')::JSON); -- select parse(hget('code:text','skills')), table function CANNOT contain subqueries
--create or replace macro parse(snt) as table ( select x.* from (select unnest((http_get('http://yulk.net/parse~'||snt)->>'body')::JSON::STRUCT(i int, lex varchar, lem varchar, pos varchar, tag varchar, dep varchar, headi int,textws varchar, nplen int, sntlen int, sid int)[]) x));
create or replace macro parsex(snt) as table (select x.* from (select unnest((http_get('http://yulk.net/parse~'||snt||'?mergenp=1&subtree=1')->>'body')::JSON::STRUCT(i int, lex varchar, lem varchar, pos varchar, tag varchar, dep varchar, headi int,textws varchar, nplen int, sntlen int, sid int,subtree int[], lefts int[], rights int[])[]) x));
create or replace macro tokenize(txt) as table  (SELECT unnest( regexp_extract_all(txt, '[a-zA-Z\-]+')) word);
create or replace macro lexcnt(txt) as table  (SELECT LOWER(word) lex, COUNT(*) cnt FROM (SELECT unnest( regexp_extract_all(txt, '[a-zA-Z\-]+')) word) GROUP BY lex ORDER BY cnt desc) ;
--from lexcnt('The quick fox jumped over the quick dog.')  select * from lexcnt('The quick fox jumped over the quick dog.') where isword(lex) = true and stop(lex) = false 
create or replace macro hget(k,f) as ( select http_get('http://yulk.net/kvr.hget-'||k||','||f)->>'body' ); --select hget('code:text','skills')
create or replace macro htext(name) as ( select http_get('http://yulk.net/kvr.hget-code:text,'||name)->>'body' );--select htext('skills')   -- http://yulk.net/kvr.hget~code:text,skills

-- http://yulk.net/vecsim~closing
create or replace macro vecsim(input) AS (select (http_get('http://yulk.net/vecsim~'||input)->>'body')::JSON::map(varchar, float));
create or replace macro vecsim(input) AS table ( select x.* from (select unnest(map_entries(vecsim(input))) x ) );
--from vecsim('skills') 

-- http://yulk.net/products~on%7Cin%7Cat%20the%20train
create or replace macro products (hyb) AS table (select unnest((http_get('http://yulk.net/products~'||hyb)->>'body')::JSON::varchar[]) cand);
-- http://yulk.net/gramc~as%20soon  select cand, gramc(cand) from products('on|in the table') 
create or replace macro gramc (chk) AS (select (http_get('http://yulk.net/gramc~'||chk)->>'body')::int) ;

-- select xget('frame', 'I return the hat.')  {"return.02":0.9633}
create or replace macro frame(snt) AS TABLE (
with t as ( select xget('frame', snt) jsonstr )
SELECT key, value FROM t, json_each(jsonstr) 
);   --from frame('I return the hat.')  

create or replace macro read(snt) as ( select xget('readability',snt) ); -- select read('It is ok.') -> 1.97
create or replace macro readability(snt) as ( select xget('readability',snt) );
create or replace macro sentiment(snt) as ( select xget('sentiment',snt)::JSON::struct(label varchar, score float) );
create or replace macro formality(snt) as ( select xget('formality',snt)::JSON::struct(label varchar, score float) );
create or replace macro formal(snt) as ( select xget('formality',snt)::JSON::struct(label varchar, score float) );
create or replace macro fluency(snt) as ( select xget('fluency',snt) );
create or replace macro cola(snt) as ( select xget('cola',snt) );
create or replace macro enzh(snt) as ( select element_at( xget('enzh',snt)::JSON::map(varchar, varchar), snt)[1] ); --select enzh('It is great.') 

--create or replace macro parse(snt) as table ( select * from read_json('http://cikuu.com:8180/parse.json?text=' || snt) ); 
create or replace macro parsezh(snt) as table ( select * from read_json('http://cikuu.com:8180/parsezh.json?text=' || snt) ) ;
create or replace macro segchs(snt) as ( select (http_get('http://yulk.net/segchs~'||snt)->>'body')::varchar[] ); -- http://yulk.net/segchs~%E6%88%91%E6%98%AF%E4%B8%AD%E5%9B%BD%E4%BA%BA%E3%80%82

create or replace macro loadtext(filename) as ( select http_get('http://yulk.net:8000/text/' || filename)->>'body');
--create or replace macro sntbr(txt) as TABLE (select unnest ( (http_get('http://cikuu.com:8180/sntbr.json?text='||txt)->>'body')::JSON::STRUCT(i int, off INT, snt VARCHAR, tc int)[], recursive := true));
create or replace macro sntbr(txt) as TABLE (select unnest ( (http_get('http://yulk.net/sntbr~'||txt)->>'body')::JSON::STRUCT(snt VARCHAR, i int, off INT,  tc int)[], recursive := true));
-- select * from sntbr( hget('text', 'skills') )

-- http://cikuu.com:8180/xget-nsp?snts=The%20fox%20jumped%20over%20the%20dog.|Justice%20delayed%20is%20justice%20denied.
create or replace macro nsp(snts) as TABLE (select unnest ( (http_get('http://yulk.net/xgetnsp?snts='||snts)->>'body')::JSON::STRUCT(i int, prev varchar, next VARCHAR, nsp float)[], recursive := true));
create or replace macro kenflue(snt) as ( SELECT (http_get('http://yulk.net/xgetkenflue?snt='||snt)->>'body'->'$[0]'->'flue')::float );

create or replace macro root(snt) as ( SELECT (http_get('http://cikuu.com:8180/meta?snt='||snt)->>'body'->>'root') );
create or replace macro tokens(snt) as ( SELECT (http_get('http://cikuu.com:8180/meta?snt='||snt)->>'body'->>'tokens') );
--create or replace macro np(snt) as ( SELECT (http_get('http://cikuu.com:8180/meta?snt='||snt)->>'body'->>'np') );  -- typeof = varchar, ["it","a box"]
create or replace macro content(snt) as ( SELECT (http_get('http://cikuu.com:8180/meta?snt='||snt)->>'body'->>'content') );
CREATE or replace MACRO content(snt) AS TABLE ( select unnest(   from_json( content(snt)::JSON, '["varchar"]') ) word );

create or replace macro textvec(snt) as ( select http_get('http://textvec.yulk.net/vec~' || snt)->>'body');
create or replace macro sntvec(snt) as ( select http_get('http://sbert.yulk.net/vec~' || snt)->>'body');

CREATE or replace MACRO veclike(snt, topk:=10) AS TABLE (select unnest ( (http_get('http://vecdic.yulk.net/veclike?q='||snt||'&topk=' || topk)->>'body')::JSON::STRUCT(snt varchar, distance float)[], recursive := true)); 
CREATE or replace MACRO vecmin(snt) AS (select http_get('http://vecdic.yulk.net/veclike?q='||snt||'&topk=1' )->>'body'->'$[0]'->'distance'); 
-- select vecmin('It is useful.') 
CREATE or replace MACRO gptdetect(txt) AS  (select http_get('http://yulk.net/xgetgptdetect?text='||txt)->>'body'->'data'->>'prob');  
--http://unmasker.yulk.net/unmasker-get?q=It%20is%20%5BMASK%5D.&model=nju&topk=10 | native, cnmid, cnuniv, blog,spok, sci,sino
CREATE or replace MACRO unmask(snt, model:='native', topk:=10) AS TABLE (select unnest ( (http_get('http://unmasker.yulk.net/unmasker-get?q='||REPLACE(snt,'*','[MASK]')||'&model='||model||'&topk='||topk)->>'body')::JSON::STRUCT(word VARCHAR, score float, snt varchar)[], recursive := true)); 
-- select * from unmask('It * ok.')
CREATE or replace MACRO unmaskmap(snt, model:='native', topk:=10) AS (select http_get('http://unmasker.yulk.net/unmasker-get?q='||REPLACE(snt,'*','[MASK]')||'&model='||model||'&topk='||topk)->>'body') ; 
create or replace macro unmask(snt, model:='native', topk:=10) AS ( select map( list(x.word), list(x.score)) from (select unnest( unmaskmap(snt, model:=model, topk:=topk)::JSON::struct(word varchar, score float, snt varchar)[]) x ) );
-- select unmask('It * ok.') 

-- http://gensim.yulk.net/gensim/most_similar_by_word?w=loneliness&topk=50
CREATE or replace MACRO wordsim(input,topk:=64) AS table (select unnest( (http_get('http://gensim.yulk.net/gensim/most_similar_by_word?w='||input||'&topk='||topk)->>'body')::JSON::STRUCT(word varchar, sim float)[], recursive := true));
CREATE or replace MACRO wordsim(input,topk:=64) AS (select MAP(ARRAY_AGG(word), ARRAY_AGG(sim)) from wordsim(input, topk:=topk)); 
--from wordsim('lonely')
create or replace macro wordvec(word) as ( select http_post('http://gensim.yulk.net/wordvec/vec',headers => MAP {'accept': 'application/json'}, params => [word] )->>'body'->word );
create or replace macro wordcos(word1, word2) as ( select list_cosine_similarity( cast(wordvec(word1) as float[300]), cast(wordvec(word2) as float[300]))  );

--CREATE or replace MACRO clause(snt) AS TABLE( select  unnest(clause(snt)::JSON::STRUCT(type varchar, prev varchar, prevpos varchar, cl varchar, next varchar, nextpos varchar, v varchar, gov varchar, govpos varchar)[], recursive := true) ) ;
create or replace macro wordcos(word1, word2) as ( select list_cosine_similarity( cast(wordvec(word1) as float[300]), cast(wordvec(word2) as float[300]))  );
create or replace macro sntcos(snt1, snt2) as (  select list_cosine_similarity( cast(sntvec(snt1) as float[384]), cast(sntvec(snt2) as float[384]))  );
create or replace macro textcos(snt1, snt2) as ( select list_cosine_similarity( cast(textvec(snt1) as float[1024]), cast(textvec(snt2) as float[1024])) );
--create or replace macro lemdis(word1, words) AS table ( select word, lexdis(word1, word) cos from (SELECT unnest(STRING_SPLIT(words,',')) word) order by cos desc );
--create or replace macro lemcos(word1, words) AS table ( select word, lexcos(word1, word) cos from (SELECT unnest(STRING_SPLIT(words,',')) word) order by cos desc );
--from lemcos('rule','habit,principle')

create or replace macro lemslex(lems) as ( select http_get('http://nlp.yulk.net/lemlex?lems='||lems)->>'body');
CREATE or replace MACRO highlems(snt, lems) AS ( SELECT regexp_replace( snt, '(?i)(\b'||lemslex(lems)||'\b)',  '<b>\1</b>', 'g') ) ;
-- select highlems('The quick brown Duck jumps over the lazy Dog.', 'jump:over')

-- for wordinsnt.sql,   SELECT list_intersect([1, 2, 3, 4], [3, 4, 5, 6]) AS intersection;
--create or replace macro lexlem(lex) AS (
--SELECT 
--    CASE 
--        WHEN EXISTS (SELECT * from glob('/yulk/hub/parkv/lexlem.parquet') limit 1) THEN (SELECT v FROM '/yulk/hub/parkv/lexlem.parquet' WHERE k = lex limit 1 )
--        ELSE hget('dic:lexlem', lex)
--    END 
--);

--create or replace macro eclist(lem) AS (
--SELECT 
--   CASE 
--        WHEN EXISTS (SELECT * from glob('/yulk/hub/parkv/eclist.parquet') limit 1) THEN (SELECT v FROM '/yulk/hub/parkv/eclist.parquet' WHERE k = lem limit 1 )
--        ELSE str_split(hget('dic:eclist', lem), ',') 
--    END 
--);

create or replace macro wordinsnt(lex, snt) AS TABLE (
with t as ( select lex, snt, lexlem(lex) as lem , enzh(snt) AS zhsnt),
t1 as ( select eclist(lem) AS eclist, segchs(zhsnt) AS words) 
select *, list_intersect(eclist, words) AS hit 
from t, t1 
);

