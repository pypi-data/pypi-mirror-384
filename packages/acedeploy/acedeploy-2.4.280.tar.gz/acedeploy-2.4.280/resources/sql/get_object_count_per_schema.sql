SELECT y.SCHEMA_NAME, SUM(y.COUNT) AS COUNT FROM (
    SELECT
        x.SCHEMA_NAME,
        COUNT(x.SCHEMA_NAME) AS COUNT
    FROM (
            SELECT
                TABLE_SCHEMA AS SCHEMA_NAME
            FROM
                "{database_name}"."INFORMATION_SCHEMA"."TABLES"
        UNION ALL
            SELECT
                FUNCTION_SCHEMA AS SCHEMA_NAME
            FROM
                "{database_name}"."INFORMATION_SCHEMA"."FUNCTIONS"
        UNION ALL
            SELECT
                PROCEDURE_SCHEMA AS SCHEMA_NAME
            FROM
                "{database_name}"."INFORMATION_SCHEMA"."PROCEDURES"
        UNION ALL
            SELECT
                FILE_FORMAT_SCHEMA AS SCHEMA_NAME
            FROM
                "{database_name}"."INFORMATION_SCHEMA"."FILE_FORMATS"
        UNION ALL
            SELECT
                STAGE_SCHEMA AS SCHEMA_NAME
            FROM
                "{database_name}"."INFORMATION_SCHEMA"."STAGES"
        ) as x
    WHERE SCHEMA_NAME != 'INFORMATION_SCHEMA'
    GROUP BY x.SCHEMA_NAME
UNION ALL
    SELECT SCHEMA_NAME, 0 COUNT FROM "{database_name}"."INFORMATION_SCHEMA"."SCHEMATA" WHERE SCHEMA_NAME != 'INFORMATION_SCHEMA'
) as y
GROUP BY y.SCHEMA_NAME
ORDER BY COUNT DESC;
