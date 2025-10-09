import asyncio
import httpx
from dotenv import load_dotenv
from client.orchestrator import dynamic_orchestrator_agent, DynamicAgentRegistry, DynamicOrchestratorContext

load_dotenv()

async def test_result_structure():
    """Test to understand the AgentRunResult structure"""
    registry = DynamicAgentRegistry()
    
    async with httpx.AsyncClient() as httpx_client:
        context = DynamicOrchestratorContext(registry, httpx_client)
        
        try:
            print("Testing orchestrator agent result structure...")
            result = await dynamic_orchestrator_agent.run("hello", deps=context)
            
            print(f"Result type: {type(result)}")
            print(f"Result attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")
            
            # Test common attributes
            common_attrs = ['data', 'value', 'result', 'output', 'content', 'response']
            for attr in common_attrs:
                if hasattr(result, attr):
                    print(f"✅ Has {attr}: {getattr(result, attr)}")
                else:
                    print(f"❌ No {attr} attribute")
            
            print(f"String representation: {str(result)}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_result_structure())