ARG VERSION=latest-debian

FROM timberio/vector:${VERSION}

# Установка Python и создание виртуальной среды
RUN apt-get update && \
    apt-get install -y python3 python3-venv python3-pip curl && \
    python3 -m venv /opt/venv && \
    apt-get clean

# Активация виртуальной среды и установка PyYAML
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pyyaml requests

COPY ./config /etc/vector/
COPY ./entrypoint.sh /entrypoint.sh
COPY ./scripts/configure_vector.py /configure_vector.py
COPY ./scripts/create_databases.py /create_databases.py

# Даем права на выполнение скриптов
RUN chmod +x /entrypoint.sh \
&& chmod +x /configure_vector.py \
&& chmod +x /create_databases.py

ENTRYPOINT ["/entrypoint.sh"]
