#!/usr/bin/env python3
"""
Test script with real SAP Datasphere credentials
"""

import asyncio
from sap_datasphere_mcp.models import DatasphereConfig
from sap_datasphere_mcp.client import DatasphereClient


async def test_real_connection():
    """Test with your actual Datasphere credentials"""
    
    # Load credentials from environment variables
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    config = DatasphereConfig(
        tenant_url=os.getenv("DATASPHERE_TENANT_URL", "https://your-tenant.eu10.hcs.cloud.sap"),
        tenant_id=os.getenv("DATASPHERE_TENANT_ID", "your-tenant-id"),
        oauth_client_id=os.getenv("OAUTH_CLIENT_ID", "your-client-id"),
        oauth_client_secret=os.getenv("OAUTH_CLIENT_SECRET", "your-client-secret"),
        oauth_token_url=os.getenv("OAUTH_TOKEN_URL", "https://your-auth.authentication.eu20.hana.ondemand.com/oauth/token"),
        oauth_authorization_url=os.getenv("OAUTH_AUTHORIZATION_URL", "https://your-auth.authentication.eu20.hana.ondemand.com/oauth/authorize")
    )
    
    client = DatasphereClient(config)
    
    try:
        print("🚀 Testing SAP Datasphere MCP Client")
        print("=" * 50)
        
        # Test connection
        print("\n🔐 Testing OAuth connection...")
        result = await client.test_connection()
        if result.success:
            print("✅ OAuth authentication successful!")
            print(f"   Tenant: {result.data['tenant_url']}")
        else:
            print(f"❌ OAuth failed: {result.error}")
            return
        
        # Discover endpoints
        print("\n🔍 Discovering API endpoints...")
        result = await client.discover_api_endpoints()
        if result.success:
            endpoints = result.data["working_endpoints"]
            if endpoints:
                print(f"✅ Found {len(endpoints)} working endpoints:")
                for ep in endpoints:
                    print(f"   • {ep['endpoint']} (HTTP {ep['status_code']})")
            else:
                print("⚠️ No working endpoints found")
                print("   This is expected - we need to find the correct API paths")
        
        # Try to list spaces
        print("\n🏢 Attempting to list spaces...")
        result = await client.list_spaces()
        if result.success:
            spaces = result.data
            if spaces:
                print(f"✅ Found {len(spaces)} spaces:")
                for space in spaces:
                    print(f"   • {space['name']} (ID: {space['id']})")
            else:
                print("📭 No spaces found")
        else:
            print(f"❌ Failed to list spaces: {result.error}")
        
        # Try to list catalog
        print("\n📊 Attempting to list catalog...")
        result = await client.list_catalog()
        if result.success:
            items = result.data
            if items:
                print(f"✅ Found {len(items)} catalog items:")
                for item in items[:5]:
                    print(f"   • {item['name']} ({item['type']})")
                if len(items) > 5:
                    print(f"   ... and {len(items) - 5} more")
            else:
                print("📭 No catalog items found")
        else:
            print(f"❌ Failed to list catalog: {result.error}")
        
        print(f"\n🎉 Test completed!")
        print(f"\n💡 Next steps:")
        print(f"   • OAuth is working perfectly ✅")
        print(f"   • Need to find correct API endpoints for your tenant")
        print(f"   • Check Datasphere admin console for API documentation")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_real_connection())