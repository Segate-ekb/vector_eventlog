-- Это пример создания таблицы в КХ.

CREATE DATABASE IF NOT EXISTS ch_test1_base;

CREATE TABLE IF NOT EXISTS ch_test1_base.eventlog_error(
   `timestamp` DateTime,
   `source_type` String,
   `host` String,
   `message` String,
   `component_id` String,
   `component_kind` String,
   `component_type` String,
   `reason` String, 
   `error` String
) ENGINE = MergeTree() PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, source_type, host);

CREATE TABLE IF NOT EXISTS ch_test1_base.eventlog(
    `DateTime` DateTime,
    `TransactionStatus` String,
    `TransactionDate` DateTime,
    `TransactionNumber` Int32,
    `User` String,
    `UserUuid` String,
    `Computer` String,
    `Application` String,
    `Connection` Int32,
    `Event` String,
    `Severity` String,
    `Comment` String,
    `Metadata` String,
    `MetadataUuid` String,
    `Data` String,
    `DataPresentation` String,
    `Server` String,
    `MainPort` Int16,
    `AddPort` Int16,
    `Session` Int32
) ENGINE = MergeTree() PARTITION BY toYYYYMM(DateTime)
ORDER BY (DateTime);