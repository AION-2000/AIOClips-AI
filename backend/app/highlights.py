"""Explainable scene-cut highlight suggestions; not generative AI."""
from __future__ import annotations
import math
import re
import subprocess
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Candidate:
    start: float
    duration: float
    score: float
    reason: str

def detect_scene_changes(path: str, *, timeout: int = 90) -> list[float]:
    cmd = ['ffmpeg','-hide_banner','-nostdin','-i',path,'-filter:v',"select='gt(scene,0.32)',showinfo",'-an','-f','null','-']
    result = subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,check=False)
    if result.returncode:
        raise RuntimeError('Scene analysis failed')
    return [float(t) for t in re.findall(r'pts_time:([0-9]+(?:\.[0-9]+)?)',result.stderr)]

def suggest_highlights(duration: float, cuts: list[float], *, clip_length: float = 30, limit: int = 6) -> list[Candidate]:
    if not math.isfinite(duration) or duration <= 0 or not math.isfinite(clip_length) or clip_length <= 0 or not 1 <= limit <= 20:
        raise ValueError('Invalid highlight parameters')
    length=min(clip_length,duration)
    valid=sorted(set(t for t in cuts if math.isfinite(t) and 0<t<duration))
    starts={0.0,max(0.0,duration-length)}
    for t in valid:
        starts.add(max(0.0,min(duration-length,t-length*.25)))
        starts.add(max(0.0,min(duration-length,t-length*.5)))
    if duration>length:
        count=min(20,int(duration/max(10,length/2)))
        for i in range(1,count+1):
            starts.add((duration-length)*i/(count+1))
    ranked=[]
    for start in starts:
        count=sum(start<t<start+length for t in valid)
        score=round(.35+.55*min(count,8)/8+.1*(1-start/max(duration,1)),3)
        ranked.append(Candidate(round(start,2),round(length,2),score,f'{count} scene transitions in selected window'))
    ranked.sort(key=lambda c:(-c.score,c.start))
    selected=[]
    for item in ranked:
        if all(max(0,min(item.start+item.duration,other.start+other.duration)-max(item.start,other.start))/item.duration<.4 for other in selected):
            selected.append(item)
        if len(selected)>=limit: break
    return selected

def analyze_video(path: str,duration: float,clip_length: float=30,limit: int=6) -> list[dict]:
    return [asdict(c) for c in suggest_highlights(duration,detect_scene_changes(path),clip_length=clip_length,limit=limit)]
