import threading
from google.cloud import pubsub_v1, storage
import json

storage_client = storage.Client()

class PubSubManager:
    def __init__(self, project_id: str, subscription_map: dict):
        self.project_id = project_id
        self.subscription_map = subscription_map
        self.subscribers = []

    def start_listeners(self):
        """Start all listeners in separate threads."""
        for sub_name, func in self.subscription_map.items():
            thread = threading.Thread(target=self.listen_to_subscription, args=(sub_name, func), daemon=True)
            thread.start()
            self.subscribers.append(thread)
            print(f"Started listener thread for {sub_name}")

    def listen_to_subscription(self, subscription_name: str, processing_func):
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(self.project_id, subscription_name)

        def callback(message):
            try:
                payload = json.loads(message.data)
                bucket_name = payload["bucket"]
                object_name = payload["name"]
                print(f"Received message for {object_name} in bucket {bucket_name}")
                processing_func(bucket_name, object_name)
                message.ack()
            except Exception as e:
                print(f"Error processing message: {e}")
                message.nack()

        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
        print(f"Listening to subscription: {subscription_name}")
        try:
            streaming_pull_future.result()  # Block thread until cancelled
        except Exception as e:
            print(f"Subscriber error: {e}")
            streaming_pull_future.cancel()
