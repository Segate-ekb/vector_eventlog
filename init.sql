CREATE DATABASE IF NOT EXISTS eventlog_storage;

CREATE TABLE IF NOT EXISTS eventlog_storage.eventlog_error(
   `timestamp` DateTime,
   `source_type` String,
   `host` String,
   `message` String,
   `err` String
) ENGINE = MergeTree() PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, source_type, host);

CREATE TABLE IF NOT EXISTS eventlog_storage.eventlog(
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
