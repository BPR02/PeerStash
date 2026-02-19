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


from datetime import datetime
from typing import Optional

from pydantic import BaseModel

# --- Host Schemas ---


class HostBase(BaseModel):
    hostname: str


class HostCreate(HostBase):
    port: int


class HostRead(HostCreate):
    last_seen: Optional[datetime]


class HostUpdate(BaseModel):
    port: Optional[int] = None
    last_seen: Optional[datetime] = None


# --- Task Schemas ---


class TaskBase(BaseModel):
    name: str


class TaskCreate(TaskBase):
    include: str
    exclude: Optional[str]
    hostname: str
    schedule: str
    retention: int
    prune_schedule: str


class TaskRead(TaskCreate):
    last_run: Optional[datetime]
    last_exit_code: Optional[int]
    last_snapshot_id: Optional[str]
    is_locked: bool


class TaskUpdate(BaseModel):
    include: Optional[str] = None
    exclude: Optional[str] = None
    hostname: Optional[str] = None
    schedule: Optional[str] = None
    retention: Optional[int] = None
    prune_schedule: Optional[str] = None
    last_run: Optional[datetime] = None
    last_exit_code: Optional[int] = None
    last_snapshot_id: Optional[str] = None
    is_locked: Optional[bool] = None
