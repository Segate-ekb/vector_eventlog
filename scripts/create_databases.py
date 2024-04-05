import requests
import os
import csv

def get_bases():
    # Получение списка баз из переменной окружения или файла
    bases = []
    ch_base_name = os.getenv("CH_BASE_NAME")
    if ch_base_name:
        bases.append(ch_base_name)
    else:
        file_path = '/etc/vector/BaseList.csv' 
        if os.path.exists(file_path):
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    bases.append(row['ClickHouseBaseName'])
        else:
            print(f"Файл {file_path} не найден!..❌")
            exit(1)
    if not bases:
        print("Список баз данных пуст! Нечего создавать!..❌")
        exit(1)
    return bases




def create_databases_and_tables(bases, log_table, error_table, ch_user, ch_password, ch_server):

    headers = {
        'Content-Type': 'text/plain'
    }

    auth = (ch_user, ch_password)

    url = check_url(ch_server)


    for base_name in bases:
        try:
            # Создание базы данных
            response = requests.post(
                f"{url}", 
                data=f"CREATE DATABASE IF NOT EXISTS {base_name}", 
                headers=headers,
                auth=auth
            )
            response.raise_for_status()
            print(f"База данных {base_name} успешно создана или уже существует.")

            # Создание таблицы eventlog_error
            response = requests.post(
                f"{url}",
                data=f"""
                CREATE TABLE IF NOT EXISTS {base_name}.{error_table} (
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
                """,
                headers=headers,
                auth=auth
            )
            response.raise_for_status()
            print(f"Таблица {error_table} в базе данных {base_name} успешно создана или уже существует.")

            # Создание таблицы eventlog
            response = requests.post(
                f"{url}",
                data=f"""
                CREATE TABLE IF NOT EXISTS {base_name}.{log_table}(
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
                """,
                headers=headers,
                auth=auth
            )
            response.raise_for_status()
            print(f"Таблица {log_table} в базе данных {base_name} успешно создана или уже существует.")

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при создании базы данных или таблицы в {base_name}: {e}")
            exit(1)

def check_url(url, default_protocol='http://'):
    # Проверяем, начинается ли URL с http:// или https://
    if not (url.startswith('http://') or url.startswith('https://')):
        # Если нет, добавляем к URL протокол по умолчанию
        url = default_protocol + url    

    return url

def main():
    ch_user = os.getenv("CH_USER")
    ch_password = os.getenv("CH_PASSWORD")
    ch_server = os.getenv("CH_SERVER")
    log_table = os.getenv("LOG_TABLE")
    error_table = os.getenv("ERROR_TABLE")
    
    bases = get_bases()
    
    create_databases_and_tables(bases, log_table, error_table, ch_user, ch_password, ch_server)

if __name__ == "__main__":
    main()
