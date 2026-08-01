import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from app.models.candidate import CandidateProfile
def test_example_validates(): CandidateProfile.model_validate(json.loads((Path(__file__).parents[2]/'data/processed/candidate.example.json').read_text()))
def test_negative_skill_years_rejected():
    with pytest.raises(ValidationError): CandidateProfile.model_validate({'last_updated':'now','candidate':{},'skills':{'x':[{'name':'Python','years':-1}]},'import_metadata':{'imported_at':'now'}})
