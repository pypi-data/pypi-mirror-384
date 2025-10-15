#!/usr/bin/env python3
"""
Asynchronous example of using the Replicated Python SDK.
"""

import asyncio

from replicated import AsyncReplicatedClient


async def main():
    # Initialize the async client with your publishable key and app slug
    async with AsyncReplicatedClient(
        publishable_key="replicated_pk_...",  # Replace with your actual key
        app_slug="my-app",  # Replace with your app slug
    ) as client:
        # Create a customer (or fetch an existing one)
        email = "user@example.com"
        customer = await client.customer.get_or_create(email_address=email)
        print(f"Customer ID: {customer.customer_id}")

        # Get or create the associated instance
        instance = await customer.get_or_create_instance()
        print(f"Instance ID: {instance.instance_id}")

        # Send some metrics concurrently
        await asyncio.gather(
            instance.send_metric("cpu_usage", 0.83),
            instance.send_metric("memory_usage", 0.67),
            instance.send_metric("disk_usage", 0.45),
        )
        print("Metrics sent successfully")

        print("Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
