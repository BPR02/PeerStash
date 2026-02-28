# Peerstash
# Copyright (C) 2026 BPR02

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# build python app
FROM ghcr.io/astral-sh/uv:python3.13-trixie AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1

WORKDIR /app
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock,ro \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen -vv && \
    uv build --wheel -vv

# build custom binaries
FROM debian:trixie AS compiler

# build custom binaries
COPY ./scripts/*.c /srv/peerstash/scripts/
RUN mkdir -p /srv/peerstash/bin && \
    apt-get update && \
    apt-get install -y build-essential && \
    gcc -o /srv/peerstash/bin/create_task /srv/peerstash/scripts/create_task.c && \
    gcc -o /srv/peerstash/bin/remove_task /srv/peerstash/scripts/remove_task.c && \
    gcc -o /srv/peerstash/bin/sync_hosts /srv/peerstash/scripts/sync_hosts.c && \
    chown root /srv/peerstash/bin/* && \
    chmod 4755 /srv/peerstash/bin/*

# get tailscale binaries
FROM tailscale/tailscale:stable AS tailscale_bin

# build final image
FROM python:3.13-slim AS final

RUN apt-get update && \
    apt-get install -y \
        openssh-server \
        openssh-client \
        curl \
        jq \
        sqlite3 \
        restic \
        fuse \
        cron \
        supervisor \
        sudo \
        netcat-openbsd \
        iptables \
        iproute2 && \
    rm -rf /var/lib/apt/lists/*

# move tailscale binaries
COPY --from=tailscale_bin /usr/local/bin/tailscaled /usr/local/bin/tailscaled
COPY --from=tailscale_bin /usr/local/bin/tailscale /usr/local/bin/tailscale
RUN mkdir -p /var/lib/tailscale /var/run/tailscale

# set up supervisord
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# install wheel from builder
WORKDIR /app
COPY --from=builder /app/dist/*.whl /app
RUN pip install --upgrade pip && \
    pip install -vv /app/*.whl && \
    rm -rf /app

# copy create_task binary from compiler
COPY --from=compiler /srv/peerstash/bin/* /srv/peerstash/bin/

# move scripts
COPY ./scripts/*.sh /srv/peerstash/scripts/
RUN chmod -R 744 /srv/peerstash/scripts

# set up files and folders
RUN mkdir -p /tmp/peerstash && chmod 777 /tmp/peerstash
RUN mkdir -p /tmp/peerstash_mnt && chmod 777 /tmp/peerstash_mnt
RUN echo "user_allow_other" >> /etc/fuse.conf

EXPOSE 22

ENTRYPOINT ["/srv/peerstash/scripts/setup.sh"]
