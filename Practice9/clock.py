"""
clock.py - Mickey Mouse Clock Logic
Handles time retrieval and angle calculation for clock hands.
"""

import datetime
import math


def get_current_time():
    """Return current (minutes, seconds) as integers."""
    now = datetime.datetime.now()
    return now.minute, now.second


def get_hand_angle(value, max_value):
    """
    Convert a time value to a rotation angle in degrees.
    
    Pygame's rotate() rotates counter-clockwise, and 0° points RIGHT.
    We want 0 units → pointing UP, increasing clockwise.
    
    Formula: angle = -(value / max_value * 360)
    The negative sign converts clockwise intent to pygame's CCW rotation.
    Starting offset: subtract 90° so 0 units = UP (12 o'clock).
    """
    fraction = value / max_value          # 0.0 – 1.0
    degrees = fraction * 360              # 0 – 360 clockwise
    pygame_angle = -(degrees - 0)         # pygame rotates CCW, so negate
    return pygame_angle


def seconds_angle(seconds):
    """Angle for the seconds hand (left hand). Full rotation = 60 s."""
    return get_hand_angle(seconds, 60)


def minutes_angle(minutes):
    """Angle for the minutes hand (right hand). Full rotation = 60 min."""
    return get_hand_angle(minutes, 60)


def rotate_image_around_base(surface, image, angle, base_pos, hand_length):
    """
    Rotate `image` by `angle` degrees and blit it so its base sits at base_pos.

    Steps:
      1. Rotate the image.
      2. Calculate where the rotated image's center should be so its 'tail'
         aligns with base_pos (the clock center).

    Parameters
    ----------
    surface    : pygame.Surface  – destination surface
    image      : pygame.Surface  – the hand image (pointing UP by default)
    angle      : float           – rotation angle (pygame CCW degrees)
    base_pos   : (x, y)          – pivot point on screen
    hand_length: int             – pixels from pivot to fingertip
    """
    import pygame

    rotated = pygame.transform.rotate(image, angle)

    # Direction the hand points after rotation (angle measured CW from UP)
    rad = math.radians(-angle - 90)          # convert to standard math angle
    tip_offset_x = math.cos(rad) * hand_length
    tip_offset_y = math.sin(rad) * hand_length

    # Center the rotated image halfway between base and tip
    cx = base_pos[0] + tip_offset_x / 2
    cy = base_pos[1] + tip_offset_y / 2

    rect = rotated.get_rect(center=(cx, cy))
    surface.blit(rotated, rect)
