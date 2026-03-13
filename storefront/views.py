
import secrets
from datetime import timedelta
from hashlib import sha1
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMessage
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ProductsForm, ReviewForm, StoreForm
from .models import Product, Purchase, ResetToken, Review, Store



def reset_password_view(request, token) -> HttpResponse:
    """
    Handles password reset form and token validation.
    """
    try:
        reset_token = ResetToken.objects.get(token=token)
        if reset_token.expiry_date < timezone.now():
            return HttpResponse("Token expired.")
        if request.method == "POST":
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")
            if new_password != confirm_password:
                return render(request, "storefront/reset_password.html", {"error": "Passwords do not match."})
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            reset_token.delete()
            return render(request, "storefront/reset_password.html", {"success": True})
        return render(request, "storefront/reset_password.html")
    except ResetToken.DoesNotExist:
        return HttpResponse("Invalid or expired token.")


def forgot_password_view(request) -> HttpResponse:
    """
    Handles forgot password form and confirmation message.
    """
    confirmation = None
    error = None
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            error = "No user found with that email."
            return render(request, "storefront/forgot_password.html", {"confirmation": confirmation, "error": error})

        # Generate secure token
        token = sha1((secrets.token_urlsafe(32) + str(user.pk)).encode()).hexdigest()
        expiry_date = timezone.now() + timedelta(hours=1)
        ResetToken.objects.create(user=user, token=token, expiry_date=expiry_date)

        # Build reset URL
        reset_url = request.build_absolute_uri(reverse("reset_password", kwargs={"token": token}))
        subject = "Password Reset Request"
        body = f"Hello {user.username},\n\nTo reset your password, click the link below.\n{reset_url}\n\nThis link will expire in 1 hour. If you did not request a password reset, please ignore this email."
        email_message = EmailMessage(subject, body, to=[email])
        email_message.send()
        confirmation = "Reset email sent. Please check your inbox."
    return render(request, "storefront/forgot_password.html", {"confirmation": confirmation, "error": error})


@login_required
def edit_product_details(request, pk) -> HttpResponse | HttpResponseRedirect:
    product: Product = get_object_or_404(Product, pk=pk)
    store: None = product.store
    # Only allow the owner (vendor) to edit products in their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        form = ProductsForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("view_store", pk=product.store.pk)
    else:
        form = ProductsForm(instance=product)
    return render(request, "storefront/edit_product_details.html", {"form": form, "product": product})


@login_required
def delete_product(request, pk) -> HttpResponse | HttpResponseRedirect:
    product: Product = get_object_or_404(Product, pk=pk)
    store: None = product.store
    # Only allow the owner (vendor) to delete products in their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        store_pk = product.store.pk
        product.delete()
        return redirect("view_store", pk=store_pk)
    return render(request, "storefront/delete_product.html", {"product": product})


@login_required
def delete_store(request, pk) -> HttpResponse | HttpResponseRedirect:
    store: Store = get_object_or_404(Store, pk=pk)
    # Only allow the owner (vendor) to delete their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        store.delete()
        return redirect("all_stores")
    return render(request, "storefront/delete_store.html", {"store": store})



def logout_view(request) -> HttpResponseRedirect:
    logout(request)
    return redirect('login')


def login_view(request) -> HttpResponseRedirect | HttpResponse:
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user: User = form.get_user()
            login(request, user)
            # Redirect all users to stores page immediately
            return redirect('all_stores')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def verify_username(username) -> bool:
    """
    Checks if username exists in database.
    """
    return not User.objects.filter(username=username).exists()


def verify_password(password) -> bool:
    """
    Checks if password is at least 8.
    """
    return len(password) >= 8



def register_user(request) -> HttpResponse | HttpResponseRedirect:
    """
    Allows users to register themselves
    as either a Vendor or Buyer.
    """
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pword = request.POST.get('password')
        confirm_pword = request.POST.get('confirm_password')
        role = request.POST.get('role')
        valid_roles: list[str] = ['Vendor', 'Buyer']
        errors = []
        if role not in valid_roles:
            errors.append('Invalid role selected.')
        if User.objects.filter(username=uname).exists():
            errors.append('Username already taken. Please choose another.')
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered. Please use a different email.')
        if pword != confirm_pword:
            errors.append('Passwords do not match. Please make sure you have entered the right password both times.')
        if errors:
            return render(request, 'register.html', {
                'errors': errors,
                'username': uname,
                'email': email,
                'role': role
            })
        # Always ensure both groups exist
        vendor_group, _ = Group.objects.get_or_create(name='Vendor')
        buyer_group, _ = Group.objects.get_or_create(name='Buyer')
        user: User = User.objects.create_user(username=uname, password=pword, email=email)
        if role == 'Vendor':
            user.groups.add(vendor_group)
        elif role == 'Buyer':
            user.groups.add(buyer_group)
        user.save()
        # Confirm correct group assignment
        if not user.groups.filter(name=role).exists():
            return render(request, 'register.html', {
                'error': f'{role} registration failed.',
                'username': uname,
                'role': role
            })
        login(request, user)
        if role == 'Buyer':
            return redirect('all_stores')
        else:
            return redirect('home')
    return render(request, 'register.html')


def change_user_password(username, new_password) -> None:
    # Retrieve a specific user by their username
    user: User = User.objects.get(username=username)

    # Use the set_password() method to change their password
    user.set_password(new_password)

    # Save the changes to the database
    user.save()


@login_required
def welcome_view(request) -> HttpResponse:
    """
    Renders the welcome page
    """
    stores: models.BaseManager[Store] = Store.objects.all()
    return render(request, 'welcome.html', {"stores": stores})


def all_stores(request) -> HttpResponse:
    """
    Displays all presently-created stores
    """
    is_vendor = False
    stores: models.BaseManager[Store] = Store.objects.all()
    if request.user.is_authenticated:
        is_vendor = request.user.groups.filter(name='Vendor').exists()
        if is_vendor:
            stores: models.BaseManager[Store] = Store.objects.filter(owner=request.user)
    context = {
        "stores": stores,
        "store_display": "All Stores",
        "is_vendor": is_vendor,
    }
    return render(request, "storefront/all_stores.html", context)


def view_product_page(request) -> HttpResponse | None:
    """
    Show product page if user permitted.
    """
    user = request.user
    if user.has_perm('eCommerce.view_product'):
        product_name = request.POST['product']
        product: Product = Product.objects.get(name=product_name)
        return render(request, 'product_page.html', {'product': product})


def change_product_price(request) -> HttpResponseRedirect | None:
    """
    Change product price if permitted.
    """
    user = request.user
    if user.has_perm('eCommerce.change_product'):
        product = request.POST.get('product')
        new_price = request.POST.get('new_price')
        Product.objects.filter(name=product).update(price=new_price)
        return HttpResponseRedirect(reverse('eCommerce:products'))


@login_required
def create_store(request) -> HttpResponseRedirect | HttpResponse:
    """
    Allows vendor to create a new store
    """
    if request.method == "POST":
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            # Check for duplicate store name
            if Store.objects.filter(title=store.title).exists():
                return render(request, "storefront/create_store.html", {"form": form, "error": "A store with this name already exists."})
            store.owner = request.user
            store.save()
            return redirect("all_stores")
    else:
        form = StoreForm()
    return render(request, "storefront/create_store.html", {"form": form})


def view_store(request, pk) -> HttpResponse:
    """
    Allows vendor or buyer to view a
    specific store
    """
    store: Store = get_object_or_404(Store, pk=pk)
    is_vendor = False
    if request.user.is_authenticated:
        is_vendor = request.user.groups.filter(name='Vendor').exists()
    return render(request, "storefront/view_store.html", {"store": store, "is_vendor": is_vendor})


@login_required
def edit_store_details(request, pk) -> HttpResponse | HttpResponseRedirect:
    """
    View to edit store details
    """
    store: Store = get_object_or_404(Store, pk=pk)
    # Only allow the owner (vendor) to edit their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            return redirect("view_store", pk=store.pk)
    else:
        form = StoreForm(instance=store)
    return render(request, "storefront/create_store.html", {"form": form})



def all_products(request, store_id) -> HttpResponse:
    """
    Show all products for a store.
    """
    store: Store = get_object_or_404(Store, pk=store_id)
    products: models.BaseManager[Product] = Product.objects.filter(store=store)

    context = {
        "products": products,
        "store": store,
    }

    return render(request, "storefront/all_products.html", context)


@login_required
def add_product(request, store_id) -> HttpResponse | HttpResponseRedirect:
    """
    View to add a new product
    """
    store: Store = get_object_or_404(Store, pk=store_id)
    # Only allow the owner (vendor) to add products to their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        form = ProductsForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            if not store:
                return render(request, "storefront/add_product.html", {"form": form, "store": store, "error": "Store not found. Cannot save product."})
            # Check for duplicate product name in this store
            if Product.objects.filter(store=store, title=product.title).exists():
                return render(request, "storefront/add_product.html", {"form": form, "store": store, "error": "A product with this name already exists in this store."})
            product.store = store
            product.save()
            if not product.store:
                return render(request, "storefront/add_product.html", {"form": form, "store": store, "error": "Product not linked to a store. Cannot save."})
            return redirect("view_store", pk=store.pk)
    else:
        form = ProductsForm()
    return render(request, "storefront/add_product.html", {"form": form, "store": store})


def get_rating_phrase_and_color(rating):
    if rating >= 4.5:
        return "Overwhelmingly positive!", "#50C878"  # emerald green
    elif rating >= 4.0:
        return "Very Positive!", "#66FF66"  # slightly brighter green
    elif rating >= 3.5:
        return "Fairly Positive!", "#99FF00"  # lime green
    elif rating >= 3.0:
        return "Decent", "#FFFF00"  # yellow
    elif rating >= 2.5:
        return "Fairly Negative", "#FFD700"  # orange-yellow
    elif rating >= 2.0:
        return "Very Negative", "#FF4500"  # orange-red
    elif rating >= 1.0:
        return "Overwhelmingly negative", "#B22222"  # slightly darker red
    elif rating > 0:
        return "Unusable", "#000000"  # black
    else:
        return "No ratings yet", "#888888"

def view_product(request, pk) -> HttpResponse:
    """
    Show details for a product.
    """
    product: Product = get_object_or_404(Product, pk=pk)
    store: None = product.store
    reviews: models.BaseManager[Review] = Review.objects.filter(product=product)
    verified_reviews = reviews.filter(verified=True)
    avg_rating: Any | int = verified_reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    phrase, color = get_rating_phrase_and_color(avg_rating)
    # Annotate each review with phrase and color
    annotated_reviews = []
    for review in reviews:
        r_phrase, r_color = get_rating_phrase_and_color(review.rating)
        annotated_reviews.append({
            'review': review,
            'phrase': r_phrase,
            'color': r_color,
        })
    is_buyer = False
    if request.user.is_authenticated:
        is_buyer = request.user.groups.filter(name='Buyer').exists()
    return render(request, "storefront/view_product.html", {
        "product": product,
        "store": store,
        "reviews": annotated_reviews,
        "avg_rating": avg_rating,
        "avg_phrase": phrase,
        "avg_color": color,
        "is_buyer": is_buyer,
    })


@login_required


@login_required
def delete_product(request, pk) -> HttpResponseRedirect:
    """
    View to delete a product
    """
    product: Product = get_object_or_404(Product, pk=pk)
    store_pk = product.store.pk
    product.delete()
    return redirect("view_store", pk=store_pk)


def all_reviews(request, product_id) -> HttpResponse:
    """
    Allows user to view all reviews for a product
    """
    product: Product = get_object_or_404(Product, pk=product_id)
    reviews: models.BaseManager[Review] = Review.objects.filter(product=product)
    context = {
        "reviews": reviews,
        "product": product,
        "page_title": f"Reviews for {product.title}",
    }
    return render(request, "storefront/all_reviews.html", context)


def view_review(request, pk) -> HttpResponse:
    """
    Allows user to view a specific review
    """
    review: Review = get_object_or_404(Review, pk=pk)
    return render(request, "storefront/view_review.html", {"review": review})


@login_required
def write_review(request, product_id) -> HttpResponseRedirect | HttpResponse:
    """
    Allows buyers to write a review
    Tags them as verified if they've bought the product
    """
    product: Product = get_object_or_404(Product, pk=product_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            user_has_bought: bool = Purchase.objects.filter(user=request.user, product=product).exists()
            review.verified = user_has_bought
            review.save()
            return redirect("view_product", pk=product.pk)
    else:
        form = ReviewForm()
    return render(request, "storefront/write_review.html", {"form": form, "product": product})


@login_required
def edit_review(request, pk) -> HttpResponseRedirect | HttpResponse:
    """
    Allows buyers to edit the content of their review
    """
    review: Review = get_object_or_404(Review, pk=pk)
    product: None = review.product
    # Restrict editing to the review's author
    if review.user != request.user:
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect("view_product", pk=product.pk)
    else:
        form = ReviewForm(instance=review)
    return render(request, "storefront/edit_review.html", {"form": form, "product": product})


@login_required
def delete_review(request, pk) -> HttpResponseRedirect | HttpResponse:
    """
    Allows buyers to delete their reviews
    """
    review: Review = get_object_or_404(Review, pk=pk)
    product: None = review.product
    # Restrict deleting to the review's author
    if review.user != request.user:
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        review.delete()
        return redirect("view_product", pk=product.pk)
    return render(request, "storefront/delete_review.html", {"review": review, "product": product})


@require_POST
@login_required
def add_item_to_cart(request) -> HttpResponse | HttpResponseRedirect:
    """
    Add an item to user cart.
    """
    # Only allow buyers to add to cart
    if not request.user.groups.filter(name='Buyer').exists():
        return HttpResponse("Only buyers can add items to cart.")
    session = request.session
    item_name = request.POST.get('item') # The product name from your form
    quantity = int(request.POST.get('quantity', 1))

    # Find the product in the database
    try:
        product: Product = Product.objects.get(title=item_name)
    except Product.DoesNotExist:
        return render(request, "product_not_found.html", status=404)

    # Check if enough inventory is available
    if product.inventory < quantity:
        return HttpResponse("Not enough inventory in stock.")

    # Subtract purchased quantity from inventory
    product.inventory -= quantity
    product.save()

    # Update cart in session
    if 'cart' in session:
        session['cart'][item_name] = quantity
    else:
        session['cart'] = {item_name: quantity}
    session.modified = True
    return redirect('show_user_cart')

@require_POST
@login_required
def empty_cart(request) -> HttpResponse | HttpResponseRedirect:
    """
    Remove all items from the user's cart.
    """
    # Only allow buyers to empty cart
    if not request.user.groups.filter(name='Buyer').exists():
        return HttpResponse("Only buyers can empty cart.")
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
    return redirect('show_user_cart')

@login_required
def show_user_cart(request) -> HttpResponse:
    """
    Display the current user's shopping cart.
    """
    # Only allow buyers to view cart
    if not request.user.groups.filter(name='Buyer').exists():
        return HttpResponse("Only buyers can view cart.")
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for item, quantity in cart.items():
        try:
            product: Product = Product.objects.get(title=item)
            cart_items.append({'product': product, 'quantity': quantity})
            total += product.price * quantity
        except Product.DoesNotExist:
            continue
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})


@login_required
def checkout_view(request) -> HttpResponse:
    """
    Checks out cart items
    """
    cart = request.session.get('cart', {})
    user = request.user
    for item, quantity in cart.items():
        try:
            product: Product = Product.objects.get(title=item)
            Purchase.objects.create(user=user, product=product, quantity=quantity)
        except Product.DoesNotExist:
            continue
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
    # Email cart/order details to user
    if user.email:
        order_details = "Your order details:\n"
        for item, quantity in cart.items():
            order_details += f"- {item}: {quantity}\n"
        email = EmailMessage(
            subject="Your Cart Checkout",
            body=order_details,
            to=[user.email]
        )
        email.send()
    return render(request, 'storefront/checkout_complete.html')


def build_email(user, reset_url) -> EmailMessage:
    """
    Builds reset email
    """
    subject = "Password Reset"
    user_email = user.email
    domain_email = "example@domain.com"
    body: str = f"Hi {user.username},\nHere is your link to reset your password: {reset_url}"
    email = EmailMessage(subject, body, domain_email, [user_email])
    return email


