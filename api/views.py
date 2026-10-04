from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils.dateparse import parse_date, parse_time

from rest_framework.views import APIView

from .caching import CachedListMixin
from .crud import CrudAPIView, ListMixin, parse_bool, parse_uuid
from .mixins import EnvelopeMixin
from .models import (
    Users, Events, Projects, Grant, Grant_partner,
    DevelopmentPlans, Deliverables, MentorshipPlans,
    SkillAssessments, SpeakingEngagements, TrainingSchedules, AdminUsers,
)
from .permissions import STAFF_ONLY_PERMISSIONS, STANDARD_PERMISSIONS
from .serializers import (
    EventsSerializers, UsersSerializers, ProjectsSerializer, GrantSerializer,
    GrantPartnerSerializer, DevelopmentPlansSerializer, DeliverablesSerializer,
    MentorshipPlansSerializer, SkillAssessmentsSerializer,
    SpeakingEngagementsSerializer, TrainingSchedulesSerializer, AdminUsersSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# Events (custom: status workflow instead of a plain update)
# ─────────────────────────────────────────────────────────────────────────────

class EventsView(EnvelopeMixin, CachedListMixin, ListMixin, APIView):
    cache_models = [Events]
    serializer_class = EventsSerializers
    permission_classes = STANDARD_PERMISSIONS

    STATUS_TRIGGERS = {
        'storage_created': 'Pending document upload',
        'document_uploaded': 'Pending L&D verification',
        'LD_verified': 'Pending schedule',
        'schedule_created': 'Pending access to dataroom',
        'dataroom_access_granted': 'Done',
    }

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        cached = self.cached_response(request)
        if cached is not None:
            return cached

        event_id = request.GET.get('event_uuid', '')
        venue = request.GET.get('venue', '')
        state = request.GET.get('state', '')
        country = request.GET.get('country', '')
        order = request.GET.get('orderBy', '')

        events = Events.objects.all()
        if event_id:
            parsed = parse_uuid(event_id)
            if parsed is None:
                return self.bad_request('event_uuid must be a valid UUID')
            events = events.filter(uuid=parsed)
        if state:
            events = events.filter(state=state)
        if venue:
            events = events.filter(venue__icontains=venue)
        if country:
            events = events.filter(country=country)
        if order == 'latest':
            events = events.order_by('-date', '-time')
        elif order == 'earliest':
            events = events.order_by('date', 'time')

        return self.list_response(request, events, EventsSerializers)

    def post(self, request, *args, **kwargs):
        data = request.data
        date = parse_date(str(data.get('date') or ''))
        time = parse_time(str(data.get('time') or ''))
        if date is None or time is None:
            return self.bad_request('A valid date (YYYY-MM-DD) and time (HH:MM) are required')

        Events.objects.create(
            transaction=data.get('transaction') or '',
            transaction_description=data.get('transaction_description') or '',
            venue=data.get('venue') or '',
            co_transactor=data.get('co_transactor') or '',
            address=data.get('address') or '',
            address2=data.get('address2') or '',
            state=(data.get('state') or '').lower(),
            country=(data.get('country') or '').lower(),
            date=date,
            time=time,
        )
        return self.success(message='Event Saved Successfully')

    def put(self, request, *args, **kwargs):
        data = request.data
        raw_uuid = data.get('event_uuid', '')
        status_trigger = data.get('status', '')

        if not raw_uuid:
            return self.bad_request('Event UUID not set')
        event_uuid = parse_uuid(raw_uuid)
        if event_uuid is None:
            return self.bad_request('Event UUID is not a valid UUID')

        new_status = self.STATUS_TRIGGERS.get(status_trigger.strip() if status_trigger else '', '')
        if not new_status:
            if status_trigger:
                return self.bad_request('invalid status trigger')
            return self.bad_request('Status Trigger not set')

        updated = Events.objects.filter(uuid=event_uuid).update(status=new_status)
        if updated == 0:
            return self.bad_request('Invalid UUID')
        return self.success(message='Updated Successfully')


# ─────────────────────────────────────────────────────────────────────────────
# Users (custom: looked up by email)
# ─────────────────────────────────────────────────────────────────────────────

class UsersView(EnvelopeMixin, CachedListMixin, ListMixin, APIView):
    cache_models = [Users]
    serializer_class = UsersSerializers
    permission_classes = STANDARD_PERMISSIONS

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        cached = self.cached_response(request)
        if cached is not None:
            return cached

        qs = Users.objects.all()
        name = request.GET.get('name', '')
        company = request.GET.get('company', '')
        phone_number = request.GET.get('phone_number', '')
        role = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')
        email = request.GET.get('email', '')

        if name:
            qs = qs.filter(name__icontains=name)
        if company:
            qs = qs.filter(company=company)
        if phone_number:
            qs = qs.filter(phone_number=phone_number)
        if role:
            qs = qs.filter(role=role)
        if email:
            qs = qs.filter(email__iexact=email)
        if status_filter:
            qs = qs.filter(status=status_filter)

        return self.list_response(request, qs, UsersSerializers)

    def post(self, request, *args, **kwargs):
        data = request.data
        name = data.get('name', '')
        company = data.get('company', '')
        phone_number = data.get('phone_number', '')
        role = data.get('role', '')
        status_val = data.get('status', '')
        email = (data.get('email', '') or '').strip()

        if not all([email, company, name, role, status_val]):
            return self.bad_request('Complete all Fields')
        try:
            validate_email(email)
        except DjangoValidationError:
            return self.bad_request('Enter a valid email address')
        if Users.objects.filter(email__iexact=email).exists():
            return self.bad_request('A user with this email already exists')

        Users.objects.create(
            name=name, company=company, phone_number=phone_number,
            role=role, status=status_val, email=email,
        )
        return self.success(message='User Saved Successfully')

    def put(self, request, *args, **kwargs):
        data = request.data
        email = (data.get('email', '') or '').strip()

        user = Users.objects.filter(email__iexact=email).order_by('date_added').first() if email else None
        if not user:
            return self.bad_request('Email Does Not exist')

        for field in ('name', 'company', 'phone_number', 'role', 'status'):
            value = data.get(field, '')
            if value:
                setattr(user, field, value)
        user.save()
        return self.success(message='Updated Successfully')


# ─────────────────────────────────────────────────────────────────────────────
# Standard resources: one short configuration class each (see crud.CrudAPIView)
# ─────────────────────────────────────────────────────────────────────────────

class ProjectsAPIView(CrudAPIView):
    model = Projects
    serializer_class = ProjectsSerializer
    label = 'Project'
    id_kind = 'uuid'
    uuid_in_query = True
    full_update = True
    update_returns_data = False
    filters = {
        'project_name': ('project_name__icontains', None),
        'transaction_name': ('transaction_name__icontains', None),
        'industry': ('industry__icontains', None),
        'sector': ('sector__icontains', None),
        'status': ('status', parse_bool),
    }


class GrantAPIView(CrudAPIView):
    model = Grant
    serializer_class = GrantSerializer
    label = 'Grant'
    id_kind = 'uuid'
    uuid_in_query = True
    full_update = True
    update_returns_data = False
    filters = {
        'development_partner': ('development_partner', None),
        'transaction_name': ('transaction_name', None),
    }


class GrantPartnerAPIView(CrudAPIView):
    model = Grant_partner
    serializer_class = GrantPartnerSerializer
    label = 'Grant partner'
    id_kind = 'uuid'
    uuid_in_path = True
    create_returns_data = False
    filters = {
        'partner_name': ('partner_name__icontains', None),
        'currency': ('currency__icontains', None),
    }


class DevelopmentPlansAPIView(CrudAPIView):
    model = DevelopmentPlans
    serializer_class = DevelopmentPlansSerializer
    label = 'Development plan'
    create_returns_data = False


class DeliverablesAPIView(CrudAPIView):
    model = Deliverables
    serializer_class = DeliverablesSerializer
    label = 'Deliverable'
    create_returns_data = False


class MentorshipPlansAPIView(CrudAPIView):
    model = MentorshipPlans
    serializer_class = MentorshipPlansSerializer
    label = 'Mentorship plan'
    create_returns_data = False


class SkillAssessmentsAPIView(CrudAPIView):
    model = SkillAssessments
    serializer_class = SkillAssessmentsSerializer
    label = 'Skill assessment'


class SpeakingEngagementsAPIView(CrudAPIView):
    model = SpeakingEngagements
    serializer_class = SpeakingEngagementsSerializer
    label = 'Speaking engagement'


class TrainingSchedulesAPIView(CrudAPIView):
    model = TrainingSchedules
    serializer_class = TrainingSchedulesSerializer
    label = 'Training schedule'


class AdminUsersAPIView(CrudAPIView):
    model = AdminUsers
    serializer_class = AdminUsersSerializer
    label = 'Admin user'
    permission_classes = STAFF_ONLY_PERMISSIONS
