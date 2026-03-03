from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils import timezone
from .models import Product, Store, Review, ResetToken
from .forms import ProductsForm, StoreForm, ReviewForm
import secrets


Vendors, created = Group.objects.get_or_create(name='Vendors')

def verify_username(username):
    from django.contrib.auth.models import User
    return not User.objects.filter(username=username).exists()


def verify_password(password):
    return len(password) >= 8


def register_user(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        pword = request.POST.get('password')
        # This matches the 'name' attribute in your HTML <select> or <input>
        role = request.POST.get('role')

        user = User.objects.create_user(username=uname, password=pword)

        group = Group.objects.get(name=role)
        user.groups.add(group)

        user.save()
        login(request, user)
        return redirect('home') # Or wherever your home page is

    return render(request, 'register.html')


def change_user_password(username, new_password):
    # Retrieve a specific user by their username
    user = User.objects.get(username=username)

    # Use the set_password() method to change their password
    user.set_password(new_password)

    # Save the changes to the database
    user.save()


@login_required(login_url='/grabsomore/alter_login/')
def welcome_view(request):
    """
    Renders the welcome page
    """
    return render(request, 'welcome.html')


def welcome(request):
    return render(request, 'welcome.html')


def all_stores(request):
    """
    Displays all presently-created stores
    """

    stores = Store.objects.all()
    context = {
        "stores": stores,
        "store_display": "All Stores",
    }
    return render(request, "storefront/all_stores.html", context)

def view_product_page(request):
    user = request.user

    # Check if the user has the 'view_product' permission for the eCommerce app
    if user.has_perm('eCommerce.view_product'):
        product_name = request.POST['product']
        product = Product.objects.get(name=product_name)

        # If they have permission, render the product page with the product data
        return render(request, 'product_page.html', {'product': product})


def change_product_price(request):
    user = request.user

    # Check if the user has permission to change products in the eCommerce app
    if user.has_perm('eCommerce.change_product'):
        product = request.POST.get('product')
        new_price = request.POST.get('new_price')

        # Call a function to update the price (e.g., set_new_price)
        Product.objects.filter(name=product).update(price=new_price)

        # Redirect the user back to the product list after a successful change
        return HttpResponseRedirect(reverse('eCommerce:products'))


@login_required
def create_store(request):
    """
    Allows vendor to create a new store
    """
    if request.method == "POST":
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            form.save()
            return redirect("all_stores")
    else:
        form = StoreForm()
    return render(request, "storefront/create_store.html", {"form": form})


def view_store(request, pk):
    """
    Allows vendor or buyer to view a
    specific store
    """
    store = get_object_or_404(Store, pk=pk)
    return render(request, "storefront/view_store.html", {"store": store})


@login_required
def edit_store_details(request, pk):
    """
    View to edit a note
    """
    store = get_object_or_404(Store, pk=pk)
    if request.method == "POST":
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            store = form.save(commit=False)
            store.save()
            return redirect("all_stores")

    else:
        form = StoreForm(instance=store)
    return render(request, "storefront/create_store.html", {"form": form})


@login_required
def delete_store(request, pk):
    """
    View to delete a product
    """
    store = get_object_or_404(Store, pk=pk)
    store.delete()


def all_products(request, store_id):
    """
    Docstring for view_notes

    :param request: Description
    """
    store = get_object_or_404(Store, pk=store_id)
    products = Product.objects.filter(store=store)

    context = {
        "products": products,
        "store": store,
    }

    return render(request, "storefront/all_products.html", context)


@login_required
def add_product(request, store_id):
    """
    View to write a new sticky note
    """
    store = get_object_or_404(Store, pk=store_id)
    if request.method == "POST":
        form = ProductsForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            if not store:
                return render(request, "storefront/add_product.html", {"form": form, "store": store, "error": "Store not found. Cannot save product."})
            product.store = store
            product.save()
            if not product.store:
                return render(request, "storefront/add_product.html", {"form": form, "store": store, "error": "Product not linked to a store. Cannot save."})
            return redirect("view_product", pk=product.pk)
    else:
        form = ProductsForm()
    return render(request, "storefront/add_product.html", {"form": form, "store": store})


def view_product(request, pk):
    """
    Docstring for view_notes

    :param request: Description
    :param pk: Description
    """
    product = get_object_or_404(Product, pk=pk)
    store = product.store
    return render(request, "storefront/view_product.html", {"product": product, "store": store})


@login_required
def edit_product_details(request, pk):
    """
    View to edit a note
    """
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductsForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
            return redirect("view_product", pk=product.pk)

    else:
        form = ProductsForm(instance=product)
    return render(request, "storefront/add_product.html", {"form": form})


@login_required
def delete_product(request, pk):
    """
    View to delete a product
    """
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect("all_products", store_id=product.store.pk)


def all_reviews(request, product_id):
    """
    Allows user to view all reviews for a product
    """
    product = get_object_or_404(Product, pk=product_id)
    reviews = Review.objects.filter(product=product)
    context = {
        "reviews": reviews,
        "product": product,
        "page_title": f"Reviews for {product.title}",
    }
    return render(request, "storefront/all_reviews.html", context)


def view_review(request, pk):
    """
    Allows user to view a specific review
    """
    review = get_object_or_404(Review, pk=pk)
    return render(request, "storefront/view_review.html", {"review": review})


@login_required
def write_review(request, product_id):
    """
    Allows buyers to write a review
    Tags them as verified if they've bought the product
    """
    product = get_object_or_404(Product, pk=product_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            # Check if user has bought the product
            cart = request.session.get('cart', {})
            user_has_bought = str(product.title) in cart
            review.verified = user_has_bought
            review.save()
            return redirect("all_reviews", product_id=product.pk)
    else:
        form = ReviewForm()
    return render(request, "storefront/write_review.html", {"form": form, "product": product})


@login_required
def edit_review(request, pk):
    """
    Allows buyers to edit the content of their review
    """
    review = get_object_or_404(Review, pk=pk)
    product = review.product
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.save()
            return redirect("all_reviews", product_id=product.pk)
    else:
        form = ReviewForm(instance=review)
    return render(request, "storefront/edit_review.html", {"form": form, "product": product})


@login_required
def delete_review(request, pk):
    """
    Allows buyers to delete their reviews
    """
    review = get_object_or_404(Review, pk=pk)
    product = review.product
    if request.method == "POST":
        review.delete()
        return redirect("all_reviews", product_id=product.pk)
    return render(request, "storefront/delete_review.html", {"review": review, "product": product})


def send_password_reset(request):
    """
    password reset logic
    """
    user_email = request.POST.get('email')
    try:
        user = User.objects.get(email=user_email)
        # Create a secure random token
        token_value = secrets.token_urlsafe(32)

        # Save token to database (expires in 1 hour)
        ResetToken.objects.create(
            user=user,
            token=token_value,
            expiry_date=timezone.now() + timezone.timedelta(hours=1)
        )

        # Build and send email
        reset_url = f"http://127.0.0.1:8000/reset-password/{token_value}/"
        email = EmailMessage(
            "Password Reset",
            f"Hello {user.username}, click here to reset: {reset_url}",
            "noreply@yourstore.com",
            [user_email]
        )
        email.send()
        return HttpResponse("Check your console for the reset link!")
    except User.DoesNotExist:
        return HttpResponse("Email not found.")


@login_required
def add_item_to_cart(request):
    session = request.session
    item_name = request.POST.get('item') # The product name from your form
    quantity = int(request.POST.get('quantity', 1))

    # Find the product in the database
    try:
        product = Product.objects.get(title=item_name)
    except Product.DoesNotExist:
        return HttpResponse("Product not found.")

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


@login_required
def show_user_cart(request):
    cart = request.session.get('cart', {})
    return render(request, 'main_cart.html', {'cart': cart})