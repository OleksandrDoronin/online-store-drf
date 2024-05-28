from decimal import Decimal
from rest_framework import serializers
from config.constants import LOSS_FACTOR
from store.api.mixins import DiscountPriceMixin


# Serializer for listing products.
class ProductSearchSerializer(DiscountPriceMixin, serializers.Serializer):
    name = serializers.CharField(read_only=True)
    price = serializers.FloatField(read_only=True)
    discounted_price = serializers.SerializerMethodField(read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return self.remove_discount_fields(data)


# Serializer for retrieving a product.
class ProductDetailSerializer(DiscountPriceMixin, serializers.Serializer):
    name = serializers.CharField(read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)
    price = serializers.FloatField(read_only=True)
    discounted_price = serializers.SerializerMethodField(read_only=True)
    discount = serializers.IntegerField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    updated_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return self.remove_discount_fields(data)


# Serializer for handling CRUD operations on Product objects.
class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)
    category = serializers.CharField(max_length=25)
    price = serializers.FloatField()
    quantity = serializers.IntegerField()
    discount = serializers.IntegerField(default=0)
    available = serializers.BooleanField(default=True)
    cost_price = serializers.FloatField()
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    updated_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    def validate(self, attrs):
        """
        Validates the product price after applying a discount to ensure it does not fall below its cost price.
        """
        cost_price = Decimal(attrs.get("cost_price", 0))
        price = Decimal(attrs.get("price", 0))
        discount = Decimal(attrs.get("discount", 0))

        # Calculate the minimum acceptable price after discount
        min_acceptable_price = cost_price * LOSS_FACTOR
        discounted_price = price * (1 - discount / 100)

        # Check if the discounted price falls below the cost price
        if discounted_price < min_acceptable_price:
            raise serializers.ValidationError(
                "Product price after applying discount cannot be lower than the cost price."
            )
        return attrs


# Serializer for handling Create, Read, and Delete operations on Category objects.
class CategorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
