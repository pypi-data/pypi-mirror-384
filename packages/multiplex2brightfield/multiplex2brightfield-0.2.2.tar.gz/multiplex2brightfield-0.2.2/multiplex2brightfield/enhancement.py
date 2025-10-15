# enhancement.py — NAFNet denoiser inference (TF/Keras 2.x), reload-safe + mixed-precision safe
import os
os.environ.setdefault("TF_GPU_ALLOCATOR", "cuda_malloc_async")
import gc
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.models import load_model

import re
import shutil
from urllib.parse import urlparse

# optional deps for nicer downloads; gracefully degrade if missing
try:
    import requests
except Exception:
    requests = None

try:
    from tqdm import tqdm
except Exception:
    tqdm = None
    
# Default model URL (used if you pass "model.h5" and it isn't present)
DEFAULT_MODEL_URL = "https://github.com/TristanWhitmarsh/multiplex2brightfield/releases/download/v0.2.1/denoise.h5"

# -------- optional cleanup hook (won't error if utils isn't packaged) --------
try:
    from .utils import maybe_cleanup
except Exception:
    def maybe_cleanup():
        try:
            tf.keras.backend.clear_session()
        except Exception:
            pass

# -------- polite GPU memory handling (no-ops on CPU) -------------------------
for g in tf.config.list_physical_devices("GPU"):
    try:
        tf.config.experimental.set_memory_growth(g, True)
    except Exception:
        pass
    
    
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)

def _is_url(s: str) -> bool:
    return bool(_URL_RE.match(str(s)))

def _download_with_progress(url: str, dst_path: str):
    """
    Stream-download to dst_path. Uses requests+tqdm when available,
    otherwise falls back to urllib (no progress bar). Writes atomically.
    """
    dst_dir = os.path.dirname(dst_path) or "."
    os.makedirs(dst_dir, exist_ok=True)
    tmp_path = dst_path + ".partial"

    def _finalize():
        # move into place atomically
        os.replace(tmp_path, dst_path)
        # basic sanity check
        if not os.path.exists(dst_path) or os.path.getsize(dst_path) == 0:
            raise IOError(f"Downloaded file is empty: {dst_path}")

    if requests is None:
        import urllib.request
        with urllib.request.urlopen(url) as r, open(tmp_path, "wb") as f:
            shutil.copyfileobj(r, f)
        _finalize()
        return

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        bar = tqdm(total=total, unit="B", unit_scale=True, unit_divisor=1024,
                   desc=os.path.basename(dst_path)) if tqdm else None
        with open(tmp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if not chunk:
                    continue
                f.write(chunk)
                if bar:
                    bar.update(len(chunk))
        if bar:
            bar.close()
    _finalize()



# =========================== Custom layers ===================================
# No keras_serializable decorators (safe to reload). We pass via custom_objects.

class SimpleGate(layers.Layer):
    def call(self, x):
        x1, x2 = tf.split(x, 2, axis=-1)
        return x1 * x2

class SCA(layers.Layer):
    def __init__(self, channels, **kwargs):
        super().__init__(**kwargs)
        self.channels = int(channels)
        self.gap  = layers.GlobalAveragePooling2D(keepdims=True)
        self.conv = layers.Conv2D(self.channels, 1, padding="same", use_bias=True)
    def call(self, x):
        w = self.gap(x)
        w = self.conv(w)
        return x * w

class NAFBlock(layers.Layer):
    """
    Matches notebook signature: NAFBlock(channels, expansion=2, drop_rate=0.0)
    Mixed-precision safe: explicitly cast residual operands to x.dtype.
    """
    def __init__(self, channels, expansion=2, drop_rate=0.0, **kwargs):
        super().__init__(**kwargs)
        self.channels  = int(channels)
        self.expansion = int(expansion)
        self.drop_rate = float(drop_rate)
        hidden = self.channels * self.expansion

        # Branch 1
        self.norm1 = layers.LayerNormalization(axis=-1, epsilon=1e-6)
        self.pw1   = layers.Conv2D(hidden * 2, 1, padding="same", use_bias=True)
        self.dw    = layers.DepthwiseConv2D(3, padding="same", use_bias=True)
        self.sg    = SimpleGate()
        self.sca   = SCA(hidden)
        self.pw2   = layers.Conv2D(self.channels, 1, padding="same", use_bias=True)
        self.do1   = (layers.SpatialDropout2D(self.drop_rate)
                      if self.drop_rate > 0.0 else layers.Activation("linear"))

        # Branch 2 (FFN-like)
        self.norm2 = layers.LayerNormalization(axis=-1, epsilon=1e-6)
        self.pw3   = layers.Conv2D(hidden * 2, 1, padding="same", use_bias=True)
        self.sg2   = SimpleGate()
        self.pw4   = layers.Conv2D(self.channels, 1, padding="same", use_bias=True)
        self.do2   = (layers.SpatialDropout2D(self.drop_rate)
                      if self.drop_rate > 0.0 else layers.Activation("linear"))

    def build(self, input_shape):
        c = int(input_shape[-1])
        # Keep variables in fp32; we’ll cast to x.dtype inside call().
        self.beta  = self.add_weight("beta",  shape=(1,1,1,c), initializer="zeros", trainable=True, dtype=tf.float32)
        self.gamma = self.add_weight("gamma", shape=(1,1,1,c), initializer="zeros", trainable=True, dtype=tf.float32)
        super().build(input_shape)

    def call(self, x, training=False):
        # -------- Branch 1 --------
        y = self.norm1(x)
        y = self.pw1(y)
        y = self.dw(y)
        y = self.sg(y)
        y = self.sca(y)
        y = self.pw2(y)
        y = self.do1(y, training=training)

        # Ensure SAME dtype for residual
        target_dtype = x.dtype
        y     = tf.cast(y,     target_dtype)
        beta  = tf.cast(self.beta,  target_dtype)
        x     = tf.cast(x,     target_dtype) + y * beta

        # -------- Branch 2 --------
        z = self.norm2(x)
        z = self.pw3(z)
        z = self.sg2(z)
        z = self.pw4(z)
        z = self.do2(z, training=training)

        z     = tf.cast(z,     target_dtype)
        gamma = tf.cast(self.gamma, target_dtype)
        x     = x + z * gamma
        return x

class Downsample(layers.Layer):
    def __init__(self, in_ch, out_ch, **kwargs):
        super().__init__(**kwargs)
        self.in_ch  = int(in_ch)
        self.out_ch = int(out_ch)
        self.conv = layers.Conv2D(self.out_ch, 2, strides=2, padding="valid", use_bias=True)
    def call(self, x):
        return self.conv(x)

class Upsample(layers.Layer):
    def __init__(self, in_ch, out_ch, **kwargs):
        super().__init__(**kwargs)
        self.in_ch  = int(in_ch)
        self.out_ch = int(out_ch)
        self.up   = layers.UpSampling2D((2,2), interpolation="nearest")
        self.conv = layers.Conv2D(self.out_ch, 3, padding="same", use_bias=True)
    def call(self, x):
        return self.conv(self.up(x))

# Map possible names stored in .h5 (plain and namespaced)
_CUSTOM_OBJECTS = {
    "SimpleGate": SimpleGate,
    "SCA": SCA,
    "NAFBlock": NAFBlock,
    "Downsample": Downsample,
    "Upsample": Upsample,
    "NAFNet>SimpleGate": SimpleGate,
    "NAFNet>SCA": SCA,
    "NAFNet>NAFBlock": NAFBlock,
    "NAFNet>Downsample": Downsample,
    "NAFNet>Upsample": Upsample,
}

# =========================== Model loading ===================================
_ai_model = None

def get_ai_model(model_file):
    """
    Load model once and cache it.

    Args:
        model_file (str): Local path or URL. If local path is missing, we try:
            1) download from the URL if model_file is a URL, else
            2) download from DEFAULT_MODEL_URL to a writable location.
    """
    global _ai_model
    if _ai_model is not None:
        return _ai_model

    # Resolve a base directory we can write to
    try:
        here = os.path.dirname(__file__)
    except NameError:
        here = ""
    here = here or os.getcwd()

    local_path = model_file

    # If not absolute, prefer package dir if file exists there; else leave as given (CWD)
    if not os.path.isabs(local_path):
        candidate = os.path.join(here, local_path)
        local_path = candidate if os.path.exists(candidate) else local_path

    # If missing, figure out where to download and ensure the target dir is writable
    if not os.path.exists(local_path):
        # Decide target filename
        if _is_url(model_file):
            filename = os.path.basename(urlparse(model_file).path) or "model.h5"
            # Prefer package dir; if not writable, fallback to CWD
            target_dir = here if os.access(here, os.W_OK) else os.getcwd()
            local_path = os.path.join(target_dir, filename)
            if not os.path.exists(local_path):
                print(f"Downloading model from URL: {model_file}")
                _download_with_progress(model_file, local_path)
        else:
            if not DEFAULT_MODEL_URL:
                raise FileNotFoundError(
                    f"Model file '{model_file}' not found and no DEFAULT_MODEL_URL set."
                )
            filename = os.path.basename(local_path) or "model.h5"
            target_dir = here if os.access(here, os.W_OK) else os.getcwd()
            local_path = os.path.join(target_dir, filename)
            if not os.path.exists(local_path):
                print(f"Model file '{model_file}' not found. Downloading default model...")
                _download_with_progress(DEFAULT_MODEL_URL, local_path)

    try:
        _ai_model = load_model(local_path, compile=False, custom_objects=_CUSTOM_OBJECTS)
    except Exception as e:
        raise RuntimeError(f"Failed to load model from '{local_path}': {e}") from e

    print(f"AI model loaded: {local_path}")
    return _ai_model


# =========================== Pre/Post + tiling ===============================
def _preprocess_uint8_to_m1p1(tile_uint8: np.ndarray) -> np.ndarray:
    # [0,255] -> [-1,1]
    return (tile_uint8.astype(np.float32) - 127.5) / 127.5

def _postprocess_m1p1_to_uint8(tile_f: np.ndarray) -> np.ndarray:
    # [-1,1] -> [0,255]
    y = (np.clip(tile_f, -1.0, 1.0) + 1.0) * 0.5
    return (y * 255.0).astype(np.uint8)

@tf.function(jit_compile=False)
def _forward(model, x):
    # x: [N,H,W,3] in [-1,1]; dtype can be fp32 or fp16 depending on policy
    return model(x, training=False)

def process_tile(tile_uint8: np.ndarray, model) -> np.ndarray:
    x = _preprocess_uint8_to_m1p1(tile_uint8)
    # Feed fp32; Keras will auto-cast if the model uses mixed precision.
    x = tf.convert_to_tensor(x[None, ...], dtype=tf.float32)
    y = _forward(model, x)[0].numpy()
    return _postprocess_m1p1_to_uint8(y)

def process_image_with_tiling(image: np.ndarray, model, tile_size=256, step_size=128) -> np.ndarray:
    h, w, _ = image.shape
    out = np.zeros((h, w, 3), dtype=np.float32)

    for y in range(0, h - tile_size + 1, step_size):
        for x in range(0, w - tile_size + 1, step_size):
            tile = image[y:y+tile_size, x:x+tile_size]
            pred = process_tile(tile, model)

            cy = tile_size // 4   # 64 when tile=256
            cx = tile_size // 4
            core = pred[cy:cy+step_size, cx:cx+step_size]  # 128×128 core

            out[y+cy:y+cy+step_size, x+cx:x+cx+step_size] = core

            del tile, pred, core
        maybe_cleanup()

    out = np.clip(out, 0, 255).astype(np.uint8)
    gc.collect()
    return out

# =========================== Public entry point ==============================
def EnhanceBrightfield(input_image_uint8: np.ndarray, model_file) -> np.ndarray:
    """
    Accept one RGB image (H,W,3) uint8, pad to reduce edge artifacts,
    denoise via the model, and return uint8 (H,W,3).
    """
    model = get_ai_model(model_file)

    pad = 256
    padded = np.pad(input_image_uint8, ((pad, pad), (pad, pad), (0, 0)), mode="reflect")

    enhanced = process_image_with_tiling(padded, model, tile_size=256, step_size=128)

    enhanced = enhanced[pad:-pad, pad:-pad]
    del padded
    maybe_cleanup()
    return enhanced
