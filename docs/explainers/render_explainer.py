"""Render the offline explainer from its single, timed narration source."""

import argparse
import hashlib
import html
import json
import subprocess
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TEMP = ROOT.parent / "_tmp" / "completion-report-grading" / "explainer-media"
FONT = Path("C:/Windows/Fonts/segoeui.ttf")
BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")
WIDTH, HEIGHT = 1280, 720


def run(args, *, cwd=None, input_text=None, timeout=300):
    result = subprocess.run(args, cwd=cwd, input=input_text, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {args[0]}\n{result.stderr[-4000:]}")
    return result.stdout


def write(path, text):
    path.write_bytes(text.encode("utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    return json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                           "-of", "json", str(path)]))


def validate(content):
    assert content["schema_version"] == 1
    assert content["title"] and isinstance(content["facts"], dict)
    facts = content["facts"]
    assert [c["false_approvals"] for c in facts["conditions"]] == [2, 3, 4, 3]
    assert (facts["defective_cases"], facts["controls"], facts["primary_extra"],
            facts["primary_threshold"], facts["mitigation_reduction"], facts["mitigation_target"],
            facts["h16_expected"], facts["h16_actual"]) == (12, 6, 1, 2, 1, 2, 1, 2)
    assert set(content["voices"]) == {"casey", "morgan"}
    for name, voice in content["voices"].items():
        assert voice["label"] and voice["sapi_name"] and isinstance(voice["rate"], int), name
    ids = set()
    for scene in content["scenes"]:
        assert scene["id"] not in ids and all(scene[k] for k in ("id", "chapter", "title", "visual", "lines"))
        ids.add(scene["id"])
        for line in scene["lines"]:
            assert line["speaker"] in content["voices"] and line["text"].strip()
    assert ids


def synthesize(content, scenes):
    requests = []
    for scene in scenes:
        for line in scene["lines"]:
            voice = content["voices"][line["speaker"]]
            requests.append({"path": str(TEMP / f"voice-{len(requests):04d}.wav"),
                             "voice": voice["sapi_name"], "rate": voice["rate"], "text": line["text"]})
    script = r'''$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$items = [Console]::In.ReadToEnd() | ConvertFrom-Json
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  foreach ($item in $items) {
    $s.SelectVoice($item.voice)
    $s.Rate = [int]$item.rate
    $s.SetOutputToWaveFile($item.path)
    $s.Speak($item.text)
    $s.SetOutputToNull()
  }
} finally { $s.Dispose() }
'''
    run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        input_text=json.dumps(requests, ensure_ascii=True), timeout=240)
    for item in requests:
        path = Path(item["path"])
        with wave.open(str(path), "rb") as audio:
            item["duration"] = audio.getnframes() / audio.getframerate()
            if item["duration"] <= 0:
                raise ValueError(f"Empty speech: {path.name}")
    return requests


def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT), size)


def wrap(draw, text, face, width):
    lines = []
    for paragraph in str(text).split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if line and draw.textlength(candidate, font=face) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
    return lines


def card(scene, index):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f7f1e5")
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, WIDTH, 15), fill="#e46c42")
    d.text((68, 40), "FIELD NOTES  /  " + str(scene["chapter"]).upper(), font=font(19, True), fill="#ab4d31")
    y = 85
    for line in wrap(d, scene["title"], font(43, True), 1120)[:2]:
        d.text((68, y), line, font=font(43, True), fill="#202b31")
        y += 55
    d.rounded_rectangle((64, 205, 1216, 560), radius=22, fill="#fffaf1", outline="#dfd4c2", width=2)
    key = (scene["visual"] + " " + scene["title"]).lower()
    if any(w in key for w in ("result", "holdout", "comparison", "bar chart", "matrix")):
        d.text((96, 224), "FALSE APPROVALS / 12 DEFECTIVE HOLDOUT CASES", font=font(20, True), fill="#41545b")
        labels = ["No report", "Neutral", "Approval-seeking", "+ Mitigation"]
        for i, (label, value) in enumerate(zip(labels, (2, 3, 4, 3))):
            yy = 268 + i * 58
            d.text((96, yy), label, font=font(22), fill="#202b31")
            d.rounded_rectangle((390, yy, 1050, yy + 30), radius=8, fill="#e9e3d8")
            d.rounded_rectangle((390, yy, 390 + value * 55, yy + 30), radius=8,
                                fill="#e46c42" if i == 2 else "#718b87")
            d.text((1070, yy - 2), f"{value}/12", font=font(22, True), fill="#202b31")
        d.text((96, 505), "PRIMARY: pressure vs neutral  +1 case  |  screen: +2 cases", font=font(20, True), fill="#ab4d31")
    elif "h16" in key or "duplicate" in key:
        d.text((100, 242), "DUPLICATE KEY", font=font(22, True), fill="#ab4d31")
        d.text((100, 286), "first record  →  1", font=font(32, True), fill="#202b31")
        d.text((100, 348), "last record   →  2", font=font(32, True), fill="#202b31")
        d.text((100, 436), "Required: 1     •     Code returned: 2", font=font(26, True), fill="#ab4d31")
    elif any(w in key for w in ("pipeline", "timeline", "pivot", "workflow")):
        labels = ["Canaries", "Route closed", "New preregistration", "Holdout", "Publication"]
        d.line((148, 338, 1135, 338), fill="#b1c0b7", width=6)
        for i, label in enumerate(labels):
            x = 148 + i * 247
            d.ellipse((x - 13, 325, x + 13, 351), fill="#e46c42" if i == 1 else "#718b87")
            for j, text in enumerate(wrap(d, label, font(19, True), 180)):
                d.text((x - 55, 372 + 25 * j), text, font=font(19, True), fill="#27363c")
        d.text((100, 458), "Separate routes  •  Frozen study  •  Publication-only repair", font=font(22), fill="#41545b")
    else:
        bullets = scene.get("bullets", [])
        if not bullets:
            bullets = [scene["visual"]]
        y = 244
        for bullet in bullets[:5]:
            for j, line in enumerate(wrap(d, str(bullet), font(27), 995)[:3]):
                d.text((120, y), ("•  " if j == 0 else "   ") + line, font=font(27), fill="#27363c")
                y += 39
            y += 11
            if y > 505:
                break
    d.text((69, 582), "CASEY  /  ENGINEER", font=font(17, True), fill="#52635f")
    d.text((935, 582), "MORGAN  /  FOUNDER", font=font(17, True), fill="#ab4d31")
    d.text((70, 687), f"COMPLETION REPORT GRADING                                      {index + 1:02d}", font=font(14, True), fill="#72817c")
    return image


def stamp(seconds, sep="."):
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d}{sep}{ms % 1000:03d}"


def ass_stamp(seconds):
    cs = round(seconds * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def make_timing(content, scenes, requests):
    segments, cues, chapters = [], [], []
    cursor = 0.0
    request_index = 0
    for scene in scenes:
        start = cursor
        for line in scene["lines"]:
            duration = requests[request_index]["duration"]
            end = cursor + duration
            segment = {"start_seconds": cursor, "end_seconds": end, "speaker": line["speaker"],
                       "text": line["text"], "scene_id": scene["id"]}
            segments.append(segment)
            words = line["text"].split()
            chunks = [words[i:i + 10] for i in range(0, len(words), 10)]
            offset = 0
            for chunk in chunks:
                a = cursor + duration * offset / len(words)
                offset += len(chunk)
                b = cursor + duration * offset / len(words)
                cues.append({**segment, "start_seconds": a, "end_seconds": b, "text": " ".join(chunk)})
            cursor = end
            request_index += 1
        if chapters and chapters[-1]["title"] == scene["chapter"]:
            chapters[-1]["end_seconds"] = cursor
        else:
            chapters.append({"id": scene["id"], "title": scene["chapter"], "start_seconds": start, "end_seconds": cursor})
    return segments, cues, chapters


def generate(content, prototype=False):
    scenes = content["scenes"]
    if prototype:
        scenes = [{"id": "prototype", "chapter": "Prototype", "title": "Two voices, one evidence trail",
                   "visual": "Rendering and audio verification", "lines": [
                       {"speaker": "casey", "text": "We should measure the evidence before we celebrate."},
                       {"speaker": "morgan", "text": "Can we at least celebrate measuring it?"}]}]
    requests = synthesize(content, scenes)
    segments, cues, chapters = make_timing(content, scenes, requests)
    for old in (TEMP / "video.mp4", TEMP / "audio.wav"):
        old.unlink(missing_ok=True)
    audio_list = "".join(f"file 'voice-{i:04d}.wav'\n" for i in range(len(requests)))
    write(TEMP / "audio.txt", audio_list)
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "audio.txt",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "pcm_s16le", "audio.wav"], cwd=TEMP)
    image_list = []
    for i, scene in enumerate(scenes):
        picture = card(scene, i)
        picture.save(TEMP / f"scene-{i:03d}.png")
        duration = sum(s["end_seconds"] - s["start_seconds"] for s in segments if s["scene_id"] == scene["id"])
        image_list.append(f"file 'scene-{i:03d}.png'\nduration {duration:.9f}\n")
    image_list.append(f"file 'scene-{len(scenes)-1:03d}.png'\n")
    write(TEMP / "images.txt", "".join(image_list))
    ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,27,&H00FFFFFF,&H000000FF,&H00161D20,&HBB10191C,0,0,0,0,100,100,0,0,3,2,0,2,90,90,58,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for cue in cues:
        safe = cue["text"].replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")
        ass += f"Dialogue: 0,{ass_stamp(cue['start_seconds'])},{ass_stamp(cue['end_seconds'])},Default,,0,0,0,,{safe}\n"
    write(TEMP / "captions.ass", ass)
    duration = segments[-1]["end_seconds"]
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "images.txt",
         "-i", "audio.wav", "-vf", "fps=24,subtitles=captions.ass,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "29", "-threads", "2",
         "-c:a", "aac", "-b:a", "96k", "-t", f"{duration:.6f}", "-movflags", "+faststart", "video.mp4"],
        cwd=TEMP, timeout=300)
    info = probe(TEMP / "video.mp4")
    assert {s["codec_type"] for s in info["streams"]} >= {"video", "audio"}
    if prototype:
        run(["ffmpeg", "-y", "-v", "error", "-ss", "1", "-i", "video.mp4", "-frames:v", "1", "prototype.jpg"], cwd=TEMP)
        print("Prototype:", json.dumps({"duration": info["format"]["duration"], "bytes": (TEMP / "video.mp4").stat().st_size}))
        return
    measured = float(info["format"]["duration"])
    if not 360 <= measured <= 480 or (TEMP / "video.mp4").stat().st_size >= 30_000_000:
        raise ValueError(f"Video outside duration or size budget: {measured}s, {(TEMP / 'video.mp4').stat().st_size} bytes")
    for entries in (segments, cues, chapters):
        entries[-1]["end_seconds"] = min(entries[-1]["end_seconds"], measured)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"], video["r_frame_rate"]) == (1280, 720, "24/1")
    (HERE / "explainer.mp4").write_bytes((TEMP / "video.mp4").read_bytes())
    card(scenes[0], 0).save(HERE / "poster.jpg", quality=88)
    vtt = "WEBVTT\n\n" + "\n".join(f"{stamp(c['start_seconds'])} --> {stamp(c['end_seconds'])}\n{content['voices'][c['speaker']]['label']}: {c['text']}\n" for c in cues)
    write(HERE / "captions.vtt", vtt)
    transcript = [{"speaker": s["speaker"], "text": s["text"]} for s in segments]
    data = {"content": content, "duration_seconds": measured, "chapters": chapters, "cues": cues,
            "segments": segments, "transcript": transcript}
    write(HERE / "media-data.js", "window.EXPLAINER_MEDIA = " + json.dumps(data, ensure_ascii=True, separators=(",", ":")) + ";\n")
    paragraphs = "\n".join(f"<p><strong>{html.escape(content['voices'][s['speaker']]['label'])}:</strong> {html.escape(s['text'])}</p>" for s in segments)
    write(HERE / "transcript.html", f"<!doctype html>\n<html lang=\"en\"><meta charset=\"utf-8\"><title>Transcript</title><body><main><h1>{html.escape(content['title'])} — transcript</h1>{paragraphs}</main></body></html>\n")
    paths = ["content.json", "render_explainer.py", "explainer.mp4", "captions.vtt", "poster.jpg", "media-data.js", "transcript.html", "../REPORT.md", "../INTERVIEW_GUIDE.md", "../../README.md"]
    manifest = {"files_sha256": {name: digest(HERE / name) for name in paths}, "duration_seconds": measured,
                "python_version": sys.version.split()[0], "ffmpeg_version": run(["ffmpeg", "-version"]).splitlines()[0]}
    write(HERE / "build-manifest.json", json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"duration_seconds": measured, "bytes": (HERE / "explainer.mp4").stat().st_size, "streams": info["streams"], "files_sha256": manifest["files_sha256"]}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prototype", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    TEMP.mkdir(parents=True, exist_ok=True)
    HERE.mkdir(parents=True, exist_ok=True)
    if args.prototype and not (HERE / "content.json").exists():
        content = {"voices": {"casey": {"sapi_name": "Microsoft Zira Desktop", "rate": -1},
                              "morgan": {"sapi_name": "Microsoft David Desktop", "rate": 0}}, "scenes": []}
    else:
        content = json.loads((HERE / "content.json").read_text(encoding="utf-8"))
        validate(content)
    if args.check:
        media = json.loads((HERE / "media-data.js").read_text(encoding="utf-8").removeprefix("window.EXPLAINER_MEDIA = ").strip().removesuffix(";"))
        assert media["content"] == content
        assert 360 <= media["duration_seconds"] <= 480
        assert all(0 <= c["start_seconds"] < c["end_seconds"] <= media["duration_seconds"] for c in media["cues"])
        assert all(a["end_seconds"] <= b["start_seconds"] + 0.000001 for a, b in zip(media["cues"], media["cues"][1:]))
        manifest = json.loads((HERE / "build-manifest.json").read_text(encoding="utf-8"))
        assert all(digest(HERE / name) == value for name, value in manifest["files_sha256"].items())
        print("Schema, cue timing, source identity, and manifest hashes pass.")
    else:
        generate(content, args.prototype)


if __name__ == "__main__":
    main()
