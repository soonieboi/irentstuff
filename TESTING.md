# **Introduction to Testing in Django**
Tests in Django run on the standard `unittest` Python module and are defined using a class-based approach. This helps to provide isolation for each test case from other test cases. The name of test files should begin with `test` and test classes should inherit from `django.test.TestCase` (which is a subclass of `unittest.TestCase`). A test is written as an assertion of the result from the method compared with a given value, e.g. `assertEquals(1+1, 2)`

Official documentation from Django is available here: https://docs.djangoproject.com/en/5.0/topics/testing/overview/

Tests are executed by calling:
- `manage.py test` - searches for any file that matches the above descriptions
- `manage.py test models` - executes all tests in a specific test file
- `manage.py test models.Category` - executes a specific test class in a specific test file
- `manage.py test models.Category.test_category_creation` - executes a specific test method in a specific test class in a specific test file

# **Creating a test**
1. Create a test script that starts with `test`
2. Write a test case that inherits from `django.test.TestCase`.
3. Set up the required objects. This is done as the first method in the class, defined as setUp(self). E.g. to set up a test for the Category model:
```
class CategoryModelTestCase(TestCase):
  def setUp(self):
    self.category = Category.objects.create(name="testcategory")
```
4. Write a test method under the test class which either retrieves an object created from the setUp method or instantiates an object to be tested. E.g.
```
  def test_category_creation():
    category = self.category
```
5. Write assertions for the tests, e.g.:
```
self.assertEquals(category.name, "testcategory")
self.assertEquals(str(category), "testcategory")
```
6. Tear down any persistent files or env variables that were set up, e.g.:
```
    def tearDown(self) -> None:
        # Insert tear down code here
        return super().tearDown()
```

# **How iRentStuff is tested**
As iRentStuff is written with a thin-model fat-view approach, tests are treated as such:
- **models** and **urls** work as unit tests, which test the simplest units
- **forms** work as integration tests, which test the result of different units working together
- **views** work as functional tests, which test business logic
Because of this, an understanding of how the modules are intertwined together is necessary in order to understand how tests for forms and views are written.

As an example, testing for the `add_item()` view calls the `ItemForm` class from `forms.py` and the `add_item` URL from `urls.py`. In turn, `ItemForm` calls the `Item` model, which has a dependency on the Category class, i.e. every Item requires a Category.

# Dependencies
## **Models**
- Category - No dependencies
- Item - Depends on Category. Also requires an image when created via the add_item() view.
- Message - Depends on Item
- Rental - Depends on Item
- Review - Depends on Rental

## **Modules**
User interaction --> urls --> views --> forms --> models

# Debugging
Because of how modules and models intertwine, debugging can be more complicated. Here are some helpful methods to facilitate debugging:

## views
Views are instantiated using the `self.client.post()` method. As views often have redirects, it is useful to print the methods of the results of these calls.

E.g. include `follow=True` and print `response.redirect_chain`:
```
response = self.client.post(
            reverse("edit_item", kwargs={"item_id": self.item.id}),
            form_data,
            follow=True,
        )
print(response.redirect_chain)
```

Other helpful methods include the following:
- `response.client`
- `response.status_code`
- `response.request`
- `response.resolver_match`

Note that these methods contain other methods that can provide more details

## forms
Forms are often also instantiated when testing views. This is done to validate that the form data passed into the view is valid. As such, assuming that a form is instantiated as `form = ItemForm(data=form_data, self.create_iamge())`, some helpful methods for debugging include:
- `form.is_valid()`
- `form.errors`
