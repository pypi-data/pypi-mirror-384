# -*- coding: utf-8 -*-
#
# Copyright (C) GrimoireLab Contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import uuid
from django.db.models import (
    CharField,
    CASCADE,
    ForeignKey,
    OneToOneField,
)
from django.core.validators import RegexValidator

from ..scheduler.tasks.models import EventizerTask
from ..models import (
    BaseModel,
    MAX_SIZE_CHAR_FIELD,
    MAX_SIZE_NAME_FIELD,
)

INVALID_NAME_ERROR = """Field may only contain lowercase letters, numbers or hyphens.
    It may only start with a letter and cannot end with a hyphen."""


class Repository(BaseModel):
    """Base class for repositories

    A repository is composed of a backend and a URI.
    """

    uuid = CharField(max_length=MAX_SIZE_CHAR_FIELD, default=uuid.uuid4, unique=True)
    uri = CharField(max_length=MAX_SIZE_CHAR_FIELD)
    datasource_type = CharField(max_length=MAX_SIZE_CHAR_FIELD)

    class Meta:
        unique_together = [
            "uri",
            "datasource_type",
        ]


validate_name = RegexValidator(
    r"^[a-z]+(?:-*[a-z0-9]+)*$",
    (INVALID_NAME_ERROR),
    "invalid",
)


class Ecosystem(BaseModel):
    """Base class for ecosystems

    An ecosystem abstract set of projects which may share a common context.
    It is composed of a unique name and an optional title and description.
    """

    name = CharField(unique=True, max_length=MAX_SIZE_NAME_FIELD, validators=[validate_name])
    title = CharField(max_length=MAX_SIZE_CHAR_FIELD, null=True)
    description = CharField(max_length=MAX_SIZE_CHAR_FIELD, null=True)

    class Meta:
        ordering = ["name"]


class Project(BaseModel):
    """Model class for Project objects.

    This class is meant to represent a set of data locations which
    have to be grouped under the same entity. Moreover, this grouping
    may have a hierarchy by defining n sub-projects.

    Every project object must have a name and must belong
    to one single Ecosystem. There cannot be two projects with
    the same name under the same Ecosytem.
    Optionally, it may have a title and a relation with
    a parent project.

    :param name: Name of the project
    :param title: Title of the project
    :param parent_project: Parent project object
    :param ecosystem: Ecosystem which the project belongs to
    """

    name = CharField(max_length=MAX_SIZE_NAME_FIELD, validators=[validate_name])
    title = CharField(max_length=MAX_SIZE_CHAR_FIELD, null=True)
    parent_project = ForeignKey(
        "project", parent_link=True, null=True, on_delete=CASCADE, related_name="subprojects"
    )
    ecosystem = ForeignKey("ecosystem", on_delete=CASCADE)

    class Meta:
        ordering = ["name"]
        unique_together = [
            "name",
            "ecosystem",
        ]


class DataSet(BaseModel):
    """Base class for data sets

    A data set is composed of a project, a category, and a repository.
    Each repository is fetched by a task. The task will be executed
    recurrently.
    """

    project = ForeignKey(Project, on_delete=CASCADE)
    repository = ForeignKey(Repository, on_delete=CASCADE)
    category = CharField(max_length=MAX_SIZE_CHAR_FIELD)
    task = OneToOneField(EventizerTask, on_delete=CASCADE, null=True, default=None)

    class Meta:
        ordering = ["id"]
        unique_together = [
            "project",
            "repository",
            "category",
        ]
