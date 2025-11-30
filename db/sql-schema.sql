
-------------------------
-- TABLE: CHAT_HISTORY --
-------------------------
CREATE TABLE chat_history
(
    session_id INT,
    chat_id    INT,
    role       VARCHAR(100)  NOT NULL,
    content    VARCHAR(2000) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, chat_id)
);

INSERT INTO chat_history(session_id, chat_id, role, content)
VALUES (1, 1, 'System', 'Test1'),
       (1, 2, 'User', 'Test2'),
       (1, 3, 'Assistant', 'Test3');

-- CREATE TABLE data_library ();
-- CREATE TABLE data_list ();
-- CREATE TABLE data_vars ();
-- CREATE TABLE data_param ();

------------------------
-- TABLE: STAT_METHOD --
------------------------
CREATE TABLE stat_method (
    id Int NOT NULL PRIMARY KEY,
    name VARCHAR(100),
    method_information JSONB,
    method_schema JSONB
);

INSERT INTO stat_method(id, name, method_information)
VALUES (1, 'MMRM', '{"name": "MMRM", "usage": "Efficacy", "description": "Mixed Model Repeated Measures across Visits (and subgroup)", "vartype": "continuous", "keyword": ["MMRM", "mixed", "repeated measures"]}'),
       (2, 'ANCOVA', '{"name": "ANCOVA", "usage": "Efficacy", "description": "Analysis of Covariance by Visit (and subgroup)", "vartype": "continuous", "keyword": ["ANCOVA", "ANOVA"]}'),
       (3, 'BINARY', '{"name": "BINARY", "usage": "Efficacy", "description": "Proportion of Response by Visit (and subgroup)", "vartype": "binary", "keyword": ["binary", "proportion"]}'),
       (4, 'TTE', '{"name": "TTE", "usage": "Efficacy", "description": "Time to Event (by subgroup) with Kaplan-Meier Quantiles and Cox Regression", "vartype": "time-to-event", "keyword": ["TTE", "time to event", "Kaplan-Meier", "Cox"]}');

-------------------------------
-- TABLE: STAT_METHOD_SCHEMA --
-------------------------------



-------------------------------
-- TABLE: STAT_METHOD_SCHEMA --
-------------------------------

CREATE TABLE stat_method_schema (
    id Int NOT NULL PRIMARY KEY,
    name VARCHAR(100),
    method_information JSONB
);