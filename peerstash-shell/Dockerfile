FROM alpine:latest

# get dependencies
RUN apk add --no-cache \
    openssh \
    busybox-suid \
    sqlite \
    restic \
    openssl \
    socat

# move scripts
COPY ./scripts/ /peerstash/scripts/
RUN chmod -R 744 /peerstash/scripts

RUN mkdir -p "/peerstash/config"
RUN mkdir -p "/peerstash/backups"

EXPOSE 22 20461 40461

ENTRYPOINT ["/peerstash/scripts/setup.sh"]
