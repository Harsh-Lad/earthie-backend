from rest_framework.response import Response
from rest_framework.decorators import api_view,  permission_classes, authentication_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated , AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.contrib.auth.decorators import login_required
from .serializers import CustomUserSerializer, HomeSlidesSerializer, HomeBlockSerializer, CategorySerializer, CollectionSerializer, GenderSerializer, ProductSerializer, CartSerializer, CartItemSerializer, WishlistItemSerializer, WishlistSerializer, OrderSerializer, OrderItemsSerializer
from .models import User,HomeSlides, HomeBlocks , Category, Collection, Gender, Products, Cart , CartItems, WishlistItem, Wishlist, Order, OrderItems
from django.db.models import Q
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import AuthenticationFailed
import razorpay
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import uuid
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class EmailVerificationRequired(AuthenticationFailed):
    default_detail = 'Email not verified.'
    default_code = 'email_not_verified'

class EmailNotFound(AuthenticationFailed):
    default_detail = 'Email not found.'
    default_code = 'email_not_found'

class InvalidCredentials(AuthenticationFailed):
    default_detail = 'Invalid credentials.'
    default_code = 'invalid_credentials'

class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        if not user.is_verified:
            raise EmailVerificationRequired("Please verify your account.")
        
        token = super().get_token(user)
        
        # Add custom claims
        token['name'] = user.name
        # ...

        return token

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')

        if email and password:
            user = self.user_exists(email)
            if user:
                if not user.check_password(password):
                    raise InvalidCredentials("Invalid credentials.")
                if not user.is_verified:
                    raise EmailVerificationRequired("Please verify your account.")
            else:
                raise EmailNotFound("Email not found.")
        else:
            raise InvalidCredentials("Invalid credentials.")

        return super().validate(attrs)

    def user_exists(self, email):
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            return None


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

# Create your views here.
@api_view(('POST',))
def register(request):
    if request.method == 'POST':
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # send activation email there is activationDone.html and activationDone.txt
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_home_slides(request):
    if request.method == 'GET':
        slides = HomeSlides.objects.filter(visibility='published')
        serializer = HomeSlidesSerializer(slides, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def get_home_blocks(request):
    if request.method == 'GET':
        slides = HomeBlocks.objects.filter(visibility='published')
        serializer = HomeBlockSerializer(slides, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

#---------------------------------------------------------------------------



@api_view(['GET'])
def product_list(request):
    query_params = request.query_params
    products = Products.objects.all()

    # Filter products based on query parameters
    if 'new_arrivals' in query_params:
        range_param = query_params.get('range')

        if range_param is not None:
            try:
                range_count = int(range_param)
                if range_count > 0:
                    products = products.order_by('-created_at')[:range_count]
                else:
                    return Response({'error': 'Invalid range count'}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({'error': 'Invalid range parameter'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            products = products.order_by('-created_at')

    if 'offers' in query_params:
        products = products.filter(isInOffer=True)

    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)



@api_view(['GET', 'PUT', 'DELETE'])
def product_detail(request, pk):
    try:
        product = Products.objects.get(pk=pk)
    except Products.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def search_products(request):
    query_params = request.query_params.get('query', '')
    if query_params:
        products = Products.objects.filter(Q(productName__icontains=query_params) | Q(tags__icontains=query_params))
    else:
        products = Products.objects.all()

    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET',])
def collection_list(request):
    try:
        collections = Collection.objects.all()
        serializer = CollectionSerializer(collections, many=True)
        if 'collection_name' in request.query_params:
            collection_name = request.query_params.get('collection_name')
            filtered_collections = Collection.objects.filter(collectionName__icontains=collection_name)
            if filtered_collections.exists():  # Check if any collections match
                collection = filtered_collections.first()  # Get the first matching collection
                products = Products.objects.filter(collection=collection)
                product_serializer = ProductSerializer(products, many=True)
                return Response({'collections': serializer.data, 'products': product_serializer.data})
            else:
                # Handle the case where no collection is found
                return Response({'error': 'No collection found with that name'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'collections': serializer.data})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])  # Replace YourAuthenticationClass with the authentication class you are using
@permission_classes([IsAuthenticated])
def add_to_wishlist_authenticated(request):
    product_id = request.data.get('product_id')

    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product_id=product_id)

    if not created:
        return Response({"message": "Product already exists in the wishlist."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Product added to wishlist."}, status=status.HTTP_201_CREATED)



@api_view(['POST'])
@permission_classes([AllowAny])  # Allow anonymous users to add to wishlist
def add_to_wishlist_anonymous(request):
    product_id = request.data.get('product_id')
    anonymous_id = request.data.get('anonymous_id')

    # If anonymous_id is not provided, create a wishlist with a unique anonymous_id
    if not anonymous_id:
        wishlist = Wishlist.objects.create()
        anonymous_id = wishlist.anonymous_id
    else:
        # If anonymous_id is provided, get or create the wishlist
        wishlist, _ = Wishlist.objects.get_or_create(anonymous_id=anonymous_id)

    # Add the product to the wishlist
    wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product_id=product_id)

    if not created:
        return Response({"message": "Product already exists in the wishlist.", "anonymous_id": anonymous_id}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Product added to wishlist.", "anonymous_id": anonymous_id}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_wishlist_authenticated(request):
    try:
        product_id = request.data.get('product_id')

        # Get the wishlist item associated with the product id and the authenticated user
        wishlist_item = WishlistItem.objects.get(wishlist__user=request.user, product_id=product_id)
        wishlist_item.delete()

        return Response({"message": "Product removed from wishlist."}, status=status.HTTP_200_OK)
    except WishlistItem.DoesNotExist:
        return Response({"message": "Product not found in the wishlist."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])  # Allow anonymous users to remove from wishlist
def remove_from_wishlist_anonymous(request):
    try:
        product_id = request.data.get('product_id')
        anonymous_id = request.data.get('anonymous_id')

        # Get the wishlist item associated with the product id and the anonymous id
        wishlist_item = WishlistItem.objects.get(wishlist__anonymous_id=anonymous_id, product_id=product_id)
        wishlist_item.delete()

        return Response({"message": "Product removed from wishlist."}, status=status.HTTP_200_OK)
    except WishlistItem.DoesNotExist:
        return Response({"message": "Product not found in the wishlist."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_wishlist_items(request):
    try:
        # Get the wishlist associated with the authenticated user
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)

        # Get all items in the wishlist
        wishlist_items = WishlistItem.objects.filter(wishlist=wishlist)
        
        # Serialize the wishlist items
        serializer = WishlistItemSerializer(wishlist_items, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow access to anyone, including anonymous users
def get_anonymous_wishlist_items(request, anonymous_id):
    try:
        # Get the wishlist associated with the provided anonymous_id
        wishlist, created = Wishlist.objects.get_or_create(anonymous_id=anonymous_id)

        # Get all items in the wishlist
        wishlist_items = WishlistItem.objects.filter(wishlist=wishlist)
        
        # Serialize the wishlist items
        serializer = WishlistItemSerializer(wishlist_items, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def check_product_in_wishlist(request, product_id):
    user = request.user
    
    if user.is_authenticated:
        wishlist_items = WishlistItem.objects.filter(wishlist__user=user, product_id=product_id)
    else:
        anonymous_id = request.data.get('anonymous_id')
        wishlist_items = WishlistItem.objects.filter(wishlist__anonymous_id=anonymous_id, product_id=product_id)
    
    if wishlist_items.exists():
        return Response({"is_in_wishlist": True}, status=status.HTTP_200_OK)
    else:
        return Response({"is_in_wishlist": False}, status=status.HTTP_200_OK)
    

@api_view(['POST'])
@authentication_classes([JWTAuthentication])  
@permission_classes([IsAuthenticated])
def add_to_cart_authenticated(request):
    product_id = request.data.get('product_id')
    size = request.data.get('size')

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItems.objects.get_or_create(cart=cart, product_id=product_id, size=size)

    if not created:
        return Response({"message": "Product already exists in the cart."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Product added to cart."}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])  
def add_to_cart_anonymous(request):
    product_id = request.data.get('product_id')
    size = request.data.get('size')
    anonymous_id = request.data.get('anonymous_id')

    if not anonymous_id:
        cart = Cart.objects.create()
        anonymous_id = cart.anonymous_id
    else:
        cart, _ = Cart.objects.get_or_create(anonymous_id=anonymous_id)

    cart_item, created = CartItems.objects.get_or_create(cart=cart, product_id=product_id, size=size)

    if not created:
        return Response({"message": "Product already exists in the cart."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Product added to cart.", "anonymous_id": anonymous_id}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart_authenticated(request):
    try:
        product_id = request.data.get('product_id')
        size = request.data.get('size')
        product = Products.objects.get(id=product_id)
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItems.objects.get(cart=cart, product=product, size=size)
        cart_item.delete()

        return Response({"message": "Product removed from cart."}, status=status.HTTP_200_OK)
    except CartItems.DoesNotExist:
        return Response({"message": "Product not found in the cart."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])  
def remove_from_cart_anonymous(request):
    try:
        product_id = request.data.get('product_id')
        size = request.data.get('size')
        anonymous_id = request.data.get('anonymous_id')

        cart_item = CartItems.objects.get(cart__anonymous_id=anonymous_id, product_id=product_id, size=size)
        cart_item.delete()

        return Response({"message": "Product removed from cart."}, status=status.HTTP_200_OK)
    except CartItems.DoesNotExist:
        return Response({"message": "Product not found in the cart."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_cart_items(request):
    try:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItems.objects.filter(cart=cart)
        
        # Calculate total cart price
        total_price = cart.total

        # Serialize cart items
        serializer = CartItemSerializer(cart_items, many=True)
        
        # Prepare response data including cart items and total price
        response_data = {
            'cart_items': serializer.data,
            'total_price': total_price
        }
        
        return Response(response_data, status=status.HTTP_200_OK)  # Use Response object from DRF
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.forms.models import model_to_dict

@api_view(['GET'])
@permission_classes([AllowAny])  
def get_anonymous_cart_items(request, anonymous_id):
    try:
        cart, created = Cart.objects.get_or_create(anonymous_id=anonymous_id)

        cart_items = CartItems.objects.filter(cart=cart)
        
        serializer = CartItemSerializer(cart_items, many=True)
        total_price = cart.total

        response_data = {
            'cart_items': serializer.data,
            'total_price': total_price
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def check_product_in_cart(request, product_id):
    user = request.user
    
    if user.is_authenticated:
        cart_items = CartItems.objects.filter(cart__user=user, product_id=product_id)
    else:
        anonymous_id = request.data.get('anonymous_id')
        cart_items = CartItems.objects.filter(cart__anonymous_id=anonymous_id, product_id=product_id)
    
    if cart_items.exists():
        return Response({"is_in_cart": True}, status=status.HTTP_200_OK)
    else:
        return Response({"is_in_cart": False}, status=status.HTTP_200_OK)
    


from django.db import transaction

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    try:
        # Get data from request
        cart_items = request.data.get('cart_items', [])
        total_amount = request.data.get('total_amount', 0)
        user = request.user
        first_name = request.data.get('firstName', '')
        last_name = request.data.get('lastName', '')
        email = request.user.email
        phone = request.data.get('phone', '')
        street_address = request.data.get('street_address', '')
        city = request.data.get('city', '')
        state = request.data.get('state', '')
        postal_code = request.data.get('postal_code', '')

            # Initialize Razorpay client
        # client = razorpay.Client(auth=("rzp_live_pEyepar8NuQCjn", "JyGZY8CkTWfMGueG3FIkOVbX"))
        client = razorpay.Client(auth=("rzp_test_dhTo8WSf0CUEtv", "6dztzOsiD83UxGDDkjmcJCmP"))

        # Create payment order
        payment_data = {
            "amount": total_amount * 100,  # Amount in paisa
            "currency": "INR",
            "receipt": f"{email}",
        }
        payment_order = client.order.create(data=payment_data)
        # Create the order instance
        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                firstName=first_name,
                lastName=last_name,
                email=email,
                phone=phone,
                total_amount=total_amount,
                street_address=street_address,
                city=city,
                state=state,
                postal_code=postal_code,
                orderid = payment_order['id']
            )

            # Retrieve cart items
            user_cart = Cart.objects.get(user=user)
            cart_items = CartItems.objects.filter(cart=user_cart)


            # order.orderid = payment_order.id
            # order.save()

            # Save order items
            for item in cart_items:
                product = Products.objects.get(id=item.product.id)
                OrderItems.objects.create(
                    order=order,
                    orderItem=product,
                    size=item.size,
                    email=email
                )

        return Response({'order_id': order.id, 'payment_order': payment_order}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['POST'])
def checkStatus(request):
    try:
        orderId = request.data.get('orderId')
        order = Order.objects.get(orderid=orderId)
        if  order.status == 'Order Placed':
            return Response({'data':'Payment Successful'}, status=status.HTTP_200_OK)
        items = OrderItems.objects.filter(order=order)
        itemSerializer = OrderItemsSerializer(items, many=True)

        # Update order status and delete cart
        order.status = 'Order Placed'
        cart = Cart.objects.get(user=order.user)
        # Prepare email data
        order_data = itemSerializer.data

        def build_item_table(order_data):
            item_table = ""
            for item in order_data:
                item_table += "| {} | {} | {} |\n".format(item['size'], item['orderItem']['productName'], item['orderItem']['price'])
            return item_table

        # Send email to customer
        subject_customer = 'Order Placed Successfully'
        html_message_customer = render_to_string('ordersuccess.html', {'order': order})
        plain_message_customer = strip_tags(html_message_customer)
        send_mail(subject_customer, plain_message_customer, 'support@earthie.in', [order.email], html_message=html_message_customer)

        # Send email to team members
        subject_team = 'New Order - Order # {}'.format(order.id)
        body_team = "A new order has been placed!\n\nOrder Details:\n* Order ID: {}\n* Customer Email: {}\n \n*Address: {}\nItems:\n{}".format(
            order.id, order.email, order.street_address + ' ' + order.state + ' ' + order.city + ' ' + order.postal_code ,build_item_table(order_data)
        )
        send_mail(subject_team, body_team, 'support@earthie.in', ['orders@earthie.in'])
        cart.delete()
        return Response({'data':'Payment Successful'}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def verify_email(request, token):
    try:
        user = User.objects.get(token=token)
        if user.is_verified:
            return Response({'data':'Email already verified. Please login.'}, status=status.HTTP_200_OK)
        user.is_verified = True
        user.save()
        subject = 'Congratulations 🔥'
        html_message = render_to_string('activationDone.html', {'name': user.name})
        plain_message = strip_tags(html_message)
        from_email = 'support@earthie.in'  # Update with your email
        to_email = user.email
        try:
            send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
        except Exception as e:
            # Handle email sending failure
            print(f"Failed to send activation email: {e}")
            return Response({'data':'Email verification failed.'}, status=status.HTTP_200_OK)
        return Response({'data':'Email verified successfully. Please login.'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'data':'Email not found'}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST'])
def resetpassword(request):
    email = request.data.get('email', None)
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

    # Generate token for resetting password
    token = str(uuid.uuid4())
    user.token = token
    user.save()

    # Construct reset password URL with token
    reset_password_url = f"https://earthie.in/setpassword?token={token}"

    # Send email to user
    subject = 'Reset Your Password 🗝️'
    message = render_to_string('resetpasswordemail.html', {
        'reset_password_url': reset_password_url,
        'name': user.name
    })
    plain_message = strip_tags(message)
    send_mail(subject, plain_message, 'support@earthie.in', [user.email], html_message=message)

    return Response({'message': 'Reset password email has been sent successfully'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def setpassword(request):
    token = request.data.get('token', None)
    password = request.data.get('password', None)
    try:
        user = User.objects.get(token=token)
    except User.DoesNotExist:
        return Response({'error': 'User with this token does not exist'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Generate token for resetting password
        new_token = str(uuid.uuid4())
        user.set_password(password)
        user.token = new_token  # Update token if needed
        user.save()

        # Construct reset password URL with token

        # Send email to user
        subject = 'Password was successfully changed 🚀'
        message = render_to_string('passwordsucess.html', {
            'name': user.name
        })
        plain_message = strip_tags(message)
        send_mail(subject, plain_message, 'support@earthie.in', [user.email], html_message=message)

        return Response({'message': 'Password was successfully changed'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def fetchOrders(request):
    try:
        user = User.objects.get(email=request.user.email)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    
    orders = Order.objects.filter(user=user)
    order_serializer = OrderSerializer(orders, many=True)
    
    orders_data = []
    for order in orders:
        order_items = OrderItems.objects.filter(order=order)
        order_items_serializer = OrderItemsSerializer(order_items, many=True)
        order_data = {
            'order': order_serializer.data,
            'order_items': order_items_serializer.data
        }
        orders_data.append(order_data)
    
    
    return Response(orders_data)