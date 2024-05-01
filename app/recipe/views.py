''' Views for Recipe Apis '''


from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes
)

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Recipe, Tag, Ingredient
from recipe import serializers

@extend_schema_view(
    list = extend_schema(
        parameters= [
            OpenApiParameter(
                "assigned_only",
                OpenApiTypes.INT, enum=[0,1],
                description="IF you want to get the list of those items that is tagged with atleast recipe"
            ),
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.RetrieveModelMixin ,
                            mixins.CreateModelMixin,
                            mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    ''' Base class for Recipe Attributes. '''

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ filter queryset to authenticated users. """
        assigned_only = bool(self.request.query_params.get("assigned_only", 0))
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(user=self.request.user).order_by("-name").distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema_view(
    list = extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag ids to filter',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient ids to filter',
            ),

        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    ''' View for manage Recipe Apis '''

    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_int(self, qs):
        """ Convert a list of strings to integers """
        return [int(i) for i in qs.split(',')]

    def get_queryset(self):
        ''' Retrieve recipes for authenticated users '''
        print("inside get_queryset for RecipeViewSet")
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_int(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_int(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(user=self.request.user).order_by('-id').distinct()

    def get_serializer_class(self):
        ''' Return the serializer class as per request '''
        print(f"inside get_serializer_class for RecipeViewSet action {self.action}")
        if self.action == 'list':
            return serializers.RecipeSerializer

        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        ''' Create a new recipe '''
        print("inside perform_create for RecipeViewSet")
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """ Upload an image to recipe. """
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TagViewSet(BaseRecipeAttrViewSet):
    """ View to manage Tags Api """

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """ View to manage Ingredient Api """

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()











