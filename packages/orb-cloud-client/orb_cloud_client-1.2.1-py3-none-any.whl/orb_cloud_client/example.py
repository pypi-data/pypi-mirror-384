#!/usr/bin/env python3
"""
Example usage of the Orb Cloud API Client.

This example demonstrates:
1. Getting a list of devices for an organization
2. Displaying the devices and letting the user select one
3. Asking the user for a URL to push data to
4. Configuring temporary datasets for the selected device with data push
"""

import os
import sys
from typing import Optional, List

# Add the client to the path (for running this example directly)
sys.path.insert(0, os.path.dirname(__file__))

from client import OrbCloudClient
from models import TempDatasetsRequest, Datasets, DataPush, Device


def get_and_display_devices(client: OrbCloudClient, organization_id: str) -> List[Device]:
    """Get and display all devices for the organization."""
    print(f"Getting devices for organization: {organization_id}")
    
    try:
        devices = client.get_organization_devices(organization_id)
        print(f"Found {len(devices)} devices:\n")
        
        for i, device in enumerate(devices, 1):
            connection_status = "Connected" if device.is_connected.value == 1 else "Disconnected"
            print(f"{i:2}. {device.name}")
            print(f"    orb_id: {device.orb_id}")
            print(f"    status: {connection_status}")
            print()
        
        return devices
        
    except Exception as e:
        print(f"Error getting devices: {e}")
        return []


def select_device(devices: List[Device]) -> Optional[Device]:
    """Allow user to select a device from the list."""
    if not devices:
        print("No devices available to select from.")
        return None
    
    while True:
        try:
            choice = input(f"Select a device (1-{len(devices)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("Exiting...")
                return None
            
            device_index = int(choice) - 1
            
            if 0 <= device_index < len(devices):
                selected_device = devices[device_index]
                print(f"Selected: {selected_device.name}")
                return selected_device
            else:
                print(f"Please enter a number between 1 and {len(devices)}")
                
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\nExiting...")
            return None


def get_push_url() -> Optional[str]:
    """Get the push URL from the user."""
    while True:
        try:
            url = input("\nEnter the URL to push data to (or 'q' to quit): ").strip()
            
            if url.lower() == 'q':
                print("Exiting...")
                return None
            
            if not url:
                print("Please enter a valid URL")
                continue
            
            # Basic URL validation
            if not (url.startswith('http://') or url.startswith('https://')):
                print("URL should start with http:// or https://")
                continue
            
            print(f"Will push data to: {url}")
            return url
            
        except KeyboardInterrupt:
            print("\nExiting...")
            return None


def configure_temp_datasets(client: OrbCloudClient, device_id: str, push_url: str) -> bool:
    """Configure temporary datasets for the specified device."""
    print(f"Configuring temporary datasets for device: {device_id}")
    
    # Create the temporary datasets configuration
    temp_config = TempDatasetsRequest(
        duration="5m",  # Run for 5 minutes
        datasets_config=Datasets(
            enabled=True,
            datasets=["responsiveness_1s", "scores_1s"],  # Collect these datasets
            push=DataPush(
                enabled=True,
                url=push_url,  # Use the user-provided URL
                datasets=["responsiveness_1s", "scores_1s"],
                format="json",
                interval_ms=500 # Push new data every 500ms (when available)
            )
        )
    )
    
    try:
        result = client.configure_temporary_datasets(device_id, temp_config)
        print(f"Temporary datasets configured successfully: {result}")
        return True
        
    except Exception as e:
        print(f"Error configuring temporary datasets: {e}")
        return False


def main():
    """Main example function."""
    # Get configuration from environment variables
    api_token = os.getenv("ORB_API_TOKEN")
    organization_id = os.getenv("ORB_ORGANIZATION_ID")
    
    if not api_token:
        print("Error: Please set ORB_API_TOKEN environment variable")
        sys.exit(1)
    
    if not organization_id:
        print("Error: Please set ORB_ORGANIZATION_ID environment variable")
        sys.exit(1)
    
    print("Orb Cloud API Client Example")
    print("=" * 30)
    
    # Create the client
    with OrbCloudClient(token=api_token) as client:
        # Step 1: Get and display all devices
        devices = get_and_display_devices(client, organization_id)
        
        if not devices:
            print("No devices found. Exiting.")
            sys.exit(1)
        
        # Step 2: Let user select a device
        selected_device = select_device(devices)
        
        if not selected_device:
            sys.exit(0)
        
        # Step 3: Get the push URL from user
        push_url = get_push_url()
        
        if not push_url:
            sys.exit(0)
        
        # Step 4: Configure temporary datasets for the selected device
        success = configure_temp_datasets(client, selected_device.orb_id, push_url)
        
        if success:
            print("\nExample completed successfully!")
            print(f"Device '{selected_device.name}' is now configured to collect temporary datasets.")
            print(f"Data will be pushed to: {push_url}")
        else:
            print("\nExample failed to configure temporary datasets.")
            sys.exit(1)


if __name__ == "__main__":
    main()
