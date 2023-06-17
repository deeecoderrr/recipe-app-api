''' Test for models '''
from django.test import TestCase
from django.contrib.auth import get_user_model

class ModelTests(TestCase):
    ''' Testing Models '''

    def test_user_create_with_email_successful(self):
        ''' Test creating a user with email is successul '''
        email = "abc@example.com"
        password = "Test@123"

        user = get_user_model().objects.create_user(
            email = email,
            password = password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))