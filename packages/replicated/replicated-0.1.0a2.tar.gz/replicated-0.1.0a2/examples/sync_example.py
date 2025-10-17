#!/usr/bin/env python3
"""
Synchronous example of using the Replicated Python SDK.
"""

from replicated import ReplicatedClient


def main():
    # Initialize the client with your publishable key and app slug
    with ReplicatedClient(
        publishable_key="replicated_pk_...",  # Replace with your actual key
        app_slug="my-app",  # Replace with your app slug
    ) as client:
        # Create a customer (or fetch an existing one)
        email = "user@example.com"
        customer = client.customer.get_or_create(email_address=email)
        print(f"Customer ID: {customer.customer_id}")

        # Get or create the associated instance
        instance = customer.get_or_create_instance()
        print(f"Instance ID: {instance.instance_id}")

        # Send some metrics
        instance.send_metric("cpu_usage", 0.83)
        instance.send_metric("memory_usage", 0.67)
        instance.send_metric("disk_usage", 0.45)
        print("Metrics sent successfully")

        print("Example completed successfully!")


if __name__ == "__main__":
    main()
