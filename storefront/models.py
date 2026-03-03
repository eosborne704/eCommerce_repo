from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
# Create your models here.

class Store(models.Model):
    """
    How each store should act
    """
    title = models.CharField(max_length=200)
    blurb = models.TextField()

    def __str__(self):
        return str(self.title)

class Product(models.Model):
    """
    This is how each product should act
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    inventory = models.IntegerField()
    store = models.ForeignKey(
        "Store", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return str(self.title)

class Review(models.Model):
    """
    This is how each review should act
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1),
        MaxValueValidator(5)],
        help_text="Rate this product out of 5"
    )
    date_written = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, null=True, blank=True
    )
    verified = models.BooleanField(default=False, help_text="Is this review from a verified buyer?")

    def __str__(self):
        return str(self.title)


class User(models.Model):
    """
    Defining User's behavior
    """
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ResetToken(models.Model):
    """
    Password Reset Logic
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=500)
    expiry_date = models.DateTimeField()
    used = models.BooleanField(default=False)

