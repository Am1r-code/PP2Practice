"""
player.py - Music Player Logic
Manages playlist, playback state, and pygame.mixer integration.
"""

import os
import pygame


class MusicPlayer:
    """
    Manages a playlist of audio tracks and playback controls.

    Attributes
    ----------
    tracks      : list[str]  – absolute file paths of all tracks
    current_idx : int        – index of the currently loaded track
    is_playing  : bool       – True while audio is active (not paused/stopped)
    is_paused   : bool       – True when playback is paused
    volume      : float      – 0.0 – 1.0
    """

    SUPPORTED_EXTS = {".mp3", ".wav", ".ogg", ".flac"}

    def __init__(self, music_dir: str):
        """Scan `music_dir` for audio files and initialise the mixer."""
        pygame.mixer.init()

        self.tracks      = self._scan_directory(music_dir)
        self.current_idx = 0
        self.is_playing  = False
        self.is_paused   = False
        self.volume      = 0.8

        pygame.mixer.music.set_volume(self.volume)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _scan_directory(self, directory: str) -> list:
        """Return sorted list of audio file paths found in `directory`."""
        if not os.path.isdir(directory):
            return []
        files = []
        for fname in sorted(os.listdir(directory)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in self.SUPPORTED_EXTS:
                files.append(os.path.join(directory, fname))
        return files

    def _load_current(self):
        """Load the track at current_idx into the mixer."""
        if not self.tracks:
            return
        pygame.mixer.music.load(self.tracks[self.current_idx])
        pygame.mixer.music.set_volume(self.volume)

    # ── Public controls ──────────────────────────────────────────────────────

    def play(self):
        """Play the current track from the beginning."""
        if not self.tracks:
            return
        self._load_current()
        pygame.mixer.music.play()
        self.is_playing = True
        self.is_paused  = False

    def stop(self):
        """Stop playback entirely."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused  = False

    def pause_toggle(self):
        """Toggle between paused and resumed states."""
        if not self.is_playing:
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            pygame.mixer.music.pause()
            self.is_paused = True

    def next_track(self):
        """Advance to the next track (wraps around)."""
        if not self.tracks:
            return
        self.current_idx = (self.current_idx + 1) % len(self.tracks)
        if self.is_playing:
            self.play()

    def prev_track(self):
        """Go back to the previous track (wraps around)."""
        if not self.tracks:
            return
        self.current_idx = (self.current_idx - 1) % len(self.tracks)
        if self.is_playing:
            self.play()

    def volume_up(self, step: float = 0.1):
        """Increase volume by `step`."""
        self.volume = min(1.0, self.volume + step)
        pygame.mixer.music.set_volume(self.volume)

    def volume_down(self, step: float = 0.1):
        """Decrease volume by `step`."""
        self.volume = max(0.0, self.volume - step)
        pygame.mixer.music.set_volume(self.volume)

    # ── Status helpers ───────────────────────────────────────────────────────

    def check_track_ended(self):
        """
        Call every frame. Auto-advance when mixer reports track finished.
        Returns True if a track transition occurred.
        """
        if self.is_playing and not self.is_paused:
            if not pygame.mixer.music.get_busy():
                self.next_track()
                return True
        return False

    @property
    def current_track_name(self) -> str:
        """Filename (without extension) of the currently loaded track."""
        if not self.tracks:
            return "No tracks found"
        path = self.tracks[self.current_idx]
        return os.path.splitext(os.path.basename(path))[0]

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def position_str(self) -> str:
        """Human-readable track position string."""
        if not self.tracks:
            return ""
        return f"Track {self.current_idx + 1} / {self.track_count}"

    @property
    def status_str(self) -> str:
        if not self.tracks:
            return "No tracks"
        if self.is_paused:
            return "⏸  PAUSED"
        if self.is_playing:
            return "▶  PLAYING"
        return "⏹  STOPPED"

    @property
    def volume_bar(self) -> str:
        """ASCII-art volume bar."""
        filled = int(self.volume * 10)
        return "♪ [" + "█" * filled + "░" * (10 - filled) + f"] {int(self.volume * 100)}%"
