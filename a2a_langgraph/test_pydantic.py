from pydantic_ai import Agent
import asyncio
import os

# Set a dummy API key for testing structure (won't actually call the API)
os.environ['GOOGLE_API_KEY'] = 'dummy-key-for-testing'

async def test():
    try:
        agent = Agent(model='google-gla:gemini-2.5-flash-lite', output_type=str, system_prompt='You are helpful')
        print("Agent created successfully")
        
        # Try to run a simple query and inspect the result structure
        print("Attempting to run agent...")
        result = await agent.run('hello')
        
        print('Result type:', type(result))
        print('Result dir:', [attr for attr in dir(result) if not attr.startswith('_')])
        
        # Check for common attributes
        attrs_to_check = ['data', 'value', 'result', 'output', 'content', 'response']
        for attr in attrs_to_check:
            if hasattr(result, attr):
                print(f'Has {attr}: True - Value: {getattr(result, attr)}')
            else:
                print(f'Has {attr}: False')
        
        # Try string conversion
        print('String representation:', str(result))
        
        return result
        
    except Exception as e:
        print(f"Error during test: {e}")
        print("This is expected since we're using a dummy API key")
        # Even with the error, we can analyze what we know about the structure
        return None

if __name__ == "__main__":
    asyncio.run(test())