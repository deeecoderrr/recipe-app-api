'''
Tests for the tags API
'''

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer
from decimal import Decimal

TAGS_URL = reverse('recipe:tag-list')


def create_user(email='user@example.com', password='testpass123'):
    """ Create and return a user. """
    return get_user_model().objects.create_user(email=email, password=password)

def create_url(tag_id):
    """ create and return tag detail url """
    return reverse('recipe:tag-detail',args=[tag_id])

class PublicTagsApiTests(TestCase):
    ''' Test unauthenticated API requests. '''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required for getting tags.'''
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    ''' Test authenticated API requests. '''

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """ Test retrieving a list of tags. """
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="desert")

        res = self.client.get(TAGS_URL)
        # Reverse name order
        tags = Tag.objects.all().order_by("-name")
        # serialize the query set containing list of tag objects
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_retrieve_limited_to_user(self):
        tag_1 = Tag.objects.create(user=self.user, name="Tag1")
        # creating another user
        user2 = create_user(email="hrsht@gmail.com")
        Tag.objects.create(user=user2, name="Tag2")
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]["name"], tag_1.name)
        self.assertEqual(res.data[0]["id"], tag_1.id)

    def test_tags_update(self):
        """ Tests updating a tag """
        tag = Tag.objects.create(user=self.user, name="After Dinner")

        data = {"name":"Before Dinner"}
        url = create_url(tag.id)
        res = self.client.patch(data=data,path=url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, data["name"])

    def test_tags_delete(self):
        """ Tests deleting a tag """
        tag = Tag.objects.create(user= self.user, name="Dessert")

        url = create_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_list_tags_assigned_to_recipe(self):
        ''' Test list only those tags that is assigned to atleast on recipe. '''

        tag1 = Tag.objects.create(
            name="pepper",
            user=self.user
        )
        tag2 = Tag.objects.create(
            name="cardomen",
            user=self.user,
        )

        recipe_1 = Recipe.objects.create(
            title="maggie",
            user=self.user,
            time_minutes=Decimal(2),
            price="25"
        )
        recipe_1.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_list_unique_ingredients_assigned_to_multiple_recipe(self):
        ''' Test list only those unique ingredients that is assigned to multiple on recipe. '''

        tag1 = Tag.objects.create(
            name="pepper",
            user=self.user
        )

        recipe_1 = Recipe.objects.create(
            title="maggie",
            user=self.user,
            time_minutes=Decimal(2),
            price="25"
        )

        recipe_2 = Recipe.objects.create(
            title="Dosa",
            user=self.user,
            time_minutes=Decimal(10),
            price="75"
        )

        recipe_1.tags.add(tag1)
        recipe_2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)

        self.assertIn(s1.data, res.data)
        self.assertEqual(len(res.data), 1)





































