from locust import HttpUser, task, between
import json

class ChatUser(HttpUser):
    wait_time = between(1, 3)
    
    # Simulate Auth Token
    def on_start(self):
        self.token = "Bearer mock_jwt_token_for_load_test"
        self.headers = {"Authorization": self.token}

    @task
    def chat_interaction(self):
        # We test the HTTP endpoints or use a custom WS client
        # Here testing a hypothetical history endpoint to stress DB
        self.client.get("/health", headers=self.headers)
        
        # Note: Locust needs a plugin for proper WebSocket testing
        # Or we verify the Auth/RateLimit via HTTP endpoints