"""
Characterisation tests: pin down the externally visible CRUD behaviour of every resource
endpoint (status codes, response envelope, what each verb returns, how ids are passed) so the
views can be refactored without changing what the frontend sees.
"""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

LOCMEM_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

# path, id kind, JSON used to create, JSON used to update, create_returns_data, update_returns_data
RESOURCES = [
    ('projects', 'uuid', {'project_name': 'p1'}, {'project_name': 'p2'}, True, False),
    ('grants', 'uuid', {'development_partner': 'd1'}, {'development_partner': 'd2'}, True, False),
    ('grant_partner', 'uuid', {'partner_name': 'g1'}, {'partner_name': 'g2'}, False, True),
    ('development-plans', 'int', {'goalSummary': 'a'}, {'goalSummary': 'b'}, False, True),
    ('deliverables', 'int', {'taskDescription': 'a'}, {'taskDescription': 'b'}, False, True),
    ('mentorship-plans', 'int', {'goals': 'a'}, {'goals': 'b'}, False, True),
    ('skill-assessments', 'int', {'skillDescription': 'a'}, {'skillDescription': 'b'}, True, True),
    ('speaking-engagements', 'int', {'eventDescription': 'a'}, {'eventDescription': 'b'}, True, True),
    ('training-schedules', 'int', {'trainingTopic': 'a'}, {'trainingTopic': 'b'}, True, True),
    ('admin-users', 'int', {'fullName': 'a'}, {'fullName': 'b'}, True, True),
]


@override_settings(CACHES=LOCMEM_CACHE)
class CrudContractTests(APITestCase):
    def setUp(self):
        cache.clear()
        user = get_user_model().objects.create_user('staff', password='p', is_staff=True)
        self.client.force_authenticate(user)

    def _create(self, path, create_body):
        response = self.client.post(f'/api/v1/{path}', create_body, format='json')
        self.assertEqual(response.status_code, 201, (path, response.content))
        return response

    def _first_item(self, path):
        data = self.client.get(f'/api/v1/{path}').json()['data']
        self.assertEqual(len(data), 1, path)
        return data[0]

    def _key(self, item, kind):
        return item['uuid'] if kind == 'uuid' else item['id']

    def test_create_and_list(self):
        for path, kind, create_body, _u, create_returns_data, _ in RESOURCES:
            with self.subTest(path):
                cache.clear()
                body = self._create(path, create_body).json()
                self.assertTrue(body['status'])
                self.assertEqual(body['data'] is not None, create_returns_data, path)
                listing = self.client.get(f'/api/v1/{path}')
                self.assertEqual(listing.status_code, 200)
                self.assertTrue(listing.json()['status'])
                self.assertIsInstance(listing.json()['data'], list)
                self.assertGreaterEqual(len(listing.json()['data']), 1)

    def test_detail_lookup_by_path_or_query(self):
        for path, kind, create_body, _u, _c, _ in RESOURCES:
            with self.subTest(path):
                cache.clear()
                self._create(path, create_body)
                key = self._key(self.client.get(f'/api/v1/{path}').json()['data'][-1], kind)
                if kind == 'int':
                    by_path = self.client.get(f'/api/v1/{path}/{key}')
                    by_query = self.client.get(f'/api/v1/{path}', {'id': key})
                    self.assertEqual(by_path.status_code, 200)
                    self.assertEqual(by_path.json()['data']['id'], key)
                    self.assertEqual(by_query.json()['data']['id'], key)
                elif path == 'grant_partner':
                    by_path = self.client.get(f'/api/v1/{path}/{key}')
                    self.assertEqual(by_path.status_code, 200)
                    self.assertEqual(by_path.json()['data']['uuid'], key)
                else:
                    by_query = self.client.get(f'/api/v1/{path}', {'uuid': key})
                    self.assertEqual(by_query.status_code, 200)
                    self.assertEqual(by_query.json()['data']['uuid'], key)

    def test_update(self):
        for path, kind, create_body, update_body, _c, update_returns_data in RESOURCES:
            with self.subTest(path):
                cache.clear()
                self._create(path, create_body)
                item = self.client.get(f'/api/v1/{path}').json()['data'][-1]
                key = self._key(item, kind)
                if kind == 'int':
                    response = self.client.put(f'/api/v1/{path}/{key}', update_body, format='json')
                else:
                    response = self.client.put(f'/api/v1/{path}', {**update_body, 'uuid': key}, format='json')
                self.assertEqual(response.status_code, 200, (path, response.content))
                self.assertTrue(response.json()['status'])
                self.assertEqual(response.json()['data'] is not None, update_returns_data, path)
                cache.clear()
                after = self.client.get(f'/api/v1/{path}').json()['data'][-1]
                changed_field = next(iter(update_body))
                self.assertEqual(after[changed_field], update_body[changed_field])

    def test_delete(self):
        for path, kind, create_body, _u, _c, _ in RESOURCES:
            with self.subTest(path):
                cache.clear()
                self._create(path, create_body)
                key = self._key(self.client.get(f'/api/v1/{path}').json()['data'][-1], kind)
                if kind == 'int':
                    response = self.client.delete(f'/api/v1/{path}/{key}')
                else:
                    response = self.client.delete(f'/api/v1/{path}', {'uuid': key}, format='json')
                self.assertEqual(response.status_code, 204, path)
                cache.clear()
                self.assertEqual(self.client.get(f'/api/v1/{path}').json()['data'], [])

    def test_missing_records_are_404(self):
        for path, kind, *_ in RESOURCES:
            with self.subTest(path):
                if kind == 'int':
                    self.assertEqual(self.client.get(f'/api/v1/{path}/999999').status_code, 404)
                    self.assertEqual(self.client.put(f'/api/v1/{path}/999999', {}, format='json').status_code, 404)
                    self.assertEqual(self.client.delete(f'/api/v1/{path}/999999').status_code, 404)
                else:
                    missing = '00000000-0000-0000-0000-000000000000'
                    self.assertEqual(self.client.put(f'/api/v1/{path}', {'uuid': missing}, format='json').status_code, 404)
                    self.assertEqual(self.client.delete(f'/api/v1/{path}', {'uuid': missing}, format='json').status_code, 404)
