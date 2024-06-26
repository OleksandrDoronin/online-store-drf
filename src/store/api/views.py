from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, generics, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from store.api.filters import ProductFilter
from permissions import IsAdmin
from store.models import Product, Category
from store.api.serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductDetailSerializer,
    ProductSearchSerializer,
    ProductPartialUpdateSerializer,
)


class ProductSearchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A view set for searching products.
    """

    queryset = Product.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProductFilter

    # Select serializer based on the action
    def get_serializer_class(self):
        action_serializers_dict = {
            "list": ProductSearchSerializer,
            "retrieve": ProductDetailSerializer,
        }
        serializer = action_serializers_dict.get(self.action)
        if not serializer:
            raise Exception(f"Serializer for {self.action=} is not exist")
        return serializer

    # Parameters for filtering products
    CATEGORY = openapi.Parameter(
        name="category",
        in_=openapi.IN_QUERY,
        description="Filter products by category. Use commas to specify multiple categories.",
        type=openapi.TYPE_STRING,
    )
    MIN_PRICE = openapi.Parameter(
        name="min_price",
        in_=openapi.IN_QUERY,
        description="Filter products by minimum price.",
        type=openapi.TYPE_NUMBER,
    )
    MAX_PRICE = openapi.Parameter(
        name="max_price",
        in_=openapi.IN_QUERY,
        description="Filter products by maximum price.",
        type=openapi.TYPE_NUMBER,
    )
    NAME = openapi.Parameter(
        name="name",
        in_=openapi.IN_QUERY,
        description="Filter products by name. Search is case-insensitive.",
        type=openapi.TYPE_STRING,
    )

    @swagger_auto_schema(
        operation_description="API endpoint for listing products with optional filters.",
        manual_parameters=[CATEGORY, MIN_PRICE, MAX_PRICE, NAME],
        responses={
            200: openapi.Response(
                "List of products.", ProductDetailSerializer(many=True)
            )
        },
        operation_id="ListProducts",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="API endpoint for retrieving a product by ID.",
        responses={200: openapi.Response("Product details.", ProductDetailSerializer)},
        operation_id="RetrieveProductByID",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CategorySearchAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    @swagger_auto_schema(
        operation_description="API endpoint for listing categories.",
        responses={200: openapi.Response("List of categories", CategorySerializer)},
        operation_id="ListCategories",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ProductCreateAPIView(generics.GenericAPIView):
    """
    A view for creating a new product.
    """

    serializer_class = ProductSerializer
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(
        operation_description="API endpoint for creating a new product.",
        request_body=ProductSerializer,
        responses={201: openapi.Response("Product created.", ProductSerializer)},
        operation_id="CreateProduct",
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        # Check data validity
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check the existence of the specified category
        try:
            category = Category.objects.get(id=serializer.validated_data["category_id"])
        except ObjectDoesNotExist:
            return Response(
                {"message": "This category doesn't exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check the existence of a product with the specified name
        if Product.objects.filter(name=serializer.validated_data["name"]).exists():
            return Response(
                {"message": "A product with the same name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        product = Product.objects.create(
            name=serializer.validated_data["name"],
            category=category,
            price=serializer.validated_data["price"],
            quantity=serializer.validated_data["quantity"],
            discount=serializer.validated_data["discount"],
            available=serializer.validated_data["available"],
            cost_price=serializer.validated_data["cost_price"],
        )
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailUpdateAPIView(
    generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.DestroyModelMixin
):
    """
    A view for retrieving and updating a product.
    """

    queryset = Product.objects.all()
    permission_classes = (IsAdmin,)

    def get_serializer_class(self):
        method = self.request.method.lower()
        action_serializers_dict = {
            "put": ProductSerializer,
            "patch": ProductPartialUpdateSerializer,
            "get": ProductSerializer,
        }
        serializer_class = action_serializers_dict.get(method)
        if not serializer_class:
            raise Exception(f"Serializer for {method=} does not exist.")
        return serializer_class

    @swagger_auto_schema(
        operation_description="API endpoint for retrieving a product by ID.",
        responses={200: openapi.Response("Product details.", ProductSerializer)},
        operation_id="RetrieveProductByIDStaff",
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="API endpoint for updating a product by ID.",
        responses={200: openapi.Response("Product updated.", ProductSerializer)},
        operation_id="UpdateProduct",
    )
    def put(self, request, **kwargs):
        return self.update_product(request, **kwargs)

    @swagger_auto_schema(
        operation_description="API endpoint for partially updating a product by ID.",
        responses={200: openapi.Response("Product updated.", ProductSerializer)},
        operation_id="PartialUpdateProduct",
    )
    def patch(self, request, **kwargs):
        return self.update_product(request, **kwargs, partial=True)

    @swagger_auto_schema(
        operation_description="API endpoint for deleting a product.",
        responses={204: openapi.Response("Product deleted.")},
        operation_id="DeleteProduct",
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def update_product(self, request, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        for attr, value in serializer.validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return Response(ProductSerializer(instance).data, status=status.HTTP_200_OK)


class CategoryCreateAPIView(generics.GenericAPIView):
    """
    A view for creating a new category.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(
        operation_description="API endpoint for creating a new category.",
        operation_id="CreateCategory",
        request_body=CategorySerializer,
        responses={201: openapi.Response("Category.", CategorySerializer)},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        category_name = serializer.validated_data["name"]
        try:
            Category.objects.get(name=category_name)
            return Response(
                {"message": "A category with the same name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ObjectDoesNotExist:
            category = Category.objects.create(name=category_name)
            return Response(
                CategorySerializer(category).data, status=status.HTTP_201_CREATED
            )


class CategoryDetailAPIView(generics.RetrieveDestroyAPIView):
    """
    A view for retrieving or deleting a category by ID.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdmin, IsAuthenticated)

    @swagger_auto_schema(
        operation_description="API endpoint for retrieving a category by ID.",
        responses={200: openapi.Response("Category details.", ProductSerializer)},
        operation_id="RetrieveProductByIDStaff",
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="API endpoint for deleting a category by ID.",
        operation_id="DeleteCategoryByIDStaff",
        responses={204: openapi.Response(description="Category deleted successfully.")},
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
