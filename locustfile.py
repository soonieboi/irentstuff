from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        # Fetch the login page to get the CSRF token
        response = self.client.get("login/")
        self.csrf_token = response.cookies.get('csrftoken', '')
        self.headers = {
            'X-CSRFToken': self.csrf_token,
            'Referer': self.client.base_url + "login/"
        }
        # print(f"Initial GET /login/ - CSRF Token fetched: {self.csrf_token}")

    @task
    def access_homepage(self):
        response = self.client.get("/")
        # if response.status_code != 200:
            # print(f"Homepage access failed: Status {response.status_code}, Body {response.text}")

    @task(3)
    def browse_items_by_category(self):
        categories = ['Home', 'Electronics', 'Sports']
        for category in categories:
            response = self.client.get(f"/stuff/?search=&category={category}")
            # if response.status_code != 200:
                # print(f"Browse by category {category} failed: Status {response.status_code}, Body {response.text}")

    @task(2)
    def search_items(self):
        search_terms = ['jacket', 'switch']
        for term in search_terms:
            response = self.client.get(f"/stuff/?search={term}")
            # if response.status_code != 200:
            #     print(f"Search for {term} failed: Status {response.status_code}, Body {response.text}")

    @task
    def register_user(self):
        headers = {'X-CSRFToken': self.csrf_token}
        response = self.client.post("register/", {
            'email': 'example@example.com',
            'password': 'password123',
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'user_example'
        }, headers=headers)
        # if response.status_code != 200:
        #     print(f"Registration failed: Status {response.status_code}, Body {response.text}")

    
    # @task
    # def login(self):
    #     response = self.client.post("login/", {
    #         'username': 'user1',
    #         'password': 'mtech@111'
    #     }, headers=self.headers)
        # if response.status_code != 200:
            # print(f"Login failed: Status {response.status_code}, Body {response.text}")


    # @task
    # def simulate_rental_process(self):
    #     item_id = "1"
    #     headers = {'X-CSRFToken': self.csrf_token}
    #     response = self.client.post(f"stuff/{item_id}/add_rental/", json={
    #         "start_date": "2024-05-10",
    #         "end_date": "2024-05-20",
    #         "renterid": "user2",
    #         "apply_loyalty_discount": True
    #     }, headers=headers)
    #     # if response.status_code != 200:
    #     #     print(f"Rental process for item {item_id} failed: Status {response.status_code}, Body {response.text}")
