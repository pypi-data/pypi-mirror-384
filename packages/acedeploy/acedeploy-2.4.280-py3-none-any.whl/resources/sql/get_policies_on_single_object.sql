-- this information can only be accessed on a per-object level
SELECT
    POLICY_DB,
    POLICY_SCHEMA,
    POLICY_NAME,
    POLICY_KIND,
    REF_DATABASE_NAME,
    REF_SCHEMA_NAME,
    REF_ENTITY_NAME,
    REF_ENTITY_DOMAIN,
    REF_COLUMN_NAME,
    REF_ARG_COLUMN_NAMES
FROM TABLE(
    INFORMATION_SCHEMA.POLICY_REFERENCES(
        REF_ENTITY_NAME => '"{schema_name}"."{object_name}"',
        REF_ENTITY_DOMAIN => '{object_type}'
    )
);
