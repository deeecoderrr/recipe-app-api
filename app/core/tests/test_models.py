''' Test for models '''

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from core import models


def create_user():
    ''' Create and return a user '''
    return get_user_model().objects.create_user(
        email = 'test@example.com',
        password = 'Test@123'
    )

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

    def test_create_a_recipe(self):
        ''' Test creating a recipe is successfull '''

        user = get_user_model().objects.create_user(
            'test@example.com',
            'test@password.com'
        )

        recipe = models.Recipe.objects.create(
            user = user,
            title = 'Test Recipe',
            time_minutes = 5,
            price = Decimal('5.50'),
            description = 'Test Recipe Description'
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_a_tag(self):
        ''' Test creating a tag is successfull '''
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)


    def test_create_ingredient(self):
        ''' Test creating a ingredient is successful '''

        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Ingredient1'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        ''' Test generating image path. '''

        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')
        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')


