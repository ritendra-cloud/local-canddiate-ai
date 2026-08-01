import json
from pathlib import Path
from app.models.candidate import CandidateProfile
class ProfileNotFound(FileNotFoundError): pass
def load_profile(path: Path) -> CandidateProfile:
    if not path.exists(): raise ProfileNotFound('Candidate profile has not been imported yet.')
    return CandidateProfile.model_validate(json.loads(path.read_text()))
def public_profile(profile: CandidateProfile) -> dict:
    data=profile.model_dump(mode='json'); data.pop('import_metadata', None); return data
