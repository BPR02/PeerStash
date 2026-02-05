FROM creativeprojects/resticprofile:0.26.0 AS binary_source

FROM python:3.11-slim

COPY --from=binary_source /usr/bin/resticprofile /usr/bin/resticprofile
COPY --from=binary_source /usr/bin/restic /usr/bin/restic

RUN apt-get update && \
    apt-get install -y \
        openssh-server \
        openssh-client \
        curl \
        jq \
        sqlite3 \
        openssl && \
    rm -rf /var/lib/apt/lists/*

# move scripts
COPY ./scripts/ /srv/peerstash/scripts/
RUN chmod -R 755 /srv/peerstash/scripts
RUN chmod 744 /srv/peerstash/scripts/setup.sh

EXPOSE 22

ENTRYPOINT ["/srv/peerstash/scripts/setup.sh"]
