
------------------------
-- TEST: CHAT_HISTORY --
------------------------
SELECT * FROM chat_history order by session_id, chat_id ;
-- where session_id = 103

SELECT session_id, COUNT(*) FROM chat_history GROUP BY session_id;

-----------------------
-- TEST: STAT_METHOD --
-----------------------

SELECT * FROM stat_method;

SELECT
    id,
    name,
    method_information ->> 'name' as method_name,
    method_information ->> 'usage' as method_usage,
    method_information ->> 'description' as method_description,
    method_information ->> 'keyword' as method_keyword
FROM
  stat_method;