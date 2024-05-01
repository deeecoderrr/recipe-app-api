'''
Tests for the User API.
'''

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
CREATE_TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    '''Create and return a new user. '''
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):
    '''' Test the public features of the User API '''
    def setUp(self) -> None:
        self.client = APIClient()

    def test_user_create_success(self):
        ''' Test creating user is successful. '''
        payload = {
            'email':'TestCheck@gmail.com',
            'password':'testpass@123',
            'name':'Test Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email = payload['email'])

        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password',res.data)

    def test_user_with_email_exists_error(self):
        ''' Test if user with email exists '''
        payload = {
            'email':'TestCheck@gmail.com',
            'password':'testpass@123',
            'name':'Test Name'
        }

        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        ''' Test return too short error if password less than 5 chars '''
        payload = {
            'email':'TestCheck@gmail.com',
            'password':'tes',
            'name':'Test Name'
        }

        res =  self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email = payload["email"]).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        ''' Test to create token for the user '''
        user_details = {
            'email':'TestCheck@gmail.com',
            'password':'tes@123',
            'name':'Test Name'
        }
        create_user(**user_details)

        payload = {
            'email':'TestCheck@gmail.com',
            'password':'tes@123',
        }

        res = self.client.post(CREATE_TOKEN_URL, payload)
        print(res.data)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_create_token_bad_cred(self):
        ''' Test return error if creds invalid  or blank '''
        user_details = {
            'email':'TestCheck@gmail.com',
            'password':'tes@123',
            'name':'Test Name'
        }
        create_user(**user_details)

        payload = {
            'email':'TestCheck@gmail.com',
            'password':'tefef4242',
        }

        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        ''' Test authorization is required for users '''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateUserApiTests(TestCase):
    """ Test Api Requests that require Authentication """

    def setUp(self) -> None:
        self.user = create_user(
            email = 'Test@gmail.com',
            password = "Test@123",
            name = "Test Name"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_profile_success(self):
        ''' Test retrieving profile for logged in user '''

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name':self.user.name,
            'email':self.user.email
        })

    def test_post_me_not_allowed(self):
        " Test Post request not allowed for ME endpoint "

        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        ''' Test update profile for the authenticated user '''

        payload = {'name':'updatedName', 'password':'upadtedPassword'}
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)














