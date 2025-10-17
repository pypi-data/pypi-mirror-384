#!/usr/bin/env python3
"""
Basic example of using the Replicated Python SDK.
This script initializes the replicated package, creates a customer and instance.
"""

import argparse

from replicated import ReplicatedClient


def main():
    parser = argparse.ArgumentParser(description="Basic Replicated SDK example")
    parser.add_argument(
        "--base-url",
        default="https://replicated.app",
        help="Base URL for the Replicated API (default: https://replicated.app)",
    )
    parser.add_argument(
        "--publishable-key",
        required=True,
        help="Your Replicated publishable key (required)",
    )
    parser.add_argument(
        "--app-slug", required=True, help="Your application slug (required)"
    )
    parser.add_argument(
        "--customer-email",
        default="user@example.com",
        help="Customer email address (default: user@example.com)",
    )
    parser.add_argument("--channel", help="Channel for the customer (optional)")
    parser.add_argument("--customer-name", help="Customer name (optional)")
    parser.add_argument(
        "--status",
        choices=["missing", "unavailable", "ready", "updating", "degraded"],
        default="ready",
        help="Instance status (default: ready)",
    )
    parser.add_argument(
        "--version",
        default="",
        help="Application version (optional)",
    )

    args = parser.parse_args()

    print("Initializing Replicated client...")
    print(f"Base URL: {args.base_url}")
    print(f"App Slug: {args.app_slug}")

    # Initialize the client
    with ReplicatedClient(
        publishable_key=args.publishable_key,
        app_slug=args.app_slug,
        base_url=args.base_url,
    ) as client:
        print("✓ Replicated client initialized successfully")

        # Create or get customer
        channel_info = f" (channel: {args.channel})" if args.channel else ""
        name_info = f" (name: {args.customer_name})" if args.customer_name else ""
        print(
            f"\nCreating/getting customer with email: "
            f"{args.customer_email}{channel_info}{name_info}"
        )
        customer = client.customer.get_or_create(
            email_address=args.customer_email,
            channel=args.channel,
            name=args.customer_name,
        )
        print(f"✓ Customer created/retrieved - ID: {customer.customer_id}")

        # Create or get instance
        print("\nCreating/getting instance for customer...")
        instance = customer.get_or_create_instance()
        print(f"✓ Instance created/retrieved - ID: {instance.instance_id}")

        # Set instance status
        instance.set_status(args.status)
        print(f"✓ Instance status set to: {args.status}")

        # Set instance version if provided
        if args.version:
            instance.set_version(args.version)
            print(f"✓ Instance version set to: {args.version}")

        print("\n🎉 Basic example completed successfully!")
        print(f"Customer ID: {customer.customer_id}")
        print(f"Instance ID: {instance.instance_id}")


if __name__ == "__main__":
    main()
