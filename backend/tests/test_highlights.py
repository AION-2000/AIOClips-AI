import pytest
from app.highlights import suggest_highlights

def test_empty_scene_list_still_returns_candidate():
    results=suggest_highlights(120,[])
    assert results and all(0<=x.start<=90 for x in results)

def test_short_source_is_clamped():
    assert suggest_highlights(8,[2,4])[0].duration==8

def test_no_significant_overlap():
    clips=suggest_highlights(240,list(range(10,240,10)))
    for i,a in enumerate(clips):
        for b in clips[i+1:]:
            overlap=max(0,min(a.start+a.duration,b.start+b.duration)-max(a.start,b.start))
            assert overlap/a.duration<.4

@pytest.mark.parametrize('duration',[0,-1,float('nan'),float('inf')])
def test_invalid_duration(duration):
    with pytest.raises(ValueError):
        suggest_highlights(duration,[])

def test_limit():
    assert len(suggest_highlights(900,list(range(10,900,10)),limit=3))<=3
