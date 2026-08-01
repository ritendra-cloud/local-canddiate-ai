import json, time
from collections.abc import AsyncIterator
import httpx
class OllamaError(RuntimeError): pass
class OllamaUnavailable(OllamaError): pass
class OllamaStreamError(OllamaError): pass
async def status(base_url: str, model: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3, connect=1.5)) as client:
            response = await client.get(f'{base_url}/api/tags'); response.raise_for_status()
        names=[item.get('name','') for item in response.json().get('models', [])]
        return {'reachable': True, 'base_url': base_url, 'configured_model': model, 'model_available': model in names}
    except (httpx.HTTPError, ValueError) as exc:
        return {'reachable': False, 'base_url': base_url, 'configured_model': model, 'model_available': False, 'error': 'Ollama is unavailable'}

async def stream_chat(base_url: str, model: str, messages: list[dict], options: dict) -> AsyncIterator[str]:
    payload={'model':model,'messages':messages,'stream':True,'options':options}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90, connect=3, read=60)) as client:
            async with client.stream('POST', f'{base_url}/api/chat', json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line: continue
                    try: item=json.loads(line)
                    except json.JSONDecodeError as exc: raise OllamaStreamError('Invalid response from the local model.') from exc
                    if item.get('error'): raise OllamaStreamError('Local model generation failed.')
                    content=item.get('message',{}).get('content','')
                    if content: yield content
                    if item.get('done'): return
    except httpx.HTTPError as exc:
        raise OllamaUnavailable('Local Ollama is unavailable.') from exc

async def structured_chat_details(base_url: str, model: str, messages: list[dict], schema: dict, options: dict) -> tuple[dict,dict]:
    payload={'model':model,'messages':messages,'stream':False,'think':False,'format':schema,'options':options}
    started=time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120,connect=3,read=100)) as client:
            response=await client.post(f'{base_url}/api/chat',json=payload); response.raise_for_status(); data=response.json()
        content=data.get('message',{}).get('content')
        if not isinstance(content,str): raise OllamaStreamError('Invalid structured response from the local model.')
        return json.loads(content),{'model':model,'prompt_characters':sum(len(m.get('content','')) for m in messages),'schema_characters':len(json.dumps(schema)),'output_characters':len(content),'duration_ms':round((time.monotonic()-started)*1000),'done_reason':data.get('done_reason')}
    except json.JSONDecodeError as exc: raise OllamaStreamError('Invalid structured response from the local model.') from exc
    except httpx.HTTPError as exc: raise OllamaUnavailable('Local Ollama is unavailable.') from exc
async def structured_chat(base_url: str, model: str, messages: list[dict], schema: dict, options: dict) -> dict:
    return (await structured_chat_details(base_url,model,messages,schema,options))[0]
