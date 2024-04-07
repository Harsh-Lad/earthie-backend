from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import send_mail
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.db.models import Sum
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, name, phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        ('admin', 'Admin'),
        ('designer', 'Designer'),
        ('print', 'Print'),
        ('user', 'User'),
    )

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=20, choices=ROLES, default='user')
    token = models.CharField(max_length=100, blank=True, null=True)  # Token for verification and password reset
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone_number']

    def __str__(self):
        return self.email
    
@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    if created:
        instance.token = str(uuid.uuid4())  # Generate a unique string token
        instance.save()
        verification_url = f"https://earthie.in/verify-email?token={instance.token}"  # Replace with your actual verification URL
        subject = 'Welcome to Earthie! Please verify your email. ✅'
        html_message = render_to_string('verifyEmail.html', {'name': instance.name, 'link':verification_url})
        plain_message = strip_tags(html_message)
        from_email = 'support@earthie.in'  # Update with your email
        to_email = instance.email
        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)

class HomeSlides(models.Model):
    VISIBILITY_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    name = models.CharField(max_length=255)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='draft')
    desktopImage = models.ImageField(upload_to='desktop_slides/')
    mobileImage = models.ImageField(upload_to='mobile_slides/')

    def __str__(self):
        return self.name


class HomeBlocks(models.Model):
    VISIBILITY_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    name = models.CharField(max_length=255)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='draft')
    blockImage = models.ImageField(upload_to='block_slides/')

    def __str__(self):
        return self.name
    

class Gender(models.Model):
    gender = models.CharField(max_length=20)

    def __str__(self):
        return self.gender

class Collection(models.Model):
    collectionName = models.CharField(max_length=50)
    collectionImage = models.ImageField(upload_to='collection_images/')

    def __str__(self):
        return self.collectionName


class Category(models.Model):
    categoryName = models.CharField(max_length=30)

    def __str__(self):
        return self.categoryName



class Products(models.Model):
    productName = models.CharField(max_length=255)
    price = models.IntegerField()
    isInOffer = models.BooleanField(default=False)
    offerName = models.CharField(max_length=255, null=True, blank=True)
    offerPrice = models.IntegerField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnail/')
    second = models.ImageField(upload_to='second/')
    third = models.ImageField(upload_to='third/')
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.CharField(max_length=255, null=True, blank=True, unique=False)

    def __str__(self):
        return self.productName
    
class Size(models.Model):
    products = models.ForeignKey(Products, on_delete=models.CASCADE)
    sizes = models.CharField(max_length=30)

    def __str__(self):
        return self.sizes

@receiver(post_save, sender=Products)
def create_sizes(sender, instance, created, **kwargs):
    if created:
        sizes = ['S', 'M', 'L', 'XL', 'XXL']
        for size in sizes:
            Size.objects.create(products=instance, sizes=size)

class reviews(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user} for {self.product}"

def generate_random_id():
    return get_random_string(length=32)

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow for both authenticated and anonymous users
    anonymous_id = models.CharField(max_length=255, unique=True, default=generate_random_id)  # Unique identifier for anonymous carts
    total = models.IntegerField(default=0)  # Add a total field to store the cart total
    num_items = models.IntegerField(default=0)  # Add a num_items field to store the total number of unique products in the cart

    def update_total(self):
        cart_items = CartItems.objects.filter(cart=self)
        total = sum(item.product.offerPrice if item.product.isInOffer else item.product.price for item in cart_items)
        self.total = total
        self.num_items = cart_items.count()  # Update the num_items field based on the count of unique products
        self.save()

    def __str__(self):
        if self.user:
            return f"{self.user.name}'s cart"
        else:
            return f"Anonymous Cart (ID: {self.anonymous_id})"

class CartItems(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    size = models.CharField(max_length=255)

# Signal to update the total when a CartItem is saved or deleted
@receiver(post_save, sender=CartItems)
@receiver(post_delete, sender=CartItems)
def update_cart_total(sender, instance, **kwargs):
    instance.cart.update_total()



class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    anonymous_id = models.CharField(max_length=255, unique=True, default=generate_random_id)


    def __str__(self):
        if self.user:
            return f"{self.user.name}'s wishlist"
        else:
            return f"Anonymous Wishlist (ID: {self.anonymous_id})"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('wishlist', 'product')  # Ensure unique products in wishlist


class Order(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('order placed', 'Order Placed'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('return', 'Return'),
        ('returned', 'Returned'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    orderid = models.CharField(max_length=255)

    def __str__(self):
        return f"Order for {self.user.name}"

class OrderItems(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    email = models.CharField(max_length=255)
    orderItem = models.ForeignKey(Products, on_delete=models.CASCADE)
    size = models.CharField(max_length=255)

    def __str__(self):
        return self.order.firstName


