import json
from pathlib import Path
from app.config import settings
from app.services.candidate_service import load_profile

PROMPT = (Path(__file__).resolve().parents[1] / 'prompts' / 'candidate_chat.txt').read_text()
def chat_messages(history, current: str) -> list[dict]:
    profile=load_profile(settings.candidate_path).model_dump(mode='json')
    profile.pop('import_metadata', None)
    system=f'{PROMPT}\n\nCANDIDATE_PROFILE:\n{json.dumps(profile, ensure_ascii=False)}'
    messages=[{'role':'system','content':system}]
    messages += [{'role':m.role,'content':m.content} for m in history]
    messages.append({'role':'user','content':current})
    return messages
def generation_options(): return {'temperature':settings.chat_temperature,'num_ctx':settings.chat_num_ctx,'num_predict':settings.chat_num_predict,'top_p':settings.chat_top_p,'repeat_penalty':settings.chat_repeat_penalty}
