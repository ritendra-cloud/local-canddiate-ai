import json, re, unicodedata
from datetime import date
from enum import Enum
from pathlib import Path
from app.config import settings
from app.services.candidate_service import load_profile

PROMPT = (Path(__file__).resolve().parents[1] / 'prompts' / 'candidate_chat.txt').read_text()
SCOPE_REFUSAL="I can only answer questions about the candidate’s verified profile, experience, skills, certifications, achievements, and job alignment. I cannot provide general-purpose coding or unrelated assistance."
class Scope(str,Enum): IN_SCOPE='IN_SCOPE'; OUT_OF_SCOPE='OUT_OF_SCOPE'; AMBIGUOUS='AMBIGUOUS'
def chat_scope(message:str, history=()):
    text=normalize_chat_query(message)
    generic=re.compile(r'\b(write|generate|create|implement|solve|fix)\b.*\b(code|program|function|algorithm|api|query|test)\b|\b(explain|translate|calculate)\b|system prompt|ignore previous instructions|coding assistant')
    anchors=re.compile(r'candidate|profile|resume|experience|skill|certification|role|project|achievement|employer|company|leadership|\b(he|his)\b')
    employment=re.search(r'(calculate|total|years|career span|tenure|joining|join date|first job|resume date|latest.*date|actual).*?(experience|employment|role|resume|job)|experience.*?(date|calculate|resume)',text)
    if employment: return Scope.IN_SCOPE,'EMPLOYMENT_DURATION',True
    if re.search(r'\b(ge|beckman|siemens|nse)\b.*\b(start|join|joining|end|left|last|tenure|role|date)\b',text): return Scope.IN_SCOPE,'EMPLOYMENT_FACT',True
    if generic.search(text): return Scope.OUT_OF_SCOPE,'GENERAL_ASSISTANCE',False
    recruiter=re.compile(r'total experience|experience|years|current company|latest role|primary skills|automation|api testing|certification|education|employer|leadership|patent|publication')
    if anchors.search(text) or recruiter.search(text): return Scope.IN_SCOPE,'CANDIDATE_SUBJECT',True
    return Scope.OUT_OF_SCOPE,'NO_CANDIDATE_ANCHOR',False
def normalize_chat_query(message:str):
    text=unicodedata.normalize('NFKC',message).lower(); text=re.sub(r'[^\w\s/+.-]',' ',text)
    aliases={'exp':'experience','yrs':'years','yoe':'years experience','cert':'certification','certs':'certifications','edu':'education','tech':'technology','techs':'technologies','proj':'project','projs':'projects','resp':'responsibility','canddiate':'candidate','candidte':'candidate','candiate':'candidate','candate':'candidate','canidate':'candidate','candiadate':'candidate','experiance':'experience','certfication':'certification'}
    return ' '.join(aliases.get(token,token) for token in text.split())
def total_experience_answer(message:str, profile):
    text=normalize_chat_query(message)
    if re.search(r'\b(total|years|how many)\b.*\bexperience\b|\bexperience\b.*\b(total|years)\b|^experience$',text):
        summary=profile.candidate.professional_summary or ''
        match=re.search(r'\b(\d+\+?\s+years?)\b',summary,re.I)
        if match: return f'The candidate has more than {match.group(1).replace("years","years of")} professional experience across QA automation, software testing, framework development, API testing, and related engineering roles.'
        return 'The candidate profile lists the employment history, but it does not provide a verified total experience figure.'
    return None
def employment_duration_answer(message,profile,as_of=None):
    text=normalize_chat_query(message)
    if not re.search(r'calculate|joining|join date|first job|resume date|career span|tenure|actual.*experience|experience.*date|overlap',text): return None
    months={'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'september':9,'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}
    def parse(value,current=False):
        if current: return as_of or date.today()
        bits=(value or '').lower().replace(',','').split()
        if len(bits)>=2 and bits[0] in months and bits[1].isdigit(): return date(int(bits[1]),months[bits[0]],1)
        return None
    intervals=[]
    for item in profile.experience:
        start=parse(item.start_date); end=parse(item.end_date, str(item.end_date or '').lower() in {'present','current','till date'})
        if start and end and end>=start: intervals.append((start,end))
    if not intervals: return 'The candidate profile does not contain sufficiently precise employment dates to calculate a verified duration.'
    intervals.sort(); earliest=intervals[0][0]; latest=max(end for _,end in intervals); merged=[]
    for start,end in intervals:
        if merged and start<=merged[-1][1]: merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else: merged.append((start,end))
    months_between=lambda start,end:(end.year-start.year)*12+end.month-start.month
    span=months_between(earliest,latest); worked=sum(months_between(start,end) for start,end in merged)
    fmt=lambda number:f'{number//12} years {number%12} months'
    return f'Using the verified employment dates in the resume: Career span: approximately {fmt(span)}, from {earliest.strftime("%b %Y")} to {latest.strftime("%b %Y")}. Non-overlapping verified employment duration: approximately {fmt(worked)}. The second figure avoids double-counting overlapping roles.'
def candidate_fact_answer(message,profile):
    text=normalize_chat_query(message)
    if 'education' in text or 'college' in text or 'institution' in text:
        aliases={'MSRIT':'M. S. Ramaiah Institute of Technology, Bangalore','CDAC':'Centre for Development of Advanced Computing, Pune'}
        names=[aliases.get(item.institution,item.institution) for item in profile.education]
        return 'The candidate’s education includes:\n'+'\n'.join(f'{i+1}. {name}' for i,name in enumerate(names))
    aliases={'ge':'General Electric Healthcare','ge healthcare':'General Electric Healthcare','general electric healthcare':'General Electric Healthcare','beckman':'Beckman Coulter','beckman coulter':'Beckman Coulter','siemens':'Siemens Information Systems Ltd, Bangalore','nse':'National Stock Exchange of India Limited'}
    employer=None
    for alias,name in aliases.items():
        if re.search(rf'\b{re.escape(alias)}\b',text): employer=next((item for item in profile.experience if item.company==name),None); break
    month_order={'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'september':9,'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}
    def chronology(item):
        parts=(item.start_date or '').lower().split()
        return (int(parts[1]) if len(parts)>1 and parts[1].isdigit() else 9999,month_order.get(parts[0],99))
    ordered=sorted(profile.experience,key=chronology)
    ordinal=re.search(r'\b(\d+)(?:st|nd|rd|th)\s+company\b',text)
    if ordinal:
        index=int(ordinal.group(1))-1; employer=ordered[index] if 0<=index<len(ordered) else None
    if employer:
        if re.search(r'\b(start|join|joining|started)\b',text): return f'{employer.company} started in {employer.start_date}.' if employer.start_date else 'That information is not included in the candidate profile.'
        if re.search(r'\b(end|left|last|employment date)\b',text): return f'{employer.company} ended in {employer.end_date}.' if employer.end_date else 'That information is not included in the candidate profile.'
        if ordinal: return employer.company
    return None
def chat_messages(history, current: str) -> list[dict]:
    profile=load_profile(settings.candidate_path).model_dump(mode='json')
    profile.pop('import_metadata', None)
    system=f'{PROMPT}\n\nCANDIDATE_PROFILE:\n{json.dumps(profile, ensure_ascii=False)}'
    messages=[{'role':'system','content':system}]
    messages += [{'role':m.role,'content':m.content} for m in history]
    messages.append({'role':'user','content':current})
    return messages
def generation_options(): return {'temperature':settings.chat_temperature,'num_ctx':settings.chat_num_ctx,'num_predict':settings.chat_num_predict,'top_p':settings.chat_top_p,'repeat_penalty':settings.chat_repeat_penalty}
