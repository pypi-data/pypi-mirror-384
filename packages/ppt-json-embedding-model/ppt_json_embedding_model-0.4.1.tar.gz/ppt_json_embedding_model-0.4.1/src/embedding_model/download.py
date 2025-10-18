"""Utilities for locating model weights.

Public release note: We do not distribute trained weights in this repository.
Set the environment variable `JSON_EMBED_MODEL_PATH` to point to a local
checkpoint, or handle weight acquisition out-of-band.
"""

import os
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
import urllib.request
import urllib.error
from tqdm import tqdm

logger = logging.getLogger(__name__)

# Default identifiers (not used to auto-download in public release)
DEFAULT_REPO = None
DEFAULT_VERSION = None
DEFAULT_MODEL_NAME = None

def get_cache_dir() -> Path:
    """Get the cache directory for downloaded models."""
    # Use user's cache directory or fallback to package dir
    if "XDG_CACHE_HOME" in os.environ:
        cache_dir = Path(os.environ["XDG_CACHE_HOME"]) / "embedding_model"
    elif "APPDATA" in os.environ:  # Windows
        cache_dir = Path(os.environ["APPDATA"]) / "embedding_model"
    else:
        cache_dir = Path.home() / ".cache" / "embedding_model"
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variables."""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PAT")

def create_authenticated_request(url: str, token: Optional[str] = None) -> urllib.request.Request:
    """Create a request with GitHub authentication if token is available."""
    req = urllib.request.Request(url)
    
    if token:
        req.add_header("Authorization", f"token {token}")
        req.add_header("Accept", "application/vnd.github.v3+json")
    
    return req

def get_release_asset_url(repo: str, version: str, filename: str, token: Optional[str] = None) -> str:
    """
    Get the download URL for a release asset using GitHub API.
    
    This is more reliable than constructing URLs directly, especially for private repos.
    """
    api_url = f"https://api.github.com/repos/{repo}/releases/tags/{version}"
    
    try:
        req = create_authenticated_request(api_url, token)
        with urllib.request.urlopen(req) as response:
            release_data = json.loads(response.read().decode())
            
        # Find the asset with matching filename
        for asset in release_data.get("assets", []):
            if asset["name"] == filename:
                if token:
                    # For authenticated requests, use the API download URL
                    return asset["url"]
                else:
                    # For public repos, use the browser download URL
                    return asset["browser_download_url"]
                    
        raise RuntimeError(f"Asset '{filename}' not found in release '{version}'")
        
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.error(f"ERROR Release '{version}' not found in repository '{repo}'")
            logger.error("NOTE: Check if the version exists and you have access to the repository")
            if not token:
                logger.error("NOTE: If this is a private repository, set GITHUB_TOKEN environment variable")
        raise RuntimeError(f"Could not access release info: HTTP {e.code} {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Could not fetch release info: {e}")

def download_file_with_progress(url: str, filepath: Path, token: Optional[str] = None) -> None:
    """Disabled in public release: weights are not distributed via this repo."""
    raise RuntimeError(
        "Auto-download of model weights is disabled in the public release. "
        "Set JSON_EMBED_MODEL_PATH to a local weights file."
    )

def download_pretrained_model(
    version: Optional[str] = DEFAULT_VERSION,
    repo: Optional[str] = DEFAULT_REPO,
    force_download: bool = False,
    cache_dir: Optional[Path] = None
) -> Path:
    """Disabled in public release: weights are not distributed via this repo.

    Returns:
        Path: never returns; always raises to direct users to set env var.
    """
    raise RuntimeError(
        "Pretrained weights are not distributed in this repository. "
        "Set JSON_EMBED_MODEL_PATH to a local checkpoint file."
    )

def get_default_model_path() -> Path:
    """
    Get the default model path, downloading if necessary.
    
    This is the main function that CLI tools should use.
    """
    logger.info("Initializing JSON Embedding Model...")
    
    # Check for environment variable override
    env_path = os.environ.get("JSON_EMBED_MODEL_PATH")
    if env_path:
        env_path = Path(env_path)
        if env_path.exists():
            logger.info(f"Using model from environment: {env_path}")
            return env_path
        else:
            logger.warning(f"WARNING Environment model path not found: {env_path}")
    
    # No auto-download in public release
    raise RuntimeError(
        "Model weights not found. Set JSON_EMBED_MODEL_PATH to your local "
        "checkpoint file path."
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    print("This package does not auto-download weights in the public release.")
    print("Set JSON_EMBED_MODEL_PATH to your local checkpoint and re-run your command.")
