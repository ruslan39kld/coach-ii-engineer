import asyncio
import httpx
import config

async def test_api():
    print(f"API Endpoint: {config.CLAUDE_ENDPOINT}")
    print(f"Model: {config.CLAUDE_MODEL}")
    print(f"API Key: {config.CLAUDE_API_KEY[:20]}..." if config.CLAUDE_API_KEY else "НЕ УСТАНОВЛЕН")
    
    print("\nОтправка тестового запроса...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                config.CLAUDE_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {config.CLAUDE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.CLAUDE_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Привет! Ответь одним словом: работает?"
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 100
                }
            )
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ API работает!")
                print(f"Ответ: {result.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
            else:
                print(f"\n❌ Ошибка API: {response.status_code}")
                
    except httpx.TimeoutException:
        print("\n❌ Timeout - API не отвечает")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

asyncio.run(test_api())
