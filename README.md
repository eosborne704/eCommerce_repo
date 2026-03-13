# eCommerce_repo
This ecommerce app allows users to register as either buyers or vendors. Vendors have the ability to create, edit and delete stores
as well as add, delete or edit products within them. Stores are made up of a title and blurb and products are made up of a title, description, price and inventory. Users who register as buyers have the option to canvas different stores
and add products across those stores to their cart for checkout. Buyers may leave reviews of the products they checked out, upon which they will be considered verified, having bought the product already. Should a buyer want to leave a review, but not have already bought the product, they will be able to leave a review, though they will be designated as unverified status and their rating will not count to the
average rating of said product. Both verified and unverified buyers will be able to edit or delete their own reviews. Password resetting via email is available 

python3 -m venv myvenv
source myvenv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional, for admin access
python manage.py runserver
python manage.py test
