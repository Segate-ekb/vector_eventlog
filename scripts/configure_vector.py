import yaml
import json
import os
import re
import csv
import argparse

from yaml.representer import SafeRepresenter

# Кастомный репрезентатор для строк, который окружает их двойными кавычками
def quoted_scalar(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

# Добавляем кастомный репрезентатор к классу Dumper
yaml.add_representer(str, quoted_scalar, Dumper=yaml.SafeDumper)

def load_yaml_file(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    return data['databases']

def get_cluster_database_list(search_path):
    # Находим все файлы настроек кластера
    files_list = find_1CV8Clst(search_path)

 # Для каждого найденного файла составляем список баз и их UUID
    cluster_database_list = []
    for file_path in files_list:
        get_bases_from_file(file_path, cluster_database_list)
        
    return cluster_database_list

def find_1CV8Clst(search_path):
    files_list = []
    for root, dirs, files in os.walk(search_path):
        for file_name in files:
            if file_name == "1CV8Clst.lst":
                files_list.append(os.path.join(root, file_name))
                print(f"Найден файл настроек кластера: {os.path.join(root, file_name)}..✅")
    if files_list == []:
        print("Файлы настроек кластера не найдены, не получится найти соответсвие баз!..❌") 
        exit(1)           
    return files_list

def get_bases_from_file(file_path, cluster_database_list):
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        file_content = file.read()
        cluster_info = parse_cluster_string(file_content)
        if isinstance(cluster_info[2], list):
            for base in cluster_info[2]:
                if isinstance(base, list) and len(base) > 1:
                    print(f"В настройках кластера найдена база <{base[1]}> c UUID <{base[0]}>..✅")
                    cluster_database_list.append((base[0], base[1]))

def parse_cluster_string(input_string):
    # Заменяем символы для приведения к формату JSON
    modified_string = input_string.replace("{", "[").replace("}", "]").replace("\\", "\\\\")
    
    # Замена UUID на строки в кавычках
    uuid_pattern = re.compile(r'([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})')
    modified_string = uuid_pattern.sub(r'"\1"', modified_string)
    
    # Экранирование кавычек внутри строки
    quotes_pattern = re.compile(r'([^,\[\]])(\"\")([^,\[\]])')
    modified_string = quotes_pattern.sub(r'\1\"\3', modified_string)

    # Экранирование кривых чисел
    quotes_pattern = re.compile(r'(,)(0\d+)(,)(0\d+)(,)')
    modified_string = quotes_pattern.sub(r'\1"\2"\3"\4"\5', modified_string)

    # Попытка разобрать строку как JSON
    try:
        result = json.loads(modified_string)
    except json.JSONDecodeError as e:
        print("Ошибка при разборе JSON:", e)
        return None
    
    return result                    

def enrich_databases(databases, cluster_database_list):
    for uuid, base_name_1c in cluster_database_list:
        for db in databases:
            if db['1c_baseName'] == base_name_1c:
                db['uuid'] = uuid

def create_csv_file(databases):
    with open('/etc/vector/BaseList.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['BaseUUID', 'ClickHouseBaseName', '1сBaseName'])
        
        for db in databases:
            base_name_1c = db['1c_baseName']
            ch_base_name = db['ch_baseName']
            uuid = db.get('uuid', '')
            if not uuid:
                print(f"UUID Для базы {base_name_1c} не найден. Сбор логов осуществляться не будет! ⚠️")
                continue
            print(f"Данные для базы {base_name_1c} записаны в файл BaseList.csv..✅")
            writer.writerow([uuid, ch_base_name, base_name_1c])
    print("Файл BaseList.csv создан..✅")

def create_vector_config(databases, template_path="/etc/vector/multiBaseConfig_template.yaml", output_path="/etc/vector/multiBaseConfig.yaml"):
    # Считываем шаблон конфигурации
    with open(template_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    # Проверяем, есть ли нужный раздел и ключ
    if 'sources' in config and 'input_logs' in config['sources'] and 'include' in config['sources']['input_logs']:
        # Формируем список путей к логам для каждой базы данных
        log_paths = []
        for db in databases:
            uuid = db.get('uuid', '')
            if uuid:
                log_paths.append(f"/var/log/eventlog/**/{uuid}/**/*.lgp")
        
        # Обновляем блок include новыми путями
        config['sources']['input_logs']['include'] = log_paths
    else:
        print("Ошибка в структуре шаблона конфигурации..❌")
        exit(1)
    
    # Сохраняем обновлённую конфигурацию в новый файл
    with open(output_path, 'w', encoding='utf-8') as file:
        yaml.safe_dump(config, file, allow_unicode=True, default_flow_style=False)
    
    print(f"Конфигурационный файл успешно обновлён и сохранён как {output_path}..✅")


def prepare_and_print_yaml(cluster_database_list):
    databases = [
        {"1c_baseName": base[1], "ch_baseName": "<Укажите имя базы Clickhouse>"} 
        for base in cluster_database_list
    ]
    yaml_structure = {"databases": databases}

    print("Список баз найденных на сервере, скопируйте данный текст в baseList.yaml: ")
    print(yaml.dump(yaml_structure, allow_unicode=True, default_flow_style=False))


def main():
    parser = argparse.ArgumentParser(description='Конфигуратор сборщика логов.')
    parser.add_argument('prepare_config', nargs='?', help='Путь к файлу YAML с конфигурацией баз данных')
    parser.add_argument('--list-bases', action='store_true', help='Вывести информацию о базах данных в консоль')
    
    args = parser.parse_args()
    
    if args.list_bases:
        cluster_database_list = get_cluster_database_list("/var/log/eventlog/")
        prepare_and_print_yaml(cluster_database_list)

    elif args.prepare_config:
        databases = load_yaml_file(args.prepare_config) 
        cluster_database_list = get_cluster_database_list("/var/log/eventlog/")
        enrich_databases(databases, cluster_database_list)
        create_csv_file(databases)
        create_vector_config(databases)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()