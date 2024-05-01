''' Serializers for Recipe Apis. '''

from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    ''' Serializer for Ingredient API '''

    class Meta:
        model = Ingredient
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return Ingredient.objects.create(**validated_data)

class TagSerializer(serializers.ModelSerializer):
    """ Serializer for tag api """
    print("Inside TagSerializer")
    class Meta:
        print("Inside Meta of TagSerializer")
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """ Create a new tag """
        print("Inside create of TagSerializer")
        print(validated_data)
        validated_data["user"] = self.context["request"].user
        return Tag.objects.create(**validated_data)


class RecipeSerializer(serializers.ModelSerializer):
    ''' Serializer for Recipe Api '''
    print("Inside RecipeSerializer")
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        print("Inside Meta of RecipeSerializer")
        model = Recipe
        fields = ['id', 'title',  'time_minutes',  'price', 'link', 'tags', 'ingredients']
        read_only_fields = ['id']

    def _get_or_create_tags(self, recipe, tags):
        """ Handle getting or creating tags as needed """
        print("Inside _get_or_create_tags of RecipeSerializer")
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, is_created = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, recipe, ingredients):
        """ Handle getting or creating ingredients as needed. """
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, is_created = Ingredient.objects.get_or_create(user=auth_user, **ingredient)
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """ Create a new recipe """
        print("Inside create of RecipeSerializer")
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        print("calling _get_or_create_tags from create of RecipeSerializer")
        self._get_or_create_tags(recipe, tags)
        self._get_or_create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """ Update recipe """
        print("Inside update of RecipeSerializer")
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            print("calling _get_or_create_tags from update of RecipeSerializer")
            self._get_or_create_tags(instance, tags)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(instance, ingredients)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    ''' Serializer for recipe detail Api. '''
    print("Inside RecipeDetailSerializer")

    class Meta(RecipeSerializer.Meta):
        print("Inside Meta of RecipeDetailSerializer")
        fields = RecipeSerializer.Meta.fields + ['description', 'image']


class RecipeImageSerializer(serializers.ModelSerializer):
    """ Serializer for uploading images to recipe. """

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {"required": True}}



