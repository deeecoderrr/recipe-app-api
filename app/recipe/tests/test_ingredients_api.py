''' Tests for the ingredients API. '''

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer
from decimal import Decimal

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_user(email='user@user.com', password='user'):
    ''' Create and return user. '''
    return get_user_model().objects.create_user(email, password)

def detail_url(ingredient_id):
    ''' Create and return a ingredient url for a specific id. '''
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


class PublicIngredientApiTest(TestCase):
    ''' Test UnAuthenticated Api Requests. '''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        ''' Test auth required for retrieving ingredients. '''
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):
    ''' Test Authenticated Api Requests. '''

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user = self.user)

    def test_retrieve_ingredients(self):
        ''' Test request to retrieve ingredients. '''

        ingredient_1 = Ingredient.objects.create(
            name = "ingredient1",
            user = self.user
        )

        query_set_ingredient = Ingredient.objects.all().order_by('-name')
        serialized_data = IngredientSerializer(query_set_ingredient, many=True)
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serialized_data.data)


    def test_retrieve_ingredient_restricted_to_specific_user(self):
        ''' Test request to retrieve ingredients specific to authenticated user '''

        user_2 = create_user(email= "user2@user.com", password='user2')
        Ingredient.objects.create(user=user_2, name ='ingredient2')

        ingredient_1 = Ingredient.objects.create(
            name="ingredient1",
            user=self.user
        )

        ingredient_get_queryset = Ingredient.objects.all().order_by('-name')
        serialized_data = IngredientSerializer(ingredient_get_queryset, many=True)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient_1.name)

    def test_update_ingredient(self):
        ''' Test updating a ingredient. '''

        ingredient_1 = Ingredient.objects.create(name="ingredient1",user=self.user)

        ingredient_1_url = detail_url(ingredient_1.id)

        payload = {
            "name": "ingredient11"
        }

        res = self.client.patch(data=payload, path=ingredient_1_url)
        ingredient_1.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["name"], ingredient_1.name)

    def test_delete_ingredient(self):
        ''' Test deleting a ingredient. '''

        ingredient_1 = Ingredient.objects.create(user=self.user,
                                                 name="ingredient1")

        res = self.client.delete(
            detail_url(ingredient_1.id)
        )

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ingredient.objects.all().count(), 0)
        self.assertFalse(Ingredient.objects.filter(user=self.user).exists())

    def test_create_ingredient(self):
        ''' Test creating an Ingredient. '''

        payload = {
            "name":"ingredient1"
        }

        res = self.client.post(data=payload, path=INGREDIENTS_URL)
        ingredient_1 = Ingredient.objects.filter(user=self.user)[0]
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.assertEqual(payload["name"], ingredient_1.name)

    def test_specific_retrieve_ingredient(self):
        """ Test getting detail of a specific ingredient. """

        ingredient_1 = Ingredient.objects.create(user=self.user,
                                                name="ingredient1")
        user2 = create_user(email="email@email.com", password="pass")
        ingredient_2 = Ingredient.objects.create(user=user2,
                                                 name="ingredient12")

        ingredient_1_url = detail_url(ingredient_1.id)
        ingredient_2_url = detail_url(ingredient_2.id)

        res = self.client.get(ingredient_1_url)
        res2 = self.client.get(ingredient_2_url)
        print("res2 data ",res2.data.items())
        print("res2 response ", res.status_code)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for (k,v) in res.data.items():
            self.assertEqual(getattr(ingredient_1, k), v)


    def test_list_ingredients_assigned_to_recipe(self):
        ''' Test list only those ingredients that is assigned to atleast on recipe. '''

        ing1 = Ingredient.objects.create(
            name="pepper",
            user = self.user
        )
        ing2 = Ingredient.objects.create(
            name="cardomen",
            user = self.user,
        )

        recipe_1 = Recipe.objects.create(
            title = "maggie",
            user = self.user,
            time_minutes = Decimal(2),
            price = "25"
        )
        recipe_1.ingredients.add(ing1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only":1})

        s1 = IngredientSerializer(ing1)
        s2 = IngredientSerializer(ing2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)



    def test_list_unique_ingredients_assigned_to_multiple_recipe(self):
        ''' Test list only those unique ingredients that is assigned to multiple on recipe. '''

        ing1 = Ingredient.objects.create(
            name="pepper",
            user = self.user
        )

        recipe_1 = Recipe.objects.create(
            title = "maggie",
            user = self.user,
            time_minutes = Decimal(2),
            price = "25"
        )

        recipe_2 = Recipe.objects.create(
            title="Dosa",
            user=self.user,
            time_minutes=Decimal(10),
            price="75"
        )

        recipe_1.ingredients.add(ing1)
        recipe_2.ingredients.add(ing1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only":1})

        s1 = IngredientSerializer(ing1)

        self.assertIn(s1.data, res.data)
        self.assertEqual(len(res.data), 1)












