"""Central settings. Everything can be overridden with GitHub Actions *Variables* (not secrets)."""
import os


def env(name, default=""):
    """os.environ.get, but an EMPTY value (what GitHub passes for an unset variable) also falls back to the default."""
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else default


# ---------------------------------------------------------------- secrets (GitHub repo secrets)
GEMINI_API_KEY = env("GEMINI_API_KEY")
CF_ACCOUNT_ID = env("CF_ACCOUNT_ID")          # Cloudflare Workers AI -> FLUX.1 schnell images (free)
CF_API_TOKEN = env("CF_API_TOKEN")
YOUTUBE_CLIENT_ID = env("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = env("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = env("YOUTUBE_REFRESH_TOKEN")

# ---------------------------------------------------------------- files
EPISODES_FILE = "ramayana_episodes.json"
STATE_FILE = "episode_state.json"
LOG_FILE = "upload_log.json"
OUT_DIR = "out"
PORTRAIT = os.path.join("assets", "shree-ram.png")   # used for the closing card + emergency fallback
MUSIC_DIR = os.path.join("assets", "music")          # optional: drop one licensed .mp3 here to replace the built-in drone

# ---------------------------------------------------------------- Gemini
GEMINI_MODELS = [m.strip() for m in env(
    "GEMINI_MODELS", "gemini-3.6-flash,gemini-3.5-flash,gemini-2.5-flash").split(",") if m.strip()]

# ---------------------------------------------------------------- video
WIDTH, HEIGHT, FPS = 1080, 1920, 30
NUM_SCENES = int(env("NUM_SCENES", "9"))              # 8 picture scenes + 1 closing card  (~40-55 s)
SCENE_PAD = 0.12                                       # tiny pause after each scene -> snappy cuts
MAX_EPISODES = int(env("MAX_EPISODES", "110"))         # after this the series restarts from episode 1
FOREGROUND_H = 1210                                    # height of the picture inside the 9:16 frame
FOREGROUND_TOP = 235                                   # y position of the picture
CAPTION_FONT = env("CAPTION_FONT", "Noto Sans Devanagari")
MUSIC_VOLUME = float(env("MUSIC_VOLUME", "0.11"))

# ---------------------------------------------------------------- upload
PRIVACY = env("UPLOAD_PRIVACY", "public")
MADE_FOR_KIDS = env("MADE_FOR_KIDS", "false").lower() == "true"
CATEGORY_ID = "24"                                     # Entertainment
CHANNEL_HASHTAGS = "#रामायण #Ramayana #JaiShreeRam #श्रीराम #मराठी #Shorts"

FIRST_COMMENT = env("FIRST_COMMENT", "true").lower() == "true"   # channel posts the episode question as the first comment
DRY_RUN = env("DRY_RUN", "false").lower() == "true"    # build the video, do NOT upload, do NOT advance the episode
EPISODE_OVERRIDE = env("EPISODE_OVERRIDE")             # build one specific episode (never changes the saved state)
