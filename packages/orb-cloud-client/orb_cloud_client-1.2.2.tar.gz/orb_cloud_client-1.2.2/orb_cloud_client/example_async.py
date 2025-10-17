from client import OrbCloudClientAsync
import asyncio
import os


async def main():
    """
    Example of using the OrbCloudClientAsync to fetch organization devices.

    Requires ORB_CLOUD_TOKEN and ORB_CLOUD_ORGANIZATION_ID environment variables to be set.
    """
    token = os.environ.get("ORB_CLOUD_TOKEN")

    if not token:
        print("Please set ORB_CLOUD_TOKEN environment variables.")
        return

    print("Getting organization...")
    async with OrbCloudClientAsync(token=token) as client:
        organizations = await client.get_organizations()
        if not organizations:
            print("No organizations found for this token.")
            return

        print("Organizations found:")
        for org in organizations:
            print(f"  - ID: {org.organization_id}, Name: {org.name}")

            print(f"Fetching devices for organization: {org.organization_id}")
            try:
                devices = await client.get_organization_devices(org.organization_id)
                if not devices:
                    print("No devices found for this organization.")
                    return

                print("Devices found:")
                for device in devices:
                    print(f"  - ID: {device.orb_id}, Name: {device.name}")
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())



