FROM creativeprojects/resticprofile:0.26.0 AS binary_source

FROM alpine:latest

COPY --from=binary_source /usr/bin/resticprofile /usr/bin/resticprofile
COPY --from=binary_source /usr/bin/restic /usr/bin/restic

RUN apk add --no-cache \
    openssh \
    busybox-suid \
    sqlite \
    restic \
    openssl

# move scripts
COPY ./scripts/ /srv/peerstash/scripts/
RUN chmod -R 700 /srv/peerstash/scripts

EXPOSE 22

ENTRYPOINT ["/srv/peerstash/scripts/setup.sh"]
