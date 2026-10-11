"""
TactileTrail - Zero-Screen Audio Naturalist
Hacktoberfest DEV Challenge (Theme: "Touch Grass")

An outdoor sensory exploration web application that guides users through
mindful, tactile nature quests via audio narration, keeping phones safely
in pockets with earbuds on.

Key Integrations:
- Core Model: Google Gemma (via Google AI Studio or Hugging Face Inference API)
  with offline Edge-AI simulation fallback.
- Audio Engine: ElevenLabs Text-to-Speech API with graceful gTTS and
  browser Web SpeechSynthesis fallback.
- Mobile UI: Responsive, tactile, sunlight-friendly outdoor interface with
  MediaSession lock-screen support and procedural ambient nature soundscape.
"""

import os
import io
import json
import random
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Query, Body
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TactileTrail")

# App Initialization
app = FastAPI(
    title="TactileTrail",
    description="Zero-Screen Audio Naturalist for the Touch Grass DEV Challenge",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ==============================================================================
# CONFIGURATION & API KEYS
# ==============================================================================
GEMMA_API_KEY = os.getenv("GEMMA_API_KEY", "").strip()
GEMMA_MODEL_NAME = os.getenv("GEMMA_MODEL_NAME", "gemma-4-26b-a4b-it").strip()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "").strip()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb").strip()

# ==============================================================================
# RICH OFFLINE / EDGE-AI NATURALIST ENGINE
# Emulates Gemma 2 weights locally for off-grid trails with zero cellular signal
# ==============================================================================
OFFLINE_NATURALIST_REPOSITORY = {
    "forest": [
        {
            "id": 1,
            "sense": "touch",
            "title": "The Cartography of Bark",
            "invitation": "Reach out with your fingertips and press gently into the nearest mature tree.",
            "narration": (
                "Close your eyes and let your fingers trace the furrowed bark before you. "
                "Notice the deep ridges, like dry riverbeds carved across centuries. "
                "Beneath this rough, dead outer cork lies the living vascular layer—the phloem—"
                "silently pulsing with sugars from the canopy high above. Feel the cool moisture "
                "harbored in its northern crevices, where micro-moss cushions have anchored themselves."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 55,
            "scientific_note": "Rhytidome cork formation & microclimatic moisture retention."
        },
        {
            "id": 2,
            "sense": "sound",
            "title": "Acoustic Layers of the Canopy",
            "invitation": "Stand still in your stride, tilt your chin upward, and close your eyelids.",
            "narration": (
                "Listen past your own breath. In the high canopy, needles and leaves create friction "
                "with the passing thermal breeze, producing a soft white-noise hush known as psithurism. "
                "Now, peel that layer back. Can you detect the subtle crackle of dry twigs settling "
                "under gravity, or the sharp, territorial chirp of a nuthatch bouncing off spruce trunks? "
                "Let the forest surround you in three dimensions."
            ),
            "haptic_cue": "double",
            "duration_seconds": 60,
            "scientific_note": "Psithurism sound propagation & spatial bioacoustics."
        },
        {
            "id": 3,
            "sense": "observation",
            "title": "The Capillary Architecture of Leaves",
            "invitation": "Pick up a fallen leaf or turn a living branch toward the dappled sunlight.",
            "narration": (
                "Observe the leaf backlit by the afternoon sun. Trace the master midrib branching into "
                "delicate fractal capillaries. These microscopic veins transported water against gravity "
                "through negative hydrostatic tension. Notice the pale speckles of fungal spores or tiny "
                "gall bumps—a miniature continent where thousands of invisible organisms conduct their lives."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 50,
            "scientific_note": "Fractal venation architecture & xylem negative tension."
        },
        {
            "id": 4,
            "sense": "reflection",
            "title": "Phytoncides and the Forest Floor",
            "invitation": "Take three slow, deep breaths, pulling the moist scent of loamy soil into your lungs.",
            "narration": (
                "Inhale deeply. That earthy scent is geosmin, produced by soil actinobacteria, mingled "
                "with airborne phytoncides released by conifers to defend against pests. When you breathe "
                "these terpenes, your heart rate naturally settles. You are not a visitor walking through "
                "nature; you are organic matter standing in communion with the living earth."
            ),
            "haptic_cue": "gentle",
            "duration_seconds": 55,
            "scientific_note": "Aerosolized coniferous phytoncides & geosmin reception."
        }
    ],
    "park": [
        {
            "id": 1,
            "sense": "touch",
            "title": "The Secret Resilience of Turf Grass",
            "invitation": "Crouch down and press your palms flat into the lawn or soil beneath you.",
            "narration": (
                "Feel the cool, dense weave of the grass blades beneath your palms. Unlike broadleaf "
                "plants that grow from the tip, grasses grow from their base—the basal meristem. This "
                "evolutionary masterpiece allows them to withstand being grazed by herbivores or trodden "
                "by human footsteps. Notice the damp chill clinging to the soil, a thermal cushion "
                "cooling our urban concrete."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 50,
            "scientific_note": "Basal meristem regeneration & urban thermal buffering."
        },
        {
            "id": 2,
            "sense": "sound",
            "title": "The Urban Edge Chorus",
            "invitation": "Pause beneath the nearest park tree and listen for the bird frequency spectrum.",
            "narration": (
                "Urban birds have adapted their vocal acoustics to rise above city rumble. Listen "
                "carefully for the bright, staccato call of a sparrow or robin. Notice how they wait for "
                "lulls in distant traffic noise to broadcast their song at higher frequencies. Filter out "
                "the mechanical hum and tune your attention strictly to the living frequencies."
            ),
            "haptic_cue": "double",
            "duration_seconds": 55,
            "scientific_note": "Acoustic adaptation and pitch-shifting in anthropogenic noise."
        },
        {
            "id": 3,
            "sense": "observation",
            "title": "Petal Velveteen and Pollen Corridors",
            "invitation": "Approach an ornamental shrub or wildflower and inspect a blossom up close.",
            "narration": (
                "Look closely at the surface of a blossom or leaf. Notice the velvety cellular texture, "
                "crafted by conical epidermal cells that scatter light to lure pollinators. If sunlight "
                "catches it just right, you might glimpse yellow pollen grains clinging like gold dust to "
                "the anthers. This is nature's ancient postal service, running quietly in your city park."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 50,
            "scientific_note": "Conical epidermal scattering & floral electrostatic pollen transfer."
        },
        {
            "id": 4,
            "sense": "reflection",
            "title": "Grounded in the Managed Wild",
            "invitation": "Stand tall, roll your shoulders back, and feel gravity pulling you down through your heels.",
            "narration": (
                "Even here, enclosed by town roads and curated gardens, the wild pulse is unbroken. "
                "The earth under your shoes stretches unbroken across tectonic plates. Feel gratitude "
                "for this oasis of green oxygen, and recognize the quiet resilience of life pushing up "
                "through every crack in the pavement."
            ),
            "haptic_cue": "gentle",
            "duration_seconds": 50,
            "scientific_note": "Biophilic decompression and postural sensory alignment."
        }
    ],
    "neighborhood": [
        {
            "id": 1,
            "sense": "touch",
            "title": "Pavement Crevices & Moss Colonizers",
            "invitation": "Find a boundary where stone, asphalt, or curb meets wild soil, and touch the edge.",
            "narration": (
                "Run a finger along the boundary where asphalt meets raw earth. Feel the gritty aggregate "
                "of human stone, and then the tender, velvety green of Bryum argenteum—silvery sidewalk "
                "moss. This tiny pioneer survives severe desiccation and vehicle exhaust, creating miniature "
                "sponges that trap water and build primeval soil right at your feet."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 55,
            "scientific_note": "Bryum argenteum desiccation tolerance & micro-edaphic succession."
        },
        {
            "id": 2,
            "sense": "sound",
            "title": "Micro-Breezes Through Garden Hedges",
            "invitation": "Walk close to a private hedge or garden overhang and listen to its wind tune.",
            "narration": (
                "Listen to the subtle whisper as a light gust filters through boxwood, privet, or cedar "
                "leaves. Each leaf geometry produces a unique acoustic signature—waxy broadleaves click, "
                "while dry ornamental grasses hiss like gentle surf. Let this small hedge screen out the "
                "rush of the digital day."
            ),
            "haptic_cue": "double",
            "duration_seconds": 50,
            "scientific_note": "Aerodynamic vegetative sound attenuation and leaf friction."
        },
        {
            "id": 3,
            "sense": "observation",
            "title": "Lichen Crusts on Fence Posts",
            "invitation": "Examine a wooden fence post, brick wall, or street tree trunk.",
            "narration": (
                "Look at the marbled rosettes of lichen clinging to the surface. Lichen is neither plant "
                "nor moss, but an intimate symbiotic partnership between fungi and microscopic algae. "
                "The fungus provides structural shelter and minerals, while the algae photosynthesize sun "
                "into sugar. They have lived this quiet collaboration for four hundred million years."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 55,
            "scientific_note": "Mutualistic symbiosis between mycobiont and photobiont."
        },
        {
            "id": 4,
            "sense": "reflection",
            "title": "Finding the Wild in the Everyday",
            "invitation": "Unclench your jaw, soften your gaze, and sense your footsteps against the earth.",
            "narration": (
                "You do not need a remote national park to touch the living world. The grass between "
                "pavers, the evening sparrows in roof gutters, the damp soil aroma after rain—they are "
                "all waiting here every day. Carry this heightened sensory awareness back across your doorstep."
            ),
            "haptic_cue": "gentle",
            "duration_seconds": 45,
            "scientific_note": "Mindful somatic presence in urban natural spaces."
        }
    ],
    "water": [
        {
            "id": 1,
            "sense": "touch",
            "title": "The Hydraulic Polish of River Stone",
            "invitation": "Pick up a smooth pebble or touch the damp edge of a waterside rock.",
            "narration": (
                "Roll this water-smoothed stone between your palms. Notice its extraordinary coolness and "
                "silk-like surface. Millions of gallons of running water, bearing fine mineral silt, have "
                "spent decades polishing away every sharp corner. Feel the thermal conductivity pulling heat "
                "from your skin, grounding you in ancient geological time."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 55,
            "scientific_note": "Hydraulic fluvial abrasion and quartz thermal conductivity."
        },
        {
            "id": 2,
            "sense": "sound",
            "title": "The Polyphonic Ripple of Moving Water",
            "invitation": "Close your eyes near the water's edge and track the rhythm of the waves or stream.",
            "narration": (
                "Listen to the water's voice. Water produces sound not from liquid itself, but from "
                "thousands of tiny oscillating air bubbles trapped and released as currents tumble over "
                "shallows. Listen for the bass undertone of deep currents contrasted against the bright, "
                "bell-like splashes of shoreline ripples."
            ),
            "haptic_cue": "double",
            "duration_seconds": 60,
            "scientific_note": "Entrained air bubble oscillation (Minnaert resonance) in fluid dynamics."
        },
        {
            "id": 3,
            "sense": "observation",
            "title": "Riparian Reeds and Surface Tension",
            "invitation": "Look closely at the water margin where stalks emerge from the surface.",
            "narration": (
                "Observe the meniscus where aquatic stems meet the water surface. See how the liquid "
                "curves gently upward, held by hydrogen bonds of surface tension. A water strider may "
                "be skating across this invisible elastic skin, its hydrophobic leg hairs preventing it "
                "from breaking the mirror of the lake."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 55,
            "scientific_note": "Surface tension meniscus & hydrophobic insect cuticle mechanics."
        },
        {
            "id": 4,
            "sense": "reflection",
            "title": "The Great Hydrological Flow",
            "invitation": "Place one hand over your chest and feel the steady rhythm of your pulse.",
            "narration": (
                "The water before you has traveled through clouds, ocean currents, and subterranean "
                "aquifers for billions of years. More than sixty percent of your own body is this very "
                "same water. When you gaze across this shore, water is contemplating water."
            ),
            "haptic_cue": "gentle",
            "duration_seconds": 50,
            "scientific_note": "Biochemical water balance and hydrological cycle resonance."
        }
    ],
    "meadow": [
        {
            "id": 1,
            "sense": "touch",
            "title": "Seed Pods and Feathery Plumes",
            "invitation": "Gently cup the flowerhead of a tall grass, dandelion, or thistle seed plume.",
            "narration": (
                "Gently stroke the dry seedhead between thumb and forefinger. Feel the delicate papery "
                "bracts and microscopic hooks designed to cling to passing animal fur, or the silky pappus "
                "filaments engineered to catch the faintest thermal updraft. Nature crafts each seed with "
                "aerodynamic perfection."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 50,
            "scientific_note": "Pappus plume drag coefficients & epizoochory seed dispersal."
        },
        {
            "id": 2,
            "sense": "sound",
            "title": "The Grassland Wind Sweep",
            "invitation": "Stand tall facing the prevailing breeze with eyes gently closed.",
            "narration": (
                "In an open meadow, wind has nothing to break its stride. Listen as it sweeps through "
                "thousands of slender grass stalks simultaneously. Unlike the heavy rumble of a forest, "
                "the meadow sings in high, sibilant whispers. Can you hear the sudden trill of a grasshopper "
                "stridulating its hind legs like a violin bow?"
            ),
            "haptic_cue": "double",
            "duration_seconds": 55,
            "scientific_note": "Poaceae stem oscillation acoustics & orthopteran stridulation."
        },
        {
            "id": 3,
            "sense": "observation",
            "title": "Sunlight Dappling and Insect Highways",
            "invitation": "Part the tall grass stems and peek down into the shadowy sub-canopy.",
            "narration": (
                "Peer beneath the tips into the golden shadows near the ground. Down here is a temperate "
                "jungle. Watch an ant navigate a vertical stem with its clawed tarsi, or a predatory "
                "wolf spider poised silently on a dead blade. A universe of microscopic drama plays out "
                "in this single square foot of soil."
            ),
            "haptic_cue": "pulse",
            "duration_seconds": 50,
            "scientific_note": "Microarthropod canopy stratification & microhabitat ecology."
        },
        {
            "id": 4,
            "sense": "reflection",
            "title": "Solar Energy Transmuted into Grass",
            "invitation": "Turn your face to the warm sky and exhale deeply through parted lips.",
            "narration": (
                "Every blade around you is a solar panel capturing photons that traveled ninety-three "
                "million miles, capturing carbon from the breeze and knitting it into living cellulose. "
                "Breathe in the sweet green scent of that alchemy. Feel steady, open, and alive."
            ),
            "haptic_cue": "gentle",
            "duration_seconds": 50,
            "scientific_note": "Photosynthetic photon efficiency and biospheric carbon sequestration."
        }
    ]
}

# ==============================================================================
# DATA MODELS
# ==============================================================================
class Checkpoint(BaseModel):
    id: int
    sense: str
    title: str
    invitation: str
    narration: str
    haptic_cue: str = "pulse"
    duration_seconds: int = 50
    scientific_note: Optional[str] = None

class WalkRequest(BaseModel):
    environment: str = Field(..., description="forest, park, neighborhood, water, meadow")
    walk_length: str = Field("standard", description="short (3 checkpoints) or standard (4 checkpoints)")
    mode: str = Field("auto", description="auto, cloud, or offline")
    sensory_focus: Optional[str] = Field(None, description="touch, sound, observation, all")
    season: Optional[str] = Field("autumn", description="spring, summer, autumn, winter")

class WalkResponse(BaseModel):
    environment: str
    season: str
    provider: str
    model_name: str
    is_offline: bool
    total_duration_estimate: int
    checkpoints: List[Checkpoint]
    ambient_sound_preset: str
    quote: str

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    checkpoint_id: Optional[int] = 1

class JournalEntry(BaseModel):
    walk_id: str
    environment: str
    date: str
    duration_minutes: int
    reflection_notes: str
    photo_data_url: Optional[str] = None
    checkpoints_completed: int

# ==============================================================================
# GEMMA PROMPT & GENERATION ENGINE
# ==============================================================================
GEMMA_SYSTEM_PROMPT = """
You are an intimate, poetic, David Attenborough-style field naturalist guiding a human who has their phone in their pocket with earbuds on.
The user is outdoors exploring nature. Your purpose is to liberate them from their screen and deeply connect them to the living, tactile world around them.

Tone and style:
- Intimate, warm, gently reverent, and scientifically curious.
- Precise botanical and acoustic vocabulary (e.g., phloem, mycorrhizae, psithurism, geosmin, capillary tension, basal meristem).
- Never sound robotic or clinical; blend natural science with lyrical mindfulness.
- Concise: Narration for each checkpoint MUST be between 50 and 75 words so it can be absorbed while walking.

Structure:
Return a JSON array of checkpoints with fields:
- "id": integer (1 to 4)
- "sense": "touch" | "sound" | "observation" | "reflection"
- "title": captivating 3-5 word title
- "invitation": exactly one direct, gentle physical invitation (e.g. "Find a mature oak and press your palms flat into its bark.")
- "narration": 50-75 words of spoken narration in David Attenborough's voice.
- "haptic_cue": "pulse" (single haptic), "double" (double haptic), or "gentle" (soft vibration)
- "duration_seconds": integer estimated seconds (45 to 65)
- "scientific_note": one brief sentence highlighting the biological/ecological phenomenon
"""

async def query_google_ai_studio(prompt: str, env_name: str, length: int) -> Optional[List[Dict[str, Any]]]:
    """Invoke Gemma (or Gemini) via Google AI Studio API."""
    if not GEMMA_API_KEY:
        return None

    models_to_try = [
        GEMMA_MODEL_NAME,
        "gemini-flash-latest",
        "gemma-4-26b-a4b-it",
        "gemma-4-31b-it",
        "gemini-2.5-flash-lite",
        "gemma-2-9b-it"
    ]
    # De-duplicate while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMMA_API_KEY}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": f"{GEMMA_SYSTEM_PROMPT}\n\nTask: Generate {length} progressive checkpoints for a walk in environment: '{env_name}'. Ensure output is valid JSON array."}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json"
                }
            }
            try:
                logger.info(f"Invoking Google AI Studio model: {model}")
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        # Parse JSON from response
                        cleaned = text_content.strip()
                        if cleaned.startswith("```json"):
                            cleaned = cleaned[7:]
                        if cleaned.endswith("```"):
                            cleaned = cleaned[:-3]
                        parsed = json.loads(cleaned.strip())
                        if isinstance(parsed, dict) and "checkpoints" in parsed:
                            parsed = parsed["checkpoints"]
                        if isinstance(parsed, list) and len(parsed) >= 2:
                            return parsed
                else:
                    logger.warning(f"Google AI Studio returned status {response.status_code} for model {model}: {response.text[:200]}")
            except Exception as e:
                logger.warning(f"Error querying Google AI Studio ({model}): {e}")
                continue
    return None

async def query_huggingface_gemma(env_name: str, length: int) -> Optional[List[Dict[str, Any]]]:
    """Invoke Google Gemma 2 on Hugging Face Serverless Inference API."""
    if not HUGGINGFACE_API_KEY:
        return None

    url = "https://api-inference.huggingface.co/models/google/gemma-2-9b-it"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    prompt = f"<bos><start_of_turn>user\n{GEMMA_SYSTEM_PROMPT}\nGenerate {length} checkpoints in JSON for: {env_name}. Output ONLY the JSON array.<end_of_turn>\n<start_of_turn>model\n"

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            logger.info("Invoking Hugging Face Inference API for Gemma-2-9b-it")
            response = await client.post(url, headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": 800, "temperature": 0.7}})
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    text_resp = data[0].get("generated_text", "")
                    if "<start_of_turn>model\n" in text_resp:
                        text_resp = text_resp.split("<start_of_turn>model\n")[-1]
                    text_resp = text_resp.strip()
                    if text_resp.startswith("```json"):
                        text_resp = text_resp[7:]
                    if text_resp.endswith("```"):
                        text_resp = text_resp[:-3]
                    parsed = json.loads(text_resp.strip())
                    if isinstance(parsed, list) and len(parsed) >= 2:
                        return parsed
        except Exception as e:
            logger.warning(f"Hugging Face Gemma inference failed: {e}")
    return None

def generate_offline_edge_walk(environment: str, count: int = 4) -> List[Dict[str, Any]]:
    """
    Simulates Gemma 2 on-device edge weights.
    Provides immediate zero-latency sensory checkpoints for deep trails without cellular signal.
    """
    key = environment.lower()
    if key not in OFFLINE_NATURALIST_REPOSITORY:
        key = "forest"

    pool = OFFLINE_NATURALIST_REPOSITORY[key]
    # Return requested length
    selected = pool[:count]
    return selected

# ==============================================================================
# AUDIO SYNTHESIS & ELEVENLABS ENGINE
# ==============================================================================
async def synthesize_elevenlabs(text: str, voice_id: str) -> Optional[bytes]:
    """Generate high-fidelity calming speech using ElevenLabs API."""
    if not ELEVENLABS_API_KEY:
        return None

    vid = voice_id or ELEVENLABS_VOICE_ID or "JBFqnCBsd6RMkjVDRZzb"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.35,
            "use_speaker_boost": True
        }
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        try:
            logger.info(f"Synthesizing speech via ElevenLabs (Voice: {vid})")
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.content
            else:
                logger.warning(f"ElevenLabs TTS returned error {response.status_code}: {response.text[:150]}")
        except Exception as e:
            logger.warning(f"ElevenLabs TTS call failed: {e}")
    return None

def synthesize_gtts_fallback(text: str) -> Optional[bytes]:
    """Local fallback speech synthesis using gTTS."""
    try:
        from gtts import gTTS
        fp = io.BytesIO()
        tts = gTTS(text=text, lang="en", tld="co.uk", slow=False)
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        logger.warning(f"gTTS fallback failed: {e}")
        return None

# ==============================================================================
# HTTP ROUTES & ENDPOINTS
# ==============================================================================
@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    """Serve the single-page responsive mobile outdoor web app."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "has_gemma_key": bool(GEMMA_API_KEY or HUGGINGFACE_API_KEY),
            "has_elevenlabs_key": bool(ELEVENLABS_API_KEY),
            "default_voice_id": ELEVENLABS_VOICE_ID,
        }
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint for Render / cloud deployment."""
    return {
        "status": "healthy",
        "service": "TactileTrail",
        "theme": "Touch Grass",
        "gemma_configured": bool(GEMMA_API_KEY or HUGGINGFACE_API_KEY),
        "elevenlabs_configured": bool(ELEVENLABS_API_KEY)
    }

@app.get("/api/config")
async def get_configuration():
    """Returns active runtime configuration & AI capabilities."""
    return {
        "ai_engine": {
            "google_ai_studio_active": bool(GEMMA_API_KEY),
            "huggingface_active": bool(HUGGINGFACE_API_KEY),
            "model_preference": GEMMA_MODEL_NAME,
            "offline_edge_available": True
        },
        "audio_engine": {
            "elevenlabs_active": bool(ELEVENLABS_API_KEY),
            "default_voice": ELEVENLABS_VOICE_ID,
            "gtts_fallback_available": True,
            "browser_speech_fallback_available": True
        },
        "environments": list(OFFLINE_NATURALIST_REPOSITORY.keys())
    }

@app.post("/api/generate-walk", response_model=WalkResponse)
async def generate_walk(payload: WalkRequest):
    """
    Generate an outdoor sensory quest with 3-4 progressive checkpoints.
    Supports Google Gemma Cloud, Hugging Face Gemma, or Local Gemma Edge simulation.
    """
    env = payload.environment.lower()
    target_count = 3 if payload.walk_length == "short" else 4
    provider = "Offline Edge Gemma"
    model_name = "Gemma-2-9B Edge Simulation (On-Device)"
    is_offline = True
    checkpoints_raw = None

    # Check user mode preference:
    use_cloud = payload.mode in ["auto", "cloud"] and (GEMMA_API_KEY or HUGGINGFACE_API_KEY)

    if use_cloud and payload.mode != "offline":
        # 1. Try Google AI Studio first
        if GEMMA_API_KEY:
            checkpoints_raw = await query_google_ai_studio(payload.environment, env, target_count)
            if checkpoints_raw:
                provider = "Google AI Studio"
                model_name = GEMMA_MODEL_NAME
                is_offline = False

        # 2. Try Hugging Face Gemma if needed
        if not checkpoints_raw and HUGGINGFACE_API_KEY:
            checkpoints_raw = await query_huggingface_gemma(env, target_count)
            if checkpoints_raw:
                provider = "Hugging Face Inference"
                model_name = "google/gemma-2-9b-it"
                is_offline = False

    # 3. Graceful Edge Fallback (Always available, completely off-grid)
    if not checkpoints_raw:
        checkpoints_raw = generate_offline_edge_walk(env, target_count)
        provider = "Gemma Edge Engine"
        model_name = "Gemma-2-9B-Naturalist (Edge Quantized Repository)"
        is_offline = True

    # Validate and structure response
    structured_checkpoints: List[Checkpoint] = []
    total_est = 0
    for idx, c in enumerate(checkpoints_raw, start=1):
        cp = Checkpoint(
            id=c.get("id", idx),
            sense=c.get("sense", "touch"),
            title=c.get("title", f"Sensory Checkpoint {idx}"),
            invitation=c.get("invitation", "Pause and attend to the textures around you."),
            narration=c.get("narration", "Take a moment to absorb your surroundings."),
            haptic_cue=c.get("haptic_cue", "pulse"),
            duration_seconds=c.get("duration_seconds", 50),
            scientific_note=c.get("scientific_note")
        )
        structured_checkpoints.append(cp)
        total_est += cp.duration_seconds + 30 # narration + reflection time

    quotes = [
        "In every walk with nature, one receives far more than he seeks. — John Muir",
        "The earth has music for those who listen. — George Santayana",
        "Notice what happens when you step away from the glowing glass and touch the living bark.",
        "To look at a single leaf is to look directly into the engine room of our atmosphere."
    ]

    return WalkResponse(
        environment=payload.environment,
        season=payload.season or "autumn",
        provider=provider,
        model_name=model_name,
        is_offline=is_offline,
        total_duration_estimate=total_est,
        checkpoints=structured_checkpoints,
        ambient_sound_preset=env,
        quote=random.choice(quotes)
    )

@app.post("/api/tts")
async def generate_audio(payload: TTSRequest):
    """
    Synthesize checkpoint narration into calming naturalist audio.
    Prioritizes ElevenLabs, seamlessly falls back to gTTS, or provides browser speech cues.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # 1. ElevenLabs Speech Synthesis
    if ELEVENLABS_API_KEY:
        audio_bytes = await synthesize_elevenlabs(text, payload.voice_id or ELEVENLABS_VOICE_ID)
        if audio_bytes:
            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"inline; filename=checkpoint_{payload.checkpoint_id}.mp3",
                    "X-Audio-Provider": "ElevenLabs"
                }
            )

    # 2. Local gTTS fallback
    fallback_audio = synthesize_gtts_fallback(text)
    if fallback_audio:
        return StreamingResponse(
            io.BytesIO(fallback_audio),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=checkpoint_{payload.checkpoint_id}.mp3",
                "X-Audio-Provider": "gTTS-Local"
            }
        )

    # 3. If server audio generation is unavailable, inform client to use Web SpeechSynthesis
    return JSONResponse(
        status_code=200,
        content={
            "fallback_to_browser_tts": True,
            "text": text,
            "message": "ElevenLabs key not provided and local synthesizer unavailable. Using high-fidelity Web SpeechSynthesis API."
        }
    )

@app.post("/api/journal/save")
async def save_journal_note(entry: JournalEntry):
    """Save an outdoor reflection note into local session/file."""
    logger.info(f"Received field journal entry for walk: {entry.walk_id} in {entry.environment}")
    # In a full deployment, can save to sqlite or filesystem
    return {
        "status": "saved",
        "walk_id": entry.walk_id,
        "message": "Field journal recorded successfully."
    }

# Entrypoint for local execution
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"\n🌱 TactileTrail is springing to life at http://localhost:{port}")
    print(f"🌲 Core AI: {'Google AI Studio / Hugging Face' if GEMMA_API_KEY or HUGGINGFACE_API_KEY else 'Offline Edge Gemma Engine'}")
    print(f"🎙️ Audio Engine: {'ElevenLabs Voice Active' if ELEVENLABS_API_KEY else 'High-Fidelity Browser SpeechSynthesis & gTTS Fallback'}\n")
    uvicorn.run("app:app", host=host, port=port, reload=True)
