
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Purchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    date_purchased = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField(default=1)
    def __str__(self):
        return f"{self.user} bought {self.product}"
# Create your models here.

class Store(models.Model):
    """
    How each store should act
    """
    title = models.CharField(max_length=200)
    blurb = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stores', help_text='Vendor who owns this store', null=True, blank=True)

    def __str__(self):
        return self.title

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False, help_text="Is this review from a verified buyer?")

    def __str__(self):
        return str(self.title)





class ResetToken(models.Model):
    """
    Password Reset Logic
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=500)
    expiry_date = models.DateTimeField()
    used = models.BooleanField(default=False)

