CREATE TABLE log_storage.onec_log_error(
       `timestamp` DateTime,
       `source_type` String,
       `host` String,
       `message` String,
       `err` String
) ENGINE = MergeTree() PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, source_type, host);