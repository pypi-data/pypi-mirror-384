from django.db.models.query_utils import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from wise.station.publish import Publisher
from wise.station.registry import station_registry


@api_view(["GET"])
def get_heap_node(request):
    publisher_name = request.query_params.get("name")
    index = request.query_params.get("index")
    if not index:
        return Response(
            {"error": "index is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    publisher = _get_publisher_by_name(publisher_name)
    if isinstance(publisher, Response):
        return publisher

    if not publisher.enable_heap:
        return Response(
            {"error": "publisher heap disabled"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        publisher.get_heap_index_message(int(index)),
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def query_publisher(request):
    publisher_name = request.query_params.get("name")
    publisher = _get_publisher_by_name(publisher_name)
    if isinstance(publisher, Response):
        return publisher

    query = Q()
    for k, v in request.query_params.items():
        if k == "name":
            continue
        query &= Q(**{k: v})

    qs = publisher.queryset.filter(query)
    messages = [publisher.get_instance_message(instance) for instance in qs]
    return Response({"results": messages}, status=status.HTTP_200_OK)


def _get_publisher_by_name(publisher_name: str) -> Publisher | Response:
    if not publisher_name:
        return Response(
            {"error": "name is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    publisher = None
    for p in station_registry.publishers:
        if p.name == publisher_name:
            publisher = p
            break

    if not publisher:
        return Response(
            {"error": "publisher not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return publisher
