from rest_framework import serializers
from .models import User, HomeSlides, HomeBlocks, Category, Collection, Gender, Size, Products, reviews, Cart, CartItems, Wishlist, WishlistItem, Order, OrderItems


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'name', 'phone_number', 'password']
        extra_kwargs = {'password': {'write_only': True}}  # Hide password in response

    def create(self, validated_data):
        # Extract password from validated data
        password = validated_data.pop('password', None)

        # Create user instance without saving it to the database yet
        user = User(**validated_data)

        if password is not None:
            # Set the password using Django's set_password method
            user.set_password(password)

        # Save the user instance with hashed password
        user.save()
        return user

    def update(self, instance, validated_data):
        # Extract password from validated data if provided
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password is not None:
            # Set the password using Django's set_password method
            instance.set_password(password)

        # Save the updated user instance with hashed password
        instance.save()
        return instance

class HomeSlidesSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeSlides
        fields = ['name', 'visibility', 'desktopImage', 'mobileImage']

class HomeBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeBlocks
        fields = ['name', 'visibility', 'blockImage']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        depth = 1

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = '__all__'
        depth = 1

class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = '__all__'
        depth = 1

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'
        depth = 1

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = '__all__'
        depth = 1

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = reviews
        fields = '__all__'
        depth = 1

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartItems
        fields = ('product', 'id', 'size')  # Include the ID for cart item management

class CartSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    num_items = serializers.SerializerMethodField()
    items = CartItemSerializer(many=True, read_only=True)

    def get_total(self, obj):
        return obj.total

    def get_num_items(self, obj):
        return obj.num_items

    class Meta:
        model = Cart
        fields = ('id', 'user', 'anonymous_id', 'total', 'num_items', 'items')

class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer() 

    class Meta:
        model = WishlistItem
        fields = ('product',)  # Include the size for the wishlist item
        depth = 1


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ('id', 'user', 'anonymous_id', 'items')

    def create(self, validated_data):
        # Extract items data from validated_data
        items_data = validated_data.pop('items', [])

        # Create wishlist instance
        wishlist = Wishlist.objects.create(**validated_data)

        # Create wishlist items
        for item_data in items_data:
            WishlistItem.objects.create(wishlist=wishlist, **item_data)

        return wishlist
    
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class OrderItemsSerializer(serializers.ModelSerializer):
    orderItem = ProductSerializer()
    class Meta:
        model = OrderItems
        fields = '__all__'