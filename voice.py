"""edge-tts narration, one voice profile per speaker, silence trimmed so cuts are tight."""
import asyncio
import os
import subprocess
import time

import characters as cast
import config


def _tts(text, path, voice, rate, pitch):
    import edge_tts

    async def run():
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(path)
    asyncio.run(run())


def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", path])
    return float(out.strip())


def _trim(src, dst, semitones=0.0):
    """Remove leading/trailing silence (edge-tts adds ~0.3 s of air at both ends)."""
    af = ("silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.09,areverse,"
          "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.15,areverse")
    if config.VOICE_PITCH_SHIFT and abs(semitones) > 0.01:
        f = 2 ** (semitones / 12.0)           # >1 = higher/younger/smaller voice, <1 = lower/older/bigger voice
        af += f",asetrate={44100 * f:.1f},aresample=44100,atempo={1 / f:.6f}"
    p = subprocess.run(["ffmpeg", "-y", "-i", src, "-af", af, "-ar", "44100", "-ac", "2", dst],
                       capture_output=True, text=True)
    if p.returncode != 0 or not os.path.exists(dst) or os.path.getsize(dst) < 1000:
        raise RuntimeError("audio trim failed:\n" + p.stderr[-600:])


def synth(text, out_wav, speaker, retries=4):
    """Returns (duration_seconds, voice_profile_name)."""
    profile, (voice, rate, pitch, _color, semitones) = cast.voice_profile(speaker)
    raw = out_wav.replace(".wav", ".raw.mp3")
    last = None
    for attempt in range(1, retries + 1):
        try:
            # last attempt: plain voice with no pitch/rate tweaks, in case the service rejects them
            r, p = (rate, pitch) if attempt < retries else ("+0%", "+0Hz")
            _tts(text, raw, voice, r, p)
            if not os.path.exists(raw) or os.path.getsize(raw) < 1000:
                raise RuntimeError("voice file is empty")
            _trim(raw, out_wav, semitones)
            d = duration(out_wav)
            if d < 0.6:
                raise RuntimeError(f"voice too short ({d:.2f}s)")
            os.remove(raw)
            return d, profile
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"   voice attempt {attempt}/{retries} failed: {str(e)[:200]}")
            time.sleep(4 * attempt)
    raise RuntimeError(f"Voice generation failed after {retries} tries: {last}")
