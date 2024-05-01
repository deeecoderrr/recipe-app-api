''' Test for Recipe APISc'''

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def create_recipe(user, **params):
    ''' Create and return a sample recipe. '''

    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'https://example.com/recipe.pdf'
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def create_user(**params):
    ''' Helper function to create and return user '''
    return get_user_model().objects.create_user(**params)

def get_detail_url(recipe_id):
    ''' create and return a dynamic get detail url for a specific recipe '''
    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    ''' create and return image upload url. '''
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


class PublicRecipeApiTest(TestCase):
    ''' Test unauthenticated API requests. '''

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        ''' Test auth is required to call API '''

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeApiTest(TestCase):
    ''' Test authenticated Api requests '''

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(
            email = 'user@gmail.com',
            password = 'password@123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe(self):
        ''' Test retrieving list of APIs '''

        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')

        serialized_data = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serialized_data.data)

    def test_list_of_recipe_limited_to_specific_user(self):
        ''' Test list of recipe limted to authenticated users. '''

        other_user = create_user(
            email = 'otheruser@test.com',
            password = 'other@123'
        )

        create_recipe(user = self.user)
        create_recipe(user = other_user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serialized_data = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serialized_data.data)

    def test_get_recipe_detail(self):
        ''' Test get recipe detail '''

        recipe = create_recipe(user=self.user)

        res = self.client.get(get_detail_url(recipe.id))

        serialized_data = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serialized_data.data)

    def test_create_recipe(self):
        ''' Test creating a recipe '''

        payload = {
            'title': 'Test title',
            'time_minutes': 30,
            'price':Decimal('5.5')
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(recipe.user, self.user)
        for (k,v) in payload.items():
            self.assertEqual(getattr(recipe, k),v)

    def test_partial_update(self):
        ''' test to partial update recipe fields using recipe api '''

        original_link = 'https://www.originallink.com/original.pdf'
        recipe = create_recipe(
            user = self.user,
            title = "Original Test Title",
            link = original_link
        )

        payload = {
            'title': 'Changed Test Title.'
        }

        res = self.client.patch(get_detail_url(recipe_id=recipe.id), payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        ''' test to full update recipe fields using recipe api '''

        recipe = create_recipe(
            user = self.user,
        )

        payload = {
        'title': 'New recipe title',
        'time_minutes': 23,
        'price': Decimal('5.35'),
        'description': 'New Sample description',
        'link': 'https://example.com/new.pdf'
    }

        res = self.client.put(get_detail_url(recipe_id=recipe.id), payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.user, self.user)

        for (k,v) in payload.items():
            self.assertEqual(getattr(recipe, k), v)

    def test_update_user_return_error(self):
        ''' Updating the user for the specific user return error '''

        new_user = create_user(email='user2@gmail.com', password = 'test@gmail.com')
        recipe = create_recipe(self.user)

        payload = {
            'user': new_user.id
        }

        url = get_detail_url(recipe.id)

        res = self.client.patch(
            url, payload
        )

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        ''' Test deleting a recipe '''

        recipe = create_recipe(self.user)

        url =  get_detail_url(recipe_id=recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_deleting_other_users_recipe_error(self):
        ''' Test trying to delete other users recipe gives error '''

        other_user = create_user(
            email = "other@example.com",
            password = 'Test@1234'
        )

        recipe = create_recipe(user = other_user)

        url = get_detail_url(recipe_id=recipe.id)

        res = self.client.delete(url)
        recipe.refresh_from_db()


        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        ''' test creating recipe with new tags '''

        data = {
            'title': 'Sample recipe title',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'tags': [{"name":"tag1"},{"name":"tag2"}],
        }

        res = self.client.post(RECIPE_URL, data=data, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipies = Recipe.objects.filter(user=self.user)
        print('Created', recipies)
        self.assertEqual(recipies.count(),1 )
        recipe = recipies[0]
        print("Tags",recipe.tags.all())
        self.assertEqual(recipe.tags.count(),2)

        for tag in data["tags"]:
            self.assertTrue(recipe.tags.filter(name=tag["name"],
                                               user=self.user).exists())

    def test_create_recipe_with_existing_tags(self):
        ''' test creating recipe with new tags '''

        indian_tag = Tag.objects.create(name="Indian", user=self.user)

        data = {
            'title': 'Sample recipe title',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'tags': [{"name":"Indian"},{"name":"tag2"}],
        }

        res = self.client.post(RECIPE_URL, data=data, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipies = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipies.count(),1 )
        recipe = recipies[0]
        self.assertEqual(recipe.tags.count(),2)
        self.assertIn(indian_tag, recipe.tags.all())
        for tag in data["tags"]:
            self.assertTrue(recipe.tags.filter(name=tag["name"],
                                               user=self.user).exists())


    def test_new_tag_is_created_when_updating_prexisting_recipe_with_new_tags(self):
        ''' test updating recipe creates new tags when updating recipe with new tags '''

        recipe = create_recipe(user=self.user)
        recipe_detail_url = get_detail_url(recipe.id)
        data = {
            "tags": [{"name": "Indian"}],
        }
        res = self.client.patch(recipe_detail_url, data=data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name=data["tags"][0]["name"])
        self.assertIn(new_tag, recipe.tags.all())

    def test_assigining_existing_tags_when_updating_existing_recipe(self):
        ''' test assigining existing tags when updating existing recipe which already has tags '''

        tag_indian = Tag.objects.create(user=self.user, name="Indian")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_indian)
        recipe_detail_url = get_detail_url(recipe.id)
        data = {
            "tags": [{"name": "Lunch"}],
        }
        res = self.client.patch(recipe_detail_url, data=data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag_indian, recipe.tags.all())
        self.assertIn(Tag.objects.get(user=self.user, name="Lunch"), recipe.tags.all())

    def test_clear_all_assigned_tags_when_updating_existing_recipe(self):
        ''' test clear all assigned tags when updating existing recipe '''

        tag_indian = Tag.objects.create(user=self.user, name="Indian")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_indian)
        recipe_detail_url = get_detail_url(recipe.id)
        data = {
            "tags": [],
        }
        res = self.client.patch(recipe_detail_url, data=data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        ''' Test creating a recipe with new ingredients. '''

        payload = {
            'title': 'Test Recipe with ingredients',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients': [
                {
                    "name": "ing-1"
                },
                {
                    "name": "ing-2"
                }
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient["name"],
                                        user=self.user
                                        ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        ''' Test creating a recipe with pre-existing ingredient passed in payload. '''

        ing_1 = Ingredient.objects.create(
            name="ing-1",
            user=self.user
        )


        payload = {
            'title': 'Test Recipe with ingredients',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients': [
                {
                    "name": "ing-1"
                },
                {
                    "name": "ing-2"
                }
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(
            user=self.user
        )

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            )
            self.assertTrue(exists)

    def test_create_a_ingredient_on_update_recipe(self):
        ''' Test creating a ingredient when updating a recipe. '''

#       Let create a recipe
        recipe = create_recipe(user=self.user)
#       run patch on the recipe by passing new ingredient data on the recipe id
        data = {
            "ingredients" : [{
                "name": "ing-1"
            },
                {
                    "name": "ing-2"
                }]
        }
        self.assertEqual(recipe.ingredients.count(), 0)
        res = self.client.patch(data=data, path=get_detail_url(recipe_id=recipe.id), format='json')
#       test if the recipe is updated with the new ingredient and also if the ingredient are created

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in data["ingredients"]:
            self.assertTrue(recipe.ingredients.filter(user=self.user, name=ingredient["name"]).exists())


    def test_assign_preexisting_ingredient_on_update_recipe(self):

        recipe = create_recipe(self.user)

        ing_1 = Ingredient.objects.create(user=self.user, name="ing-1")
        recipe.ingredients.add(ing_1)

        ing_2 = Ingredient.objects.create(user=self.user, name="ing-2")

        data = {
            "ingredients": [{
                "name": "ing-2"
            }]
        }

        res = self.client.patch(data=data, path=get_detail_url(recipe.id), format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.all().count(), 1)

        self.assertTrue(recipe.ingredients.filter(user=self.user, name=data["ingredients"][0]["name"]))




    def test_clear_recipe_ingredient(self):
        """ test clearing the ingredients from recipe. """
        recipe = create_recipe(self.user)

        ing_1 = Ingredient.objects.create(user=self.user, name="ing-1")
        recipe.ingredients.add(ing_1)

        data = {
            "ingredients": []
        }

        res = self.client.patch(data=data, path=get_detail_url(recipe.id), format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.all().count(), 0)


class ImageUploadTests(TestCase):
    ''' Test for the image upload API. '''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email = "deecoderr@gmail.com",
            password="1234"
        )
        self.client.force_authenticate(self.user)

        self.recipe = create_recipe(
            user = self.user
        )

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        ''' Test uploading image to a recipe. '''

#       create a url to post for image upload
        url = image_upload_url(recipe_id=self.recipe.id)
#       create a temp file to craft the image to be loaded to payload
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new('RGB', (10,10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            data = {"image": image_file}
            res = self.client.post(data=data, path=url, format='multipart')
            self.recipe.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)

            self.assertIn('image', res.data)
            self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        ''' Test uploading invalid image. '''

        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_tags(self):
        ''' Test filtering recipe by tags. '''

        r1 = create_recipe(user=self.user, title= "Thai Vegetable")
        r2 = create_recipe(user=self.user, title= "Aubergine")

        tag1 = Tag.objects.create(user=self.user, name="Vegan")
        tag2 = Tag.objects.create(user=self.user, name="Vegetarian")

        r1.tags.add(tag1)
        r2.tags.add(tag2)

        r3 = create_recipe(user=self.user, title= "Fish")

        params = {'tags': f"{tag1.id},{tag2.id}"}

        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data , res.data)
        self.assertIn(s2.data , res.data)
        self.assertNotIn(s3.data , res.data)


    def test_filter_by_ingredients(self):
        ''' Test filtering recipe by ingredients. '''

        r1 = create_recipe(user=self.user, title= "Thai Vegetable")
        r2 = create_recipe(user=self.user, title= "Aubergine")

        ing1 = Tag.objects.create(user=self.user, name="pepper")
        ing2 = Tag.objects.create(user=self.user, name="turmeric")

        r1.tags.add(ing1)
        r2.tags.add(ing2)

        r3 = create_recipe(user=self.user, title= "Dahi bada")

        params = {'tags': f"{ing1.id},{ing2.id}"}

        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data , res.data)
        self.assertIn(s2.data , res.data)
        self.assertNotIn(s3.data , res.data)
















