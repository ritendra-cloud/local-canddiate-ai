#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT/'backend'))
from app.config import settings
from app.services.resume_import_service import extract_docx, build_profile
def main():
    source=settings.resume_file; output=settings.candidate_path
    if not source.exists(): raise SystemExit(f'Resume missing: {source}')
    try: lines=extract_docx(source)
    except Exception as exc: raise SystemExit(f'Invalid DOCX: {exc}')
    if not lines: raise SystemExit('No usable text found in resume.')
    profile=build_profile(lines); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(profile.model_dump(mode='json'), indent=2)+'\n')
    meta=profile.import_metadata; print(f'Source: {source}\nOutput: {output}\nSections: {", ".join(meta.sections_detected) or "none"}\nSkills: {sum(map(len,profile.skills.values()))}\nExperience: {len(profile.experience)}\nUnclassified blocks: {meta.unclassified_block_count}\nWarnings: {"; ".join(meta.warnings)}')
if __name__=='__main__': main()
