from pathlib import Path
from typing import Union
import re

def sanitize_filename(filename: str) -> str:
    """
    Convert a string into a safe filename by removing or replacing invalid characters.
    
    Args:
        filename: The string to convert into a safe filename
        
    Returns:
        A sanitized version of the filename that is safe to use in the filesystem
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces and other special chars
    filename = re.sub(r'[\s\-]+', '_', filename)
    # Remove any non-ASCII characters
    filename = re.sub(r'[^\x00-\x7F]+', '', filename)
    # Remove any leading/trailing periods or spaces
    filename = filename.strip('. ')
    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed'
    return filename

def get_data_dir(base_path: Union[str, Path]) -> Path:
    """Get the absolute path to the data directory."""
    base = Path(base_path)
    if base.name == 'data':
        return base
    return base / 'data'

def get_songs_dir(base_path: Union[str, Path]) -> Path:
    """Get the absolute path to the songs directory."""
    return get_data_dir(base_path) / 'songs'

def get_songs_catalog_path(base_path: Union[str, Path]) -> Path:
    """Get the absolute path to the songs catalog file."""
    return get_data_dir(base_path) / 'songs.json'

def get_song_dir(base_path: Union[str, Path], song_id: int) -> Path:
    """
    Get the absolute path to a song's directory.
    
    Args:
        base_path: Base project directory
        song_id: Genius song ID
        
    Returns:
        Path to the song directory
    """
    return get_songs_dir(base_path) / str(song_id)

def ensure_song_dir(base_path: Union[str, Path], song_id: int) -> Path:
    """
    Ensure a song's directory exists and return its path.
    
    Args:
        base_path: Base project directory
        song_id: Genius song ID
        
    Returns:
        Path to the created/existing song directory
    """
    song_dir = get_song_dir(base_path, song_id)
    song_dir.mkdir(parents=True, exist_ok=True)
    return song_dir