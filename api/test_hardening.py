"""Tests for input validation, pagination, permissions, uploads, throttling and production hardening."""
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import AdminUsers, Deliverables, Grant, Projects, Users

LOCMEM_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


def _login_as(test, staff=True):
    user = get_user_model().objects.create_user(
        'staff' if staff else 'regular', password='p', is_staff=staff)
    test.client.force_authenticate(user)
    return user


@override_settings(CACHES=LOCMEM_CACHE)
class InvalidInputTests(APITestCase):
    """Malformed ids and filters answer 400, never 500."""

    def setUp(self):
        cache.clear()
        _login_as(self)

    def test_malformed_uuid_and_filters_are_400(self):
        bad_requests = [
            '/api/v1/projects?uuid=abc',
            '/api/v1/projects?status=maybe',
            '/api/v1/grants?uuid=abc',
            '/api/v1/events?event_uuid=abc',
            '/api/v1/development-plans?id=abc',
            '/api/v1/projects?page=0',
            '/api/v1/projects?page_size=abc',
        ]
        for url in bad_requests:
            self.assertEqual(self.client.get(url).status_code, 400, url)
        events_put = self.client.put(
            '/api/v1/events', {'event_uuid': 'abc', 'status': 'storage_created'}, format='json')
        self.assertEqual(events_put.status_code, 400)
        self.assertEqual(self.client.delete('/api/v1/projects', {'uuid': 'abc'}, format='json').status_code, 400)
        self.assertEqual(self.client.put('/api/v1/grants', {'uuid': 'abc'}, format='json').status_code, 400)

    def test_malformed_uuid_in_path_is_404(self):
        self.assertEqual(self.client.get('/api/v1/grant_partner/not-a-uuid').status_code, 404)

    def test_status_filter_accepts_true_and_false_in_any_case(self):
        Projects.objects.create(project_name='open', status=False)
        Projects.objects.create(project_name='done', status=True)
        for raw, expected in (('false', 'open'), ('False', 'open'), ('true', 'done'), ('TRUE', 'done')):
            cache.clear()
            body = self.client.get('/api/v1/projects', {'status': raw}).json()
            self.assertEqual([p['project_name'] for p in body['data']], [expected], raw)


@override_settings(CACHES=LOCMEM_CACHE)
class UsersEmailTests(APITestCase):
    PAYLOAD = {'name': 'A', 'company': 'C', 'role': 'R', 'status': 'S', 'email': 'dup@example.com'}

    def setUp(self):
        cache.clear()
        _login_as(self)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.assertEqual(self.client.post('/api/v1/users', self.PAYLOAD, format='json').status_code, 200)
        again = {**self.PAYLOAD, 'email': 'DUP@example.com'}
        self.assertEqual(self.client.post('/api/v1/users', again, format='json').status_code, 400)
        self.assertEqual(Users.objects.count(), 1)

    def test_invalid_email_is_rejected(self):
        response = self.client.post('/api/v1/users', {**self.PAYLOAD, 'email': 'not-an-email'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_put_updates_only_the_matching_user(self):
        self.client.post('/api/v1/users', self.PAYLOAD, format='json')
        self.client.post('/api/v1/users', {**self.PAYLOAD, 'email': 'other@example.com'}, format='json')
        self.client.put('/api/v1/users', {'email': 'dup@example.com', 'name': 'Changed'}, format='json')
        self.assertEqual(Users.objects.get(email='dup@example.com').name, 'Changed')
        self.assertEqual(Users.objects.get(email='other@example.com').name, 'A')


@override_settings(CACHES=LOCMEM_CACHE)
class PaginationTests(APITestCase):
    def setUp(self):
        cache.clear()
        _login_as(self)
        Projects.objects.bulk_create([Projects(project_name=f'p{i:02d}') for i in range(25)])

    def test_pages_cover_every_row_exactly_once(self):
        seen = []
        for page in (1, 2, 3):
            cache.clear()
            body = self.client.get('/api/v1/projects', {'page': page, 'page_size': 10}).json()
            seen += [p['project_name'] for p in body['data']]
            self.assertEqual(body['pagination']['count'], 25)
            self.assertEqual(body['pagination']['total_pages'], 3)
        self.assertEqual(sorted(seen), sorted(f'p{i:02d}' for i in range(25)))

    def test_default_returns_all_rows_below_the_default_size_with_metadata(self):
        body = self.client.get('/api/v1/projects').json()
        self.assertEqual(len(body['data']), 25)
        self.assertFalse(body['pagination']['has_next'])

    def test_page_size_is_capped(self):
        with override_settings(API_MAX_PAGE_SIZE=5):
            body = self.client.get('/api/v1/projects', {'page_size': 1000}).json()
        self.assertEqual(len(body['data']), 5)
        self.assertEqual(body['pagination']['page_size'], 5)

    def test_page_past_the_end_is_400_but_an_empty_list_is_fine(self):
        self.assertEqual(self.client.get('/api/v1/projects', {'page': 99}).status_code, 400)
        Projects.objects.all().delete()
        cache.clear()
        self.assertEqual(self.client.get('/api/v1/projects').json()['data'], [])

    def test_cached_responses_keep_their_pagination(self):
        first = self.client.get('/api/v1/projects', {'page_size': 10}).json()
        second = self.client.get('/api/v1/projects', {'page_size': 10}).json()
        self.assertEqual(first, second)
        self.assertEqual(second['pagination']['count'], 25)


@override_settings(CACHES=LOCMEM_CACHE)
class PermissionTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_regular_user_can_read_and_write_but_not_delete(self):
        _login_as(self, staff=False)
        created = self.client.post('/api/v1/grants', {'development_partner': 'd'}, format='json')
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.get('/api/v1/grants').status_code, 200)
        uuid = Grant.objects.get().uuid
        response = self.client.delete('/api/v1/grants', {'uuid': str(uuid)}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Grant.objects.count(), 1)

    def test_staff_can_delete(self):
        _login_as(self, staff=True)
        self.client.post('/api/v1/grants', {'development_partner': 'd'}, format='json')
        uuid = Grant.objects.get().uuid
        self.assertEqual(self.client.delete('/api/v1/grants', {'uuid': str(uuid)}, format='json').status_code, 204)

    def test_admin_users_are_staff_only_for_every_method(self):
        _login_as(self, staff=False)
        self.assertEqual(self.client.get('/api/v1/admin-users').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/admin-users', {'fullName': 'x'}, format='json').status_code, 403)
        self.assertEqual(self.client.put('/api/v1/admin-users/1', {'fullName': 'x'}, format='json').status_code, 403)
        self.assertEqual(self.client.delete('/api/v1/admin-users/1').status_code, 403)
        self.assertEqual(AdminUsers.objects.count(), 0)

    def test_staff_can_use_admin_users(self):
        _login_as(self, staff=True)
        self.assertEqual(self.client.post('/api/v1/admin-users', {'fullName': 'x'}, format='json').status_code, 201)


@override_settings(CACHES=LOCMEM_CACHE, MEDIA_ROOT=tempfile.mkdtemp())
class UploadValidationTests(APITestCase):
    def setUp(self):
        cache.clear()
        _login_as(self)

    def _post(self, name, content, content_type='application/octet-stream'):
        upload = SimpleUploadedFile(name, content, content_type=content_type)
        return self.client.post(
            '/api/v1/deliverables', {'taskDescription': 't', 'evidence': upload}, format='multipart')

    def test_disallowed_extensions_are_rejected(self):
        for name in ('shell.html', 'x.svg', 'run.exe', 'noextension', 'evil.php'):
            self.assertEqual(self._post(name, b'<script>alert(1)</script>').status_code, 400, name)
        self.assertEqual(Deliverables.objects.count(), 0)

    def test_allowed_file_is_accepted_regardless_of_extension_case(self):
        self.assertEqual(self._post('report.PDF', b'%PDF-1.4 test', 'application/pdf').status_code, 201)

    def test_oversized_file_is_rejected(self):
        with override_settings(UPLOAD_MAX_MB=1):
            response = self._post('big.pdf', b'0' * (1024 * 1024 + 1), 'application/pdf')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Deliverables.objects.count(), 0)

    def test_every_upload_field_is_validated(self):
        for path in ('development-plans', 'mentorship-plans', 'training-schedules'):
            upload = SimpleUploadedFile('x.html', b'<b>', content_type='text/html')
            response = self.client.post(f'/api/v1/{path}', {'evidenceURL': upload}, format='multipart')
            self.assertEqual(response.status_code, 400, path)


@override_settings(CACHES=LOCMEM_CACHE)
class LoginThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        get_user_model().objects.create_user('victim', password='right-password-1')

    def _login(self, password, username='victim', **extra):
        return self.client.post(
            '/api/token', {'username': username, 'password': password}, format='json', **extra)

    def test_repeated_wrong_passwords_get_throttled(self):
        codes = [self._login('wrong').status_code for _ in range(8)]
        self.assertEqual(codes[:5], [401] * 5)
        self.assertIn(429, codes[5:])

    def test_throttle_cannot_be_dodged_by_changing_ip(self):
        codes = [self._login('wrong', REMOTE_ADDR=f'10.0.0.{i}').status_code for i in range(8)]
        self.assertIn(429, codes)

    def test_other_usernames_are_unaffected(self):
        get_user_model().objects.create_user('other', password='right-password-2')
        for _ in range(8):
            self._login('wrong')
        self.assertEqual(self._login('right-password-2', username='other').status_code, 200)


class ProductionHardeningTests(APITestCase):
    HTTPS = dict(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=[r'^api/v1/health/?$'],
                 SECURE_HSTS_SECONDS=3600)

    @override_settings(CACHES=LOCMEM_CACHE, **HTTPS)
    def test_plain_http_is_redirected_except_for_health(self):
        client = self.client_class()
        self.assertEqual(client.get('/api/v1/projects').status_code, 301)
        self.assertEqual(client.get('/api/v1/health').status_code, 200)

    @override_settings(CACHES=LOCMEM_CACHE, **HTTPS)
    def test_https_responses_carry_hsts(self):
        response = self.client_class().get('/api/v1/health', secure=True)
        self.assertEqual(response.headers['Strict-Transport-Security'], 'max-age=3600')

    @override_settings(STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    })
    def test_admin_login_page_is_reachable_under_the_configured_path(self):
        self.assertEqual(self.client.get('/admin/login/').status_code, 200)


@override_settings(CACHES=LOCMEM_CACHE)
class ApiDocsTests(APITestCase):
    def test_schema_requires_login_and_documents_the_api(self):
        self.assertIn(self.client.get('/api/schema/').status_code, (401, 403))
        _login_as(self)
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/api/v1/projects', response.content)
