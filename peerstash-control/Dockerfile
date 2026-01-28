FROM creativeprojects/resticprofile:0.26.0 AS binary_source

FROM python:3.12-slim

COPY --from=binary_source /usr/bin/resticprofile /usr/bin/resticprofile
COPY --from=binary_source /usr/bin/restic /usr/bin/restic

RUN apt-get update && \
    apt-get install -y \
        openssh-client \
        sqlite3 \
        openssl && \
    rm -rf /var/lib/apt/lists/*

# move scripts
COPY ./scripts/ /srv/peerstash/scripts/
RUN chmod -R 700 /srv/peerstash/scripts

EXPOSE 22

ENTRYPOINT ["/srv/peerstash/scripts/setup.sh"]
