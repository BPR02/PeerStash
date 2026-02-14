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
        sudo && \
    rm -rf /var/lib/apt/lists/*

# install wheel from builder
WORKDIR /app
COPY --from=builder /app/dist/*.whl /app
RUN pip install --upgrade pip && \
    pip install -vv /app/*.whl && \
    rm -rf /app

# move scripts
COPY ./scripts/ /srv/peerstash/scripts/
RUN chmod -R 744 /srv/peerstash/scripts

EXPOSE 22

ENTRYPOINT ["/srv/peerstash/scripts/setup.sh"]
