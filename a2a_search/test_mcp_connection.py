# test_mcp_connection.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_connection():
    server_params = StdioServerParameters(
        command="docker",
        args=["run", "-i", "--rm", "duckduck"]
    )
    
    print("🔗 Connecting to server...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            print("✅ Stdio connection established")
            
            async with ClientSession(read, write) as session:
                print("✅ Session created")
                
                print("🔄 Initializing session...")
                await session.initialize()
                print("✅ Session initialized!")
                
                # Lister les tools disponibles
                tools = await session.list_tools()
                print(f"✅ Tools available: {tools}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())