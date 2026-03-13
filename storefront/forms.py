
from django import forms
from .models import Product, Store, Review

class StoreForm(forms.ModelForm):
    """
    Form for creating and editing stores
    """
    class Meta:
        """
        Store fields
        """
        model = Store
        fields = ["title", "blurb"]  # owner will be set in view, not exposed in form

class ProductsForm(forms.ModelForm):
    """
    Form for creating and editing stores
    """
    class Meta:
        """
        Form for creating and editing
        """
        model = Product
        fields = ["title", "content", "price", "inventory"]

class ReviewForm(forms.ModelForm):
    """
    Form for creating and editing reviews
    """
    class Meta:
        """
        Form for writing and editing
        """
        model = Review
        fields = ["title", "content", "rating"]