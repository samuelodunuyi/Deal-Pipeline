import uuid as uuid_lib

from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from .caching import CachedListMixin
from .mixins import EnvelopeMixin
from .permissions import STANDARD_PERMISSIONS


def parse_uuid(value):
    """A UUID for valid input, otherwise None (never raises)."""
    if isinstance(value, uuid_lib.UUID):
        return value
    try:
        return uuid_lib.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def parse_int(value):
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return None


def parse_bool(value):
    lowered = str(value).strip().lower()
    if lowered in ('true', '1', 't', 'yes'):
        return True
    if lowered in ('false', '0', 'f', 'no'):
        return False
    raise ValueError(f'{value!r} is not a valid boolean')


class PaginationError(ValueError):
    pass


def paginate(request, queryset):
    """
    Returns (page_items, meta). `?page=` (default 1) and `?page_size=` (default
    API_DEFAULT_PAGE_SIZE, capped at API_MAX_PAGE_SIZE) select the slice.
    """
    default_size = settings.API_DEFAULT_PAGE_SIZE
    max_size = settings.API_MAX_PAGE_SIZE

    page_size = parse_int(request.query_params.get('page_size', default_size))
    page_number = parse_int(request.query_params.get('page', 1))
    if page_size is None or page_size < 1:
        raise PaginationError('page_size must be a positive integer')
    if page_number is None or page_number < 1:
        raise PaginationError('page must be a positive integer')
    page_size = min(page_size, max_size)

    if not queryset.ordered:
        queryset = queryset.order_by('pk')
    paginator = Paginator(queryset, page_size)
    try:
        page = paginator.page(page_number)
    except EmptyPage:
        if page_number == 1:
            return [], _meta(paginator, 1, page_size, has_next=False, has_previous=False)
        raise PaginationError('page is out of range')
    return page.object_list, _meta(paginator, page_number, page_size, page.has_next(), page.has_previous())


def _meta(paginator, page, page_size, has_next, has_previous):
    return {
        'count': paginator.count,
        'page': page,
        'page_size': page_size,
        'total_pages': paginator.num_pages,
        'has_next': has_next,
        'has_previous': has_previous,
    }


class ListMixin:
    """Paginated list responses (with caching) for hand-written views."""

    def list_response(self, request, queryset, serializer_class):
        try:
            items, meta = paginate(request, queryset)
        except PaginationError as exc:
            return self.bad_request(str(exc))
        data = serializer_class(items, many=True).data
        return self.respond_and_cache(request, data, meta)


class CrudAPIView(EnvelopeMixin, CachedListMixin, ListMixin, APIView):
    """
    One configurable GET/POST/PUT/DELETE view for a model. Subclasses set:

        model, serializer_class, label          what it manages
        id_kind = 'int' | 'uuid'                how a single record is addressed
        uuid_in_path / uuid_in_query            where a uuid may be read from (GET)
        full_update                             True: PUT replaces, False: PUT is partial
        create_returns_data / update_returns_data
        filters = {'param': ('orm_lookup', coercer_or_None)}   list filters from the query string

    Integer ids come from the URL path (`/<pk>`) or `?id=`; uuids are read from the path,
    `?uuid=`, or the request body (PUT and DELETE), depending on the flags.
    """

    model = None
    serializer_class = None
    label = 'Record'
    id_kind = 'int'
    uuid_in_path = False
    uuid_in_query = False
    full_update = False
    create_returns_data = True
    update_returns_data = True
    filters = {}

    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = STANDARD_PERMISSIONS

    @property
    def cache_models(self):
        return [self.model]

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    # -- helpers ---------------------------------------------------------------------------

    def _coerce_key(self, raw):
        return parse_uuid(raw) if self.id_kind == 'uuid' else parse_int(raw)

    def _key_error(self):
        return self.bad_request('A valid UUID is required' if self.id_kind == 'uuid' else 'A valid integer id is required')

    def _lookup(self, key):
        field = 'uuid' if self.id_kind == 'uuid' else 'id'
        return self.model.objects.filter(**{field: key}).first()

    def _not_found(self):
        return self.not_found(f'{self.label} not found')

    def _filtered_queryset(self, request):
        qs = self.model.objects.all()
        for param, (lookup, coerce) in self.filters.items():
            raw = request.query_params.get(param)
            if not raw:
                continue
            value = coerce(raw) if coerce else raw
            qs = qs.filter(**{lookup: value})
        return qs

    # -- verbs -----------------------------------------------------------------------------

    def get(self, request, pk=None, uuid=None):
        cached = self.cached_response(request)
        if cached is not None:
            return cached

        raw = pk if pk is not None else uuid
        if raw is None:
            raw = request.query_params.get('id' if self.id_kind == 'int' else ('uuid' if self.uuid_in_query else None))

        if raw is not None and raw != '':
            key = self._coerce_key(raw)
            if key is None:
                return self._key_error()
            obj = self._lookup(key)
            if obj is None:
                return self._not_found()
            return self.respond_and_cache(request, self.get_serializer(obj).data)

        try:
            qs = self._filtered_queryset(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.list_response(request, qs, self.serializer_class)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.bad_request('Invalid data', serializer.errors)
        serializer.save()
        return self.created(serializer.data if self.create_returns_data else None, f'{self.label} created successfully')

    def _target_key(self, request, pk):
        """The raw id for PUT/DELETE: from the path for int ids, from the body for uuids."""
        if self.id_kind == 'int':
            return pk
        return request.data.get('uuid')

    def put(self, request, pk=None, uuid=None):
        raw = uuid if uuid is not None else self._target_key(request, pk)
        if raw is None and self.id_kind == 'int':
            return self._not_found()
        key = self._coerce_key(raw)
        if key is None:
            return self._key_error()
        obj = self._lookup(key)
        if obj is None:
            return self._not_found()

        serializer = self.get_serializer(obj, data=request.data, partial=not self.full_update)
        if not serializer.is_valid():
            return self.bad_request('Invalid data', serializer.errors)
        serializer.save()
        return self.success(serializer.data if self.update_returns_data else None, f'{self.label} updated successfully')

    def delete(self, request, pk=None, uuid=None):
        raw = uuid if uuid is not None else self._target_key(request, pk)
        if raw is None and self.id_kind == 'int':
            return self._not_found()
        key = self._coerce_key(raw)
        if key is None:
            return self._key_error()
        obj = self._lookup(key)
        if obj is None:
            return self._not_found()
        obj.delete()
        return self.deleted(f'{self.label} deleted successfully')
