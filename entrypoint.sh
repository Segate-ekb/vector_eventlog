#!/bin/bash

# Объявляем переменную для хранения имени конфигурационного файла
CONFIG_FILE=""

# Процедура для проверки и заполнения переменных окружения
check_and_fill_env_vars() {
    local error=0

    # Проверяем и заполняем переменную CH_USER
    if [ -n "${CH_USER_FILE}" ] && [ -f "${CH_USER__FILE}" ]; then
        export CH_USER=$(cat "${CH_USER__FILE}")
        echo "CH_USER задан через секрет..✅"
    elif [ -n "${CH_USER}" ]; then
        echo "CH_USER из переменной окружения..✅"
    else
        echo "Ошибка: CH_USER не задан..❌"
        error=1
    fi

    # Проверяем и заполняем переменную CH_PASSWORD
    if [ -n "${CH_PASSWORD_FILE}" ] && [ -f "${CH_PASSWORD__FILE}" ]; then
        export CH_PASSWORD=$(cat "${CH_PASSWORD__FILE}")
        echo "CH_PASSWORD задан через секрет..✅"
    elif [ -n "${CH_PASSWORD}" ]; then
        echo "CH_PASSWORD из переменной окружения..✅"
    else
        echo "CH_PASSWORD не задан, доступ к clickhouse без пароля возможен только в демонстрационных целях! .. ⚠️"
    fi

    # Устанавливаем CH_SERVER, если не задан
    if [ -z "${CH_SERVER}" ]; then
        export CH_SERVER="clickhouse:8123"
        echo "CH_SERVER не задан. Используется значение по умолчанию: <clickhouse:8123>..✅"
    else
        echo "CH_SERVER из переменной окружения: <${CH_SERVER}>..✅"
    fi

    # Устанавливаем LOG_TABLE, если не задан
    if [ -z "${LOG_TABLE}" ]; then
        export LOG_TABLE="eventlog"
        echo "LOG_TABLE не задан. Используется значение по умолчанию: <eventlog>..✅"
    else
        echo "LOG_TABLE из переменной окружения: <${LOG_TABLE}>..✅"
    fi

    # Устанавливаем ERROR_TABLE, если не задан
    if [ -z "${ERROR_TABLE}" ]; then
        export ERROR_TABLE="eventlog_error"
        echo "ERROR_TABLE не задан. Используется значение по умолчанию: <eventlog_error>..✅"
    else
        echo "ERROR_TABLE из переменной окружения: <${ERROR_TABLE}>..✅"
    fi

    # Устанавливаем CREATE_CLICKHOUSE_BASES_ALLOWED, если не задан
    if [ -z "${CREATE_CLICKHOUSE_BASES_ALLOWED}" ]; then
        export CREATE_CLICKHOUSE_BASES_ALLOWED="true"
        echo "CREATE_CLICKHOUSE_BASES_ALLOWED не задан. Используется значение по умолчанию: <true>..✅"
    else
        echo "CREATE_CLICKHOUSE_BASES_ALLOWED из переменной окружения: <${CREATE_CLICKHOUSE_BASES_ALLOWED}>..✅"
    fi

    # Выход, если были обнаружены ошибки
    if [ "$error" -ne 0 ]; then
        echo "Обнаружены ошибки при проверке переменных окружения. Выход из скрипта.❌"
        exit 1
    fi
}



# Процедура для определения способа сбора логов
define_log_collection_method() {
    if [ -n "${CH_BASE_NAME}" ]; then
        echo "Используется общая база данных. Конфигурация: singleBaseConfig.yaml..✅"
        CONFIG_FILE="singleBaseConfig.yaml"
        python3 configure_vector.py --single-base
    elif [ -n "${BASE_LIST}" ]; then
        # Предполагаем, что BASE_LIST содержит YAML в виде строки
        echo "${BASE_LIST}" > /tmp/baseList.yaml
        echo "BASE_LIST определена. Конфигурация: multiBaseConfig.yaml..✅"
        CONFIG_FILE="multiBaseConfig.yaml"
        python3 configure_vector.py "/tmp/baseList.yaml"
    elif [ -n "${BASE_LIST__FILE}" ] && [ -f "${BASE_LIST__FILE}" ]; then
        # BASE_LIST__FILE указывает на файл
        echo "BASE_LIST__FILE определена и файл существует. Конфигурация: multiBaseConfig.yaml..✅"
        CONFIG_FILE="multiBaseConfig.yaml"
        python3 configure_vector.py "${BASE_LIST__FILE}"
    elif [ -f "/etc/vector/baseList.yaml" ]; then
        # Файл /etc/vector/baseList.yaml существует
        echo "Файл /etc/vector/baseList.yaml найден. Конфигурация: multiBaseConfig.yaml..✅"
        CONFIG_FILE="multiBaseConfig.yaml"
        python3 configure_vector.py "/etc/vector/baseList.yaml"
    else
        echo "Ошибка: CH_BASE_NAME не задана, BASE_LIST и BASE_LIST__FILE не определены, файл /etc/vector/baseList.yaml не найден. Невозможно определить конфигурацию..❌"
        exit 1
    fi

    # Проверяем код возврата предыдущей команды
    if [ $? -ne 0 ]; then
        echo "Ошибка при заполнении конфигурации vector. Прерывание выполнения..❌"
        exit 1
    fi
}

create_clickhouse_bases() {
    if [ "${CREATE_CLICKHOUSE_BASES_ALLOWED}" == "false" ]; then
        echo "Создание баз данных ClickHouse запрещено. Пропускаем..."
        return
    fi

    python3 create_databases.py

    # Проверяем код возврата предыдущей команды
    if [ $? -ne 0 ]; then
        echo "Ошибка при создании баз данных ClickHouse. Прерывание выполнения..❌"
        exit 1
    fi
}


# Процедура для ожидания доступности сервера ClickHouse
wait_for_clickhouse() {
    echo "Проверка доступности сервера ClickHouse..."
    local start_ts=$(date +%s)
    local end_ts=$(($start_ts + 300)) # 5 минут ожидания
    local server_ready=0

    while [ $(date +%s) -lt $end_ts ]; do
        if curl -s "${CH_SERVER}" > /dev/null; then
            echo "Сервер ClickHouse доступен..✅"
            server_ready=1
            break
        else
            echo "Ожидаем доступности сервера ClickHouse..⏳"
            sleep 5
        fi
    done

    if [ $server_ready -eq 0 ]; then
        echo "Ошибка: Сервер ClickHouse не стал доступен в течение 5 минут..❌"
        exit 1
    fi
}


start_vector() {
    if [ -z "${CONFIG_FILE}" ]; then
        echo "Конфигурационный файл не определен. Невозможно запустить Vector..❌"
        exit 1
    else
        echo "Запуск Vector с конфигурацией: /etc/vector/${CONFIG_FILE}"
        vector --config "/etc/vector/${CONFIG_FILE}"
    fi
}

list_bases() {
    echo "Запуск скрипта для вывода списка баз данных..."
    python3 configure_vector.py --list-bases
}

case "$1" in
    list-bases)
        list_bases
        ;;
    *)
        check_and_fill_env_vars
        define_log_collection_method
        wait_for_clickhouse
        create_clickhouse_bases
        start_vector
        ;;
esac