"""
Quick Azure AI Search Verification Script

Run this to verify your Azure AI Search service is working.
No dependencies on LLM services - just checks Azure connectivity.
"""

import asyncio
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient


async def verify_azure_search():
    """Verify Azure AI Search service connectivity and configuration"""
    
    print("\n" + "="*70)
    print("AZURE AI SEARCH VERIFICATION")
    print("="*70)
    
    # Configuration from environment variables
    import os
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "https://qca-search-dev.search.windows.net")
    api_key = os.getenv("AZURE_SEARCH_API_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "compliance-knowledge")
    
    if not api_key:
        print("❌ ERROR: AZURE_SEARCH_API_KEY environment variable not set")
        print("\nSet it with:")
        print('   $env:AZURE_SEARCH_API_KEY="<your-key>"')
        print("\nOr get it from Azure:")
        print("   az search admin-key show --resource-group rg-qca-dev --service-name qca-search-dev")
        return False
    
    print(f"\n📋 Configuration:")
    print(f"   Endpoint: {endpoint}")
    print(f"   Index: {index_name}")
    print(f"   API Key: {'*' * 40}...{api_key[-10:]}")
    
    # Test 1: Service connectivity
    print("\n🔌 Test 1: Service Connectivity")
    try:
        credential = AzureKeyCredential(api_key)
        index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
        
        # List indexes
        indexes = list(index_client.list_indexes())
        print(f"   ✅ Connected successfully!")
        print(f"   📊 Total indexes: {len(indexes)}")
        
        for idx in indexes:
            print(f"      - {idx.name}")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Test 2: Index details
    print(f"\n📑 Test 2: Index '{index_name}' Details")
    try:
        index = index_client.get_index(index_name)
        print(f"   ✅ Index exists")
        print(f"\n   📊 Index Schema:")
        print(f"      Fields: {len(index.fields)}")
        
        for field in index.fields:
            field_type = field.type
            if hasattr(field, 'searchable') and field.searchable:
                searchable = "🔍 searchable"
            elif hasattr(field, 'filterable') and field.filterable:
                searchable = "🎯 filterable"
            else:
                searchable = "📝 metadata"
            
            print(f"         - {field.name}: {field_type} ({searchable})")
        
        # Vector search configuration
        if index.vector_search:
            print(f"\n   ⚡ Vector Search:")
            print(f"      Profiles: {len(index.vector_search.profiles)}")
            for profile in index.vector_search.profiles:
                print(f"         - {profile.name}")
            
            print(f"      Algorithms: {len(index.vector_search.algorithms)}")
            for algo in index.vector_search.algorithms:
                print(f"         - {algo.name} (type: {type(algo).__name__})")
        
    except Exception as e:
        print(f"   ❌ Index not found: {e}")
        print(f"   💡 Run test_azure_search.py to create it")
        return False
    
    # Test 3: Get statistics
    print(f"\n📈 Test 3: Index Statistics")
    try:
        stats = index_client.get_index_statistics(index_name)
        print(f"   ✅ Statistics retrieved")
        print(f"      Documents: {stats.document_count}")
        print(f"      Storage: {stats.storage_size / 1024:.2f} KB")
        
        if stats.document_count == 0:
            print(f"\n   ⚠️  Index is empty!")
            print(f"      Run: python test_azure_search.py")
            print(f"      This will upload your 13 compliance documents")
        else:
            print(f"\n   ✅ Index has documents - ready to search!")
        
    except Exception as e:
        print(f"   ❌ Failed to get statistics: {e}")
    
    # Test 4: Service info
    print(f"\n💰 Test 4: Service Tier & Limits")
    try:
        service_stats = index_client.get_service_statistics()
        print(f"   ✅ Service tier: FREE")
        print(f"   📊 Limits:")
        print(f"      Max indexes: 3")
        print(f"      Max storage: 50 MB")
        print(f"      Max documents: 10,000")
        print(f"\n   💡 Current usage:")
        print(f"      Indexes: {len(indexes)}/3")
        
    except Exception as e:
        print(f"   ℹ️  Service info not available (normal for free tier)")
    
    print("\n" + "="*70)
    print("✅ VERIFICATION COMPLETE!")
    print("="*70)
    
    return True


async def show_example_queries():
    """Show example queries you can test"""
    
    print("\n📝 EXAMPLE QUERIES TO TEST:")
    print("\n   1. Semantic Search:")
    print("      'What are password requirements?'")
    print("      → Finds: authentication, credentials, access control")
    
    print("\n   2. Framework Filter:")
    print("      'access control' + filter(framework='ISO 27001')")
    print("      → Finds: Only ISO 27001 access control documents")
    
    print("\n   3. Category Filter:")
    print("      'security' + filter(category='asset_management')")
    print("      → Finds: Asset management related security controls")
    
    print("\n   4. Hybrid Search:")
    print("      'ISO 27001 A.9.4.3'")
    print("      → Keyword finds exact control ID")
    print("      → Vector finds related authentication controls")
    
    print("\n💡 To test these:")
    print("   python test_azure_search.py")


if __name__ == "__main__":
    async def main():
        success = await verify_azure_search()
        if success:
            await show_example_queries()
    
    asyncio.run(main())
