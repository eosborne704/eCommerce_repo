from django.test import TestCase
from django.urls import reverse
from .models import Store

class StoreModelTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(title="Test Store", blurb="A test store blurb.")

    def test_store_has_title(self):
        self.assertEqual(self.store.title, "Test Store")

    def test_store_has_blurb(self):
        self.assertEqual(self.store.blurb, "A test store blurb.")

    def test_store_str(self):
        self.assertEqual(str(self.store), "Test Store")

class StoreViewTests(TestCase):
    """
    Tests the viewing of stores
    both all and singular stores
    """
    def setUp(self):
        self.store = Store.objects.create(title="Test Store", blurb="A test store blurb.")

    def test_view_all_stores(self):
        response = self.client.get(reverse('all_stores'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.store.title)

    def test_view_single_store(self):
        response = self.client.get(reverse('view_store', args=[self.store.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.store.title)
        self.assertContains(response, self.store.blurb)
