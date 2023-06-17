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

    def test_new_user_email_is_normalized(self):
        ''' Test email is normalized for new user '''
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com']
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'Pass@123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_value_error(self):
        ''' Test creating a user without email raises error '''
        with self.assertRaises(ValueError):
            user = get_user_model().objects.create_user('','Pass@123')

    def test_create_super_user(self):
        ''' Testing creating a superuser'''
        user = get_user_model().objects.create_superuser('test1@example.com', 'Pass@123')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
