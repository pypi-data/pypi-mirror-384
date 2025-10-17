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

import django_rq

from django.db.models import (
    F,
    OuterRef,
    Subquery,
)

from rest_framework import (
    filters,
    generics,
    pagination,
    response,
    serializers,
)

from .models import SchedulerStatus, get_registered_task_model
from .tasks.models import EventizerTask


class EventizerPaginator(pagination.PageNumberPagination):
    page_size = 25
    page_size_query_param = "size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return response.Response(
            {
                "links": {"next": self.get_next_link(), "previous": self.get_previous_link()},
                "count": self.page.paginator.count,
                "page": self.page.number,
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )


class EventizerTaskListSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")
    last_jobs = serializers.SerializerMethodField()

    class Meta:
        model = EventizerTask
        fields = [
            "uuid",
            "status",
            "runs",
            "failures",
            "last_run",
            "last_jobs",
            "scheduled_at",
            "datasource_type",
            "datasource_category",
        ]

    def get_last_jobs(self, obj):
        job_klass = get_registered_task_model("eventizer")[1]
        jobs = job_klass.objects.filter(task=obj).order_by("-job_num")[:10]
        return EventizerJobSummarySerializer(jobs, many=True).data


class EventizerJobListSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = get_registered_task_model("eventizer")[1]
        fields = [
            "uuid",
            "job_num",
            "status",
            "scheduled_at",
            "finished_at",
            "queue",
        ]


class EventizerTaskSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = EventizerTask
        fields = [
            "uuid",
            "status",
            "runs",
            "failures",
            "last_run",
            "job_interval",
            "scheduled_at",
            "datasource_type",
            "datasource_category",
        ]


class EventizerJobSummarySerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = get_registered_task_model("eventizer")[1]
        fields = [
            "uuid",
            "job_num",
            "status",
            "scheduled_at",
            "finished_at",
        ]


class EventizerJobSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")
    progress = serializers.SerializerMethodField()

    class Meta:
        model = get_registered_task_model("eventizer")[1]
        fields = [
            "uuid",
            "job_num",
            "status",
            "scheduled_at",
            "finished_at",
            "queue",
            "progress",
        ]

    def get_progress(self, obj):
        if obj.status == SchedulerStatus.RUNNING:
            rq_job = django_rq.get_queue(obj.queue).fetch_job(obj.uuid)
            if rq_job:
                return rq_job.progress.to_dict()
        return obj.progress


class EventizerJobLogsSerializer(serializers.ModelSerializer):
    logs = serializers.SerializerMethodField()

    class Meta:
        model = get_registered_task_model("eventizer")[1]
        fields = [
            "uuid",
            "logs",
        ]

    def get_logs(self, obj):
        if obj.status == SchedulerStatus.RUNNING:
            rq_job = django_rq.get_queue(obj.queue).fetch_job(obj.uuid)
            if rq_job:
                return rq_job.job_log
        return obj.logs


class EventizerTaskList(generics.ListAPIView):
    serializer_class = EventizerTaskListSerializer
    pagination_class = EventizerPaginator
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "scheduled_at",
        "last_run",
    ]
    ordering = [F("last_run").desc(nulls_first=True)]

    def get_queryset(self):
        queryset = EventizerTask.objects.all()
        status = self.request.query_params.get("status")
        last_run_status = self.request.query_params.get("last_run_status")
        if status is not None:
            if int(status) == SchedulerStatus.FAILED:
                queryset = queryset.filter(jobs__status=status).distinct()
            else:
                queryset = queryset.filter(status=status)
        if last_run_status is not None:
            annotation = Subquery(
                get_registered_task_model("eventizer")[1]
                .objects.filter(task_id=OuterRef("id"), finished_at__isnull=False)
                .order_by("-job_num")
                .values("status")[:1]
            )
            queryset = queryset.annotate(last_run_status=annotation).filter(
                last_run_status=last_run_status
            )
        return queryset


class EventizerTaskDetail(generics.RetrieveAPIView):
    queryset = EventizerTask.objects.all()
    lookup_field = "uuid"
    serializer_class = EventizerTaskSerializer
    pagination_class = EventizerPaginator


class EventizerJobList(generics.ListAPIView):
    serializer_class = EventizerJobListSerializer
    pagination_class = EventizerPaginator

    def get_queryset(self):
        task_id = self.kwargs["task_id"]
        queryset = (
            get_registered_task_model("eventizer")[1]
            .objects.filter(task__uuid=task_id)
            .order_by("-scheduled_at")
        )
        status = self.request.query_params.get("status")
        if status is not None:
            queryset = queryset.filter(status=status)
        return queryset


class EventizerJobDetail(generics.RetrieveAPIView):
    lookup_field = "uuid"
    serializer_class = EventizerJobSerializer
    pagination_class = EventizerPaginator

    def get_queryset(self):
        task_id = self.kwargs["task_id"]
        return get_registered_task_model("eventizer")[1].objects.filter(task__uuid=task_id)


class EventizerJobLogs(generics.RetrieveAPIView):
    lookup_field = "uuid"
    serializer_class = EventizerJobLogsSerializer
    pagination_class = EventizerPaginator

    def get_queryset(self):
        task_id = self.kwargs["task_id"]
        return get_registered_task_model("eventizer")[1].objects.filter(task__uuid=task_id)
