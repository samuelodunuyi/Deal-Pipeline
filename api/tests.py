from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import DevelopmentPlans, Events, Grant

LOCMEM_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


@override_settings(CACHES=LOCMEM_CACHE)
class CacheKeyTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(get_user_model().objects.create_user('u', password='p'))

    def test_detail_routes_do_not_share_a_cache_entry(self):
        a = DevelopmentPlans.objects.create(goalSummary='plan a')
        b = DevelopmentPlans.objects.create(goalSummary='plan b')

        first = self.client.get(f'/api/v1/development-plans/{a.pk}')
        second = self.client.get(f'/api/v1/development-plans/{b.pk}')

        self.assertEqual(first.json()['data']['goalSummary'], 'plan a')
        self.assertEqual(second.json()['data']['goalSummary'], 'plan b')


@override_settings(CACHES=LOCMEM_CACHE)
class GrantFilterTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(get_user_model().objects.create_user('u', password='p'))

    def test_unknown_client_name_param_does_not_500(self):
        response = self.client.get('/api/v1/grants', {'client_name': 'x'})
        self.assertEqual(response.status_code, 200)


@override_settings(CACHES=LOCMEM_CACHE)
class EventsPostTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(get_user_model().objects.create_user('u', password='p'))

    def test_null_state_is_treated_as_empty_not_500(self):
        response = self.client.post(
            '/api/v1/events',
            {'transaction': 't', 'state': None, 'country': 'ng', 'date': '2026-01-01', 'time': '10:00'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Events.objects.get().state, '')

    def test_empty_date_is_rejected_not_500(self):
        response = self.client.post(
            '/api/v1/events',
            {'transaction': 't', 'state': 'Lagos', 'country': 'NG', 'date': '', 'time': ''},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Events.objects.count(), 0)

    def test_valid_event_is_saved_lowercased(self):
        response = self.client.post(
            '/api/v1/events',
            {'transaction': 't', 'state': 'Lagos', 'country': 'NG', 'date': '2026-01-01', 'time': '10:00'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        event = Events.objects.get()
        self.assertEqual((event.state, event.country), ('lagos', 'ng'))


@override_settings(CACHES=LOCMEM_CACHE)
class MoneyFieldTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(get_user_model().objects.create_user('u', password='p'))

    def test_amounts_are_stored_exactly_and_returned_as_json_numbers(self):
        created = self.client.post(
            '/api/v1/grants',
            {'development_partner': 'dp', 'total_grant_required': 10000.1, 'total_grant_used': 0.1,
             'total_grant_left': '9999.99'},
            format='json',
        )
        self.assertEqual(created.status_code, 201)
        grant = Grant.objects.get()
        self.assertEqual(grant.total_grant_required, Decimal('10000.10'))
        self.assertEqual(grant.total_grant_used, Decimal('0.10'))

        body = self.client.get('/api/v1/grants').json()['data'][0]
        for field in ('total_grant_required', 'total_grant_used', 'total_grant_left'):
            self.assertIsInstance(body[field], (int, float), field)
        self.assertEqual(body['total_grant_left'], 9999.99)

    def test_more_than_two_decimal_places_is_rejected(self):
        response = self.client.post(
            '/api/v1/grants', {'total_grant_required': '1.234'}, format='json'
        )
        self.assertEqual(response.status_code, 400)


class CorsTests(APITestCase):
    ALLOWED = 'https://app.example.com'

    @override_settings(CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=[ALLOWED])
    def test_only_listed_origins_get_cors_headers(self):
        allowed = self.client.get('/api/v1/health', HTTP_ORIGIN=self.ALLOWED)
        evil = self.client.get('/api/v1/health', HTTP_ORIGIN='https://evil.example.net')
        self.assertEqual(allowed.headers.get('Access-Control-Allow-Origin'), self.ALLOWED)
        self.assertNotIn('Access-Control-Allow-Origin', evil.headers)


@override_settings(CACHES=LOCMEM_CACHE)
class AuthTests(APITestCase):
    def test_anonymous_requests_are_rejected(self):
        for path in ('/api/v1/projects', '/api/v1/users', '/api/v1/grants', '/api/v1/events'):
            self.assertIn(self.client.get(path).status_code, (401, 403), path)
        self.assertIn(self.client.post('/api/v1/projects', {}, format='json').status_code, (401, 403))
        self.assertIn(self.client.delete('/api/v1/projects', {}, format='json').status_code, (401, 403))

    def test_health_stays_public(self):
        self.assertEqual(self.client.get('/api/v1/health').status_code, 200)

    def test_token_login_then_access(self):
        get_user_model().objects.create_user('alice', password='s3cret-pass')
        token = self.client.post(
            '/api/token', {'username': 'alice', 'password': 's3cret-pass'}, format='json'
        ).json()['access']
        response = self.client.get('/api/v1/projects', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 200)
