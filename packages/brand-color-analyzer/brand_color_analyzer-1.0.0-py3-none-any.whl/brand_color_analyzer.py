"""
Brand Color Analyzer
====================

A comprehensive tool for analyzing brand colors based on empirical research in color psychology 
and marketing. The tool provides detailed analysis of colors including brand personality dimensions,
emotional responses, and cultural associations.

Research Foundation:
-------------------
- Labrecque & Milne (2012): "Exciting Red and Competent Blue: The Importance of Color in Marketing"
- Singh (2006): "Impact of Color on Marketing"
- Elliot & Maier (2014): "Color Psychology: Effects of Perceiving Color on Psychological Functioning in Humans"

Features:
--------
- Research-based color analysis
- Brand personality dimension analysis
- Emotional response evaluation
- Cultural association analysis
- Support for multiple image formats (PNG, JPG, JPEG, TIFF, WebP)
- Batch processing capabilities
- Multiple output formats (JSON, TXT)

Installation:
------------
pip install -r requirements.txt

Usage:
-----
Single image analysis:
    python brand_color_analyzer.py path/to/image.jpg output/directory

Batch processing:
    python brand_color_analyzer.py path/to/image/directory output/directory

Options:
    --min-frequency   Minimum color frequency to analyze (default: 5.0)
    --max-frequency   Maximum color frequency to analyze (default: 100.0)
    --format          Output format: json or txt (default: json)
    -v, --verbose     Increase output verbosity

Copyright (c) 2025 Michail Semoglou
All rights reserved.

Contact:
-------
Author: Michail Semoglou
Email: m.semoglou@tongji.edu.cn
GitHub: https://github.com/MichailSemoglou

License: MIT

Citation:
--------
If you use this tool in academic work, please cite:
    APA
    Semoglou, M. (2025). Brand Color Analyzer: A Research-Based Tool for Color Psychology in Marketing (Version 1.0.0). Retrieved from https://github.com/MichailSemoglou/brand-color-analyzer
    MLA
    Semoglou, Michail. "Brand Color Analyzer: A Research-Based Tool for Color Psychology in Marketing." 2025. GitHub, https://github.com/MichailSemoglou/brand-color-analyzer.
    Chicago
    Semoglou, Michail. "Brand Color Analyzer: A Research-Based Tool for Color Psychology in Marketing." Version 1.0.0. GitHub, 2025.
"""

__version__ = "1.0.0"

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any, Type
from dataclasses import dataclass
from collections import Counter
from datetime import datetime
import colorsys
import argparse

import numpy as np
import numpy.typing as npt
from PIL import Image
from matplotlib import colors
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Type aliases
RGB = Union[Tuple[int, int, int], npt.NDArray[np.int_]]
HSV = Tuple[float, float, float]
CMYK = Tuple[float, float, float, float]

class ColorValidationError(Exception):
    """Exception raised for color validation errors."""
    pass

class ColorValidator:
    """Validates color values and formats."""
    
    @staticmethod
    def validate_rgb(rgb: RGB) -> RGB:
        """
        Validate RGB values are within correct range.
        
        Args:
            rgb: RGB color value as tuple or numpy array
            
        Returns:
            Validated RGB tuple
            
        Raises:
            ColorValidationError: If RGB values are invalid
        """
        try:
            if isinstance(rgb, tuple):
                if not all(isinstance(x, int) for x in rgb):
                    raise ColorValidationError("RGB values must be integers")
                if not all(0 <= x <= 255 for x in rgb):
                    raise ColorValidationError("RGB values must be between 0 and 255")
                if len(rgb) != 3:
                    raise ColorValidationError("RGB tuple must have exactly 3 values")
                return rgb
            elif isinstance(rgb, np.ndarray):
                if rgb.dtype != np.int_:
                    raise ColorValidationError("RGB numpy array must be of integer type")
                if not np.all((rgb >= 0) & (rgb <= 255)):
                    raise ColorValidationError("RGB values must be between 0 and 255")
                if rgb.size != 3:
                    raise ColorValidationError("RGB array must have exactly 3 values")
                return tuple(rgb.tolist())
            raise ColorValidationError("RGB must be tuple or numpy array")
        except Exception as e:
            raise ColorValidationError(f"RGB validation error: {str(e)}")

    @staticmethod
    def validate_hsv(hsv: HSV) -> HSV:
        """
        Validate HSV values are within correct range.
        
        Args:
            hsv: HSV color value
            
        Returns:
            Validated HSV tuple
            
        Raises:
            ColorValidationError: If HSV values are invalid
        """
        try:
            if not isinstance(hsv, tuple) or len(hsv) != 3:
                raise ColorValidationError("HSV must be a tuple of 3 values")
            
            h, s, v = hsv
            if not all(isinstance(x, (int, float)) for x in hsv):
                raise ColorValidationError("HSV values must be numeric")
                
            if not 0 <= h <= 360:
                raise ColorValidationError("Hue must be between 0 and 360")
            if not 0 <= s <= 1:
                raise ColorValidationError("Saturation must be between 0 and 1")
            if not 0 <= v <= 1:
                raise ColorValidationError("Value must be between 0 and 1")
                
            return (float(h), float(s), float(v))
        except Exception as e:
            raise ColorValidationError(f"HSV validation error: {str(e)}")

@dataclass
class ColorAttributes:
    """Color information in different color spaces."""
    rgb: RGB
    hsv: HSV
    hex: str
    cmyk: CMYK
    name: str

@dataclass
class BrandPersonality:
    """
    Brand personality dimensions based on Aaker (1997) and
    color relationships from Labrecque & Milne (2012).
    
    Attributes:
        sincerity: White, pink, yellow associations (0-100)
        excitement: Red, orange, yellow associations (0-100)
        competence: Blue, brown associations (0-100)
        sophistication: Black, purple, pink associations (0-100)
        ruggedness: Brown, green associations (0-100)
    """
    sincerity: float
    excitement: float
    competence: float
    sophistication: float
    ruggedness: float

    def to_dict(self) -> Dict[str, float]:
        """Convert personality scores to dictionary with rounded values."""
        return {
            "sincerity": round(self.sincerity, 2),
            "excitement": round(self.excitement, 2),
            "competence": round(self.competence, 2),
            "sophistication": round(self.sophistication, 2),
            "ruggedness": round(self.ruggedness, 2)
        }

    def to_text(self) -> str:
        """Convert personality scores to formatted text."""
        return (
            f"Brand Personality Dimensions:\n"
            f"  Sincerity: {self.sincerity:.2f}%\n"
            f"  Excitement: {self.excitement:.2f}%\n"
            f"  Competence: {self.competence:.2f}%\n"
            f"  Sophistication: {self.sophistication:.2f}%\n"
            f"  Ruggedness: {self.ruggedness:.2f}%"
        )

@dataclass
class EmotionalResponse:
    """
    Emotional responses to color based on Singh (2006) and 
    Elliot & Maier (2014).
    
    Attributes:
        arousal: Level of stimulation/excitement (0-100)
        pleasure: Level of enjoyment/positivity (0-100)
        dominance: Level of control/power (0-100)
        warmth: Level of perceived warmth (0-100)
        calmness: Level of relaxation/peace (0-100)
    """
    arousal: float
    pleasure: float
    dominance: float
    warmth: float
    calmness: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert emotional responses to dictionary with rounded values."""
        return {
            "arousal": round(self.arousal, 2),
            "pleasure": round(self.pleasure, 2),
            "dominance": round(self.dominance, 2),
            "warmth": round(self.warmth, 2),
            "calmness": round(self.calmness, 2)
        }

    def to_text(self) -> str:
        """Convert emotional responses to formatted text."""
        return (
            f"Emotional Responses:\n"
            f"  Arousal: {self.arousal:.2f}%\n"
            f"  Pleasure: {self.pleasure:.2f}%\n"
            f"  Dominance: {self.dominance:.2f}%\n"
            f"  Warmth: {self.warmth:.2f}%\n"
            f"  Calmness: {self.calmness:.2f}%"
        )

@dataclass
class CulturalAssociations:
    """
    Cultural and contextual associations based on research.
    
    Attributes:
        trust: Level of perceived trustworthiness (0-100)
        quality: Level of perceived quality (0-100)
        premium: Level of perceived premium/luxury (0-100)
        innovation: Level of perceived innovation (0-100)
        tradition: Level of perceived traditionalism (0-100)
    """
    trust: float
    quality: float
    premium: float
    innovation: float
    tradition: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert cultural associations to dictionary with rounded values."""
        return {
            "trust": round(self.trust, 2),
            "quality": round(self.quality, 2),
            "premium": round(self.premium, 2),
            "innovation": round(self.innovation, 2),
            "tradition": round(self.tradition, 2)
        }

    def to_text(self) -> str:
        """Convert cultural associations to formatted text."""
        return (
            f"Cultural Associations:\n"
            f"  Trust: {self.trust:.2f}%\n"
            f"  Quality: {self.quality:.2f}%\n"
            f"  Premium: {self.premium:.2f}%\n"
            f"  Innovation: {self.innovation:.2f}%\n"
            f"  Tradition: {self.tradition:.2f}%"
        )
    
class ColorConverter:
    """Utility class for color space conversions and naming."""
    
    @staticmethod
    def rgb_to_hsv(rgb: RGB) -> HSV:
        """
        Convert RGB to HSV color space.
        
        Args:
            rgb: RGB color tuple or array
            
        Returns:
            HSV color tuple
            
        Raises:
            ColorValidationError: If RGB values are invalid
        """
        rgb = ColorValidator.validate_rgb(rgb)
        r, g, b = [x / 255.0 for x in rgb]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        hsv = (round(h * 360, 2), round(s, 3), round(v, 3))
        return ColorValidator.validate_hsv(hsv)

    @staticmethod
    def rgb_to_hex(rgb: RGB) -> str:
        """
        Convert RGB to hexadecimal string.
        
        Args:
            rgb: RGB color tuple or array
            
        Returns:
            Hexadecimal color string (e.g., "#FF0000")
            
        Raises:
            ColorValidationError: If RGB values are invalid
        """
        rgb = ColorValidator.validate_rgb(rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    @staticmethod
    def rgb_to_cmyk(rgb: RGB) -> CMYK:
        """
        Convert RGB to CMYK color space.
        
        Args:
            rgb: RGB color tuple or array
            
        Returns:
            CMYK color tuple (values 0-100)
            
        Raises:
            ColorValidationError: If RGB values are invalid
        """
        rgb = ColorValidator.validate_rgb(rgb)
        r, g, b = [x / 255.0 for x in rgb]
        
        # Handle special cases
        if r == g == b == 0:
            return (0.0, 0.0, 0.0, 100.0)
            
        c = 1 - r
        m = 1 - g
        y = 1 - b
        k = min(c, m, y)
        
        if k == 1:
            return (0.0, 0.0, 0.0, 100.0)
            
        c = round((c - k) / (1 - k) * 100, 2)
        m = round((m - k) / (1 - k) * 100, 2)
        y = round((y - k) / (1 - k) * 100, 2)
        k = round(k * 100, 2)
        
        return (c, m, y, k)

    @staticmethod
    def get_color_name(rgb: RGB) -> str:
        """
        Get human-readable color name using closest named color match.
        
        Args:
            rgb: RGB color tuple or array
            
        Returns:
            Human-readable color name (e.g., "Deep Sky Blue")
            
        Raises:
            ColorValidationError: If RGB values are invalid
        """
        rgb = ColorValidator.validate_rgb(rgb)
        rgb_normalized = tuple(x/255 for x in rgb)
        
        min_dist = float('inf')
        closest_name = "Unknown"
        
        for name, color_value in colors.CSS4_COLORS.items():
            color_rgb = colors.to_rgb(color_value)
            dist = sum((a - b) ** 2 for a, b in zip(rgb_normalized, color_rgb))
            
            if dist < min_dist:
                min_dist = dist
                closest_name = name
        
        return closest_name.replace('_', ' ').title()

class ColorAnalyzer:
    """Main class for color analysis incorporating research-based findings."""
    
    def __init__(self) -> None:
        """Initialize analyzer with color converter."""
        self.converter = ColorConverter()

    def analyze_color(self, rgb: RGB, output_format: str = "json") -> Union[Dict[str, Any], str]:
        """
        Analyze color and return comprehensive results.
        
        Args:
            rgb: RGB color tuple or array
            output_format: Output format ("json" or "txt")
            
        Returns:
            Dictionary or formatted string containing analysis results:
                - color_attributes: Basic color information
                - brand_personality: Brand personality dimension scores
                - emotional_response: Emotional response scores
                - cultural_associations: Cultural association scores
            
        Raises:
            ColorValidationError: If RGB values are invalid
            ValueError: If output_format is invalid
        """
        if output_format not in ["json", "txt"]:
            raise ValueError('output_format must be either "json" or "txt"')

        try:
            # Validate and convert color to different spaces
            rgb = ColorValidator.validate_rgb(rgb)
            hsv = self.converter.rgb_to_hsv(rgb)
            hex_code = self.converter.rgb_to_hex(rgb)
            cmyk = self.converter.rgb_to_cmyk(rgb)
            name = self.converter.get_color_name(rgb)
            
            # Perform analysis
            brand_personality = self._analyze_brand_personality(hsv)
            emotional_response = self._analyze_emotional_response(hsv)
            cultural_associations = self._analyze_cultural_associations(hsv)
            
            if output_format == "json":
                return {
                    "color_attributes": {
                        "rgb": rgb,
                        "hsv": hsv,
                        "hex": hex_code,
                        "cmyk": cmyk,
                        "name": name
                    },
                    "brand_personality": brand_personality.to_dict(),
                    "emotional_response": emotional_response.to_dict(),
                    "cultural_associations": cultural_associations.to_dict()
                }
            else:  # txt format
                return (
                    f"Color Analysis Results\n"
                    f"=====================\n\n"
                    f"Color Information:\n"
                    f"  Name: {name}\n"
                    f"  RGB: {rgb}\n"
                    f"  HSV: {hsv}\n"
                    f"  HEX: {hex_code}\n"
                    f"  CMYK: {cmyk}\n\n"
                    f"{brand_personality.to_text()}\n\n"
                    f"{emotional_response.to_text()}\n\n"
                    f"{cultural_associations.to_text()}"
                )
        except Exception as e:
            logger.error(f"Error analyzing color {rgb}: {str(e)}")
            raise

    def _analyze_brand_personality(self, hsv: HSV) -> BrandPersonality:
        """
        Analyze brand personality dimensions based on Labrecque & Milne (2012).
        
        Args:
            hsv: HSV color values
            
        Returns:
            BrandPersonality object with dimension scores
            
        Raises:
            ColorValidationError: If HSV values are invalid
        """
        hsv = ColorValidator.validate_hsv(hsv)
        h, s, v = hsv
        
        # Calculate base color influences
        red_influence = max(0, 1 - min(abs(h - 0), abs(h - 360)) / 30)
        blue_influence = max(0, 1 - abs(h - 210) / 30) if 180 <= h <= 240 else 0
        purple_influence = max(0, 1 - abs(h - 285) / 15) if 270 <= h <= 300 else 0
        yellow_influence = max(0, 1 - abs(h - 60) / 30) if 30 <= h <= 90 else 0
        green_influence = max(0, 1 - abs(h - 120) / 30) if 90 <= h <= 150 else 0
        brown_influence = s * (1 - v) if 20 <= h <= 40 else 0
        
        return BrandPersonality(
            sincerity=self._calculate_sincerity(h, s, v, yellow_influence),
            excitement=self._calculate_excitement(h, s, v, red_influence),
            competence=self._calculate_competence(h, s, v, blue_influence),
            sophistication=self._calculate_sophistication(h, s, v, purple_influence),
            ruggedness=self._calculate_ruggedness(h, s, v, brown_influence, green_influence)
        )

    def _calculate_sincerity(self, h: float, s: float, v: float, yellow_influence: float) -> float:
        """Calculate sincerity score based on color properties."""
        # White influence (low saturation, high value)
        white_influence = (1 - s) * v
        
        # Pink influence (around 350° hue)
        pink_influence = max(0, 1 - min(abs(h - 350), abs(h - (-10))) / 20) * s * v
        
        # Calculate weighted score (0-100)
        score = (
            white_influence * 40 +
            yellow_influence * 35 +
            pink_influence * 25
        )
        
        return min(100, max(0, score))
        
    def _calculate_excitement(self, h: float, s: float, v: float, red_influence: float) -> float:
        """Calculate excitement score based on color properties."""
        # Orange influence (around 30° hue)
        orange_influence = max(0, 1 - abs(h - 30) / 15) if 15 <= h <= 45 else 0
        
        # Yellow influence calculated in main method
        yellow_influence = max(0, 1 - abs(h - 60) / 30) if 30 <= h <= 90 else 0
        
        # Intensity factor
        intensity = s * v
        
        # Calculate weighted score (0-100)
        score = (
            red_influence * 45 +
            orange_influence * 30 +
            yellow_influence * 25
        ) * intensity
        
        return min(100, max(0, score))
        
    def _calculate_competence(self, h: float, s: float, v: float, blue_influence: float) -> float:
        """Calculate competence score based on color properties."""
        # Brown influence
        brown_influence = s * (1 - v) if 20 <= h <= 40 else 0
        
        # Intensity for blue
        blue_intensity = s * v
        
        # Calculate weighted score (0-100)
        score = (
            blue_influence * blue_intensity * 70 +
            brown_influence * 30
        )
        
        return min(100, max(0, score))
        
    def _calculate_sophistication(self, h: float, s: float, v: float, purple_influence: float) -> float:
        """Calculate sophistication score based on color properties."""
        # Black influence (low value)
        black_influence = 1 - v
        
        # Pink influence (around 350° hue)
        pink_influence = max(0, 1 - min(abs(h - 350), abs(h - (-10))) / 20) * s * v
        
        # Calculate weighted score (0-100)
        score = (
            black_influence * 40 +
            purple_influence * 35 +
            pink_influence * 25
        )
        
        return min(100, max(0, score))
        
    def _calculate_ruggedness(self, h: float, s: float, v: float, brown_influence: float, green_influence: float) -> float:
        """Calculate ruggedness score based on color properties."""
        # Intensity factor
        intensity = s * v
        
        # Calculate weighted score (0-100)
        score = (
            brown_influence * 60 +
            green_influence * intensity * 40
        )
        
        return min(100, max(0, score))

    def _analyze_emotional_response(self, hsv: HSV) -> EmotionalResponse:
        """
        Analyze emotional responses based on color properties.
        
        Args:
            hsv: HSV color values
            
        Returns:
            EmotionalResponse object with response scores
            
        Raises:
            ColorValidationError: If HSV values are invalid
        """
        hsv = ColorValidator.validate_hsv(hsv)
        h, s, v = hsv
        
        # Calculate base influences
        warm_hue = max(0, 1 - min(abs(h - 30), abs(h - 350)) / 30)  # Red-orange-yellow range
        cool_hue = max(0, 1 - abs(h - 210) / 60)  # Blue-green range
        
        # Intensity factors
        intensity = s * v
        muted_factor = (1 - s) * v
        
        return EmotionalResponse(
            arousal=self._calculate_arousal(h, s, v, warm_hue, intensity),
            pleasure=self._calculate_pleasure(h, s, v, warm_hue, cool_hue),
            dominance=self._calculate_dominance(h, s, v),
            warmth=self._calculate_warmth(h, s, v, warm_hue),
            calmness=self._calculate_calmness(h, s, v, cool_hue, muted_factor)
        )

    def _calculate_arousal(self, h: float, s: float, v: float, warm_hue: float, intensity: float) -> float:
        """Calculate arousal score based on color properties."""
        # High arousal: Saturated warm colors
        warm_arousal = warm_hue * intensity * 100
        
        # Moderate arousal: High value, high saturation cool colors
        cool_arousal = (1 - warm_hue) * intensity * 70
        
        score = max(warm_arousal, cool_arousal)
        return min(100, max(0, score))

    def _calculate_pleasure(self, h: float, s: float, v: float, warm_hue: float, cool_hue: float) -> float:
        """Calculate pleasure score based on color properties."""
        # Warm colors contribution
        warm_pleasure = warm_hue * s * v * 90
        
        # Cool colors contribution
        cool_pleasure = cool_hue * s * v * 70
        
        # Light colors contribution (high value, low-medium saturation)
        light_pleasure = v * (1 - s) * 80
        
        score = max(warm_pleasure, cool_pleasure, light_pleasure)
        return min(100, max(0, score))

    def _calculate_dominance(self, h: float, s: float, v: float) -> float:
        """Calculate dominance score based on color properties."""
        # Strong, saturated colors increase dominance
        saturation_factor = s * 0.7
        
        # Dark colors (low value) also contribute to dominance
        darkness_factor = (1 - v) * 0.3
        
        score = (saturation_factor + darkness_factor) * 100
        return min(100, max(0, score))

    def _calculate_warmth(self, h: float, s: float, v: float, warm_hue: float) -> float:
        """Calculate warmth score based on color properties."""
        # Warm colors with moderate to high saturation and value
        score = warm_hue * s * v * 100
        return min(100, max(0, score))

    def _calculate_calmness(self, h: float, s: float, v: float, cool_hue: float, muted_factor: float) -> float:
        """Calculate calmness score based on color properties."""
        # Cool, muted colors increase calmness
        cool_calmness = cool_hue * muted_factor * 100
        
        # Light, low-saturation colors also contribute
        light_calmness = v * (1 - s) * 80
        
        score = max(cool_calmness, light_calmness)
        return min(100, max(0, score))

    def _analyze_cultural_associations(self, hsv: HSV) -> CulturalAssociations:
        """
        Analyze cultural associations based on color properties.
        
        Args:
            hsv: HSV color values
            
        Returns:
            CulturalAssociations object with association scores
            
        Raises:
            ColorValidationError: If HSV values are invalid
        """
        hsv = ColorValidator.validate_hsv(hsv)
        h, s, v = hsv
        
        # Calculate base influences
        blue_influence = max(0, 1 - abs(h - 210) / 30) if 180 <= h <= 240 else 0
        gold_influence = max(0, 1 - abs(h - 45) / 15) * s * v if 30 <= h <= 60 else 0
        silver_influence = (1 - s) * v if v > 0.7 else 0
        
        return CulturalAssociations(
            trust=self._calculate_trust(h, s, v, blue_influence),
            quality=self._calculate_quality(h, s, v, gold_influence, silver_influence),
            premium=self._calculate_premium(h, s, v, gold_influence),
            innovation=self._calculate_innovation(h, s, v),
            tradition=self._calculate_tradition(h, s, v)
        )

    def _calculate_trust(self, h: float, s: float, v: float, blue_influence: float) -> float:
        """Calculate trust score based on color properties."""
        # Blue is highly associated with trust
        blue_trust = blue_influence * s * v * 100
        
        # Conservative colors (low saturation, high value) also contribute
        conservative_trust = (1 - s) * v * 70
        
        score = max(blue_trust, conservative_trust)
        return min(100, max(0, score))

    def _calculate_quality(self, h: float, s: float, v: float, gold_influence: float, silver_influence: float) -> float:
        """Calculate quality score based on color properties."""
        # Gold and silver tones suggest quality
        metallic_quality = max(gold_influence * 100, silver_influence * 90)
        
        # Deep, rich colors (high saturation, medium-low value)
        rich_quality = s * (1 - v) * 80
        
        score = max(metallic_quality, rich_quality)
        return min(100, max(0, score))

    def _calculate_premium(self, h: float, s: float, v: float, gold_influence: float) -> float:
        """Calculate premium score based on color properties."""
        # Gold tones highly correlate with premium perception
        gold_premium = gold_influence * 100
        
        # Dark, rich colors also suggest premium quality
        dark_premium = s * (1 - v) * 80
        
        # Black (very low value) is associated with premium
        black_premium = (1 - v) * (1 - s) * 90 if v < 0.2 else 0
        
        score = max(gold_premium, dark_premium, black_premium)
        return min(100, max(0, score))

    def _calculate_innovation(self, h: float, s: float, v: float) -> float:
        """Calculate innovation score based on color properties."""
        # Bright, saturated colors suggest innovation
        bright_factor = s * v
        
        # Purple and blue hues are associated with innovation
        tech_hue = max(0, 1 - min(abs(h - 270), abs(h - 210)) / 45)
        
        # Unique combinations of high saturation and unusual hues
        uniqueness = s * (1 - max(0, 1 - min(abs(h - 180), abs(h - 300)) / 30))
        
        score = (bright_factor * 0.4 + tech_hue * 0.4 + uniqueness * 0.2) * 100
        return min(100, max(0, score))

    def _calculate_tradition(self, h: float, s: float, v: float) -> float:
        """Calculate tradition score based on color properties."""
        # Earth tones (browns, deep reds)
        earth_tone = max(0, 1 - min(abs(h - 30), abs(h - 0)) / 30) * s * (1 - v)
        
        # Deep, muted colors
        muted_depth = (1 - s) * (1 - v)
        
        # Classic navy blue
        navy = max(0, 1 - abs(h - 220) / 20) * s * (1 - v) if 200 <= h <= 240 else 0
        
        score = (earth_tone * 0.4 + muted_depth * 0.3 + navy * 0.3) * 100
        return min(100, max(0, score))


class ImageAnalyzer:
    """Class for analyzing colors in images."""
    
    def __init__(self, min_frequency: float = 5.0, max_frequency: float = 100.0) -> None:
        """
        Initialize image analyzer.
        
        Args:
            min_frequency: Minimum color frequency percentage to analyze (default: 5.0)
            max_frequency: Maximum color frequency percentage to analyze (default: 100.0)
            
        Raises:
            ValueError: If frequency values are invalid
        """
        if not 0 <= min_frequency <= max_frequency <= 100:
            raise ValueError(
                "Invalid frequency range. Must satisfy: "
                "0 <= min_frequency <= max_frequency <= 100"
            )
            
        self.color_analyzer = ColorAnalyzer()
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.webp'}
        self.min_frequency = min_frequency
        self.max_frequency = max_frequency

    def analyze_image(self, image_path: Union[str, Path], output_format: str = "json") -> Dict[str, Any]:
        """
        Analyze colors in an image.
        
        Args:
            image_path: Path to image file
            output_format: Output format ("json" or "txt")
            
        Returns:
            Dictionary containing analysis results
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image format is not supported
            Exception: For other errors during analysis
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if path.suffix.lower() not in self.supported_formats:
            raise ValueError(
                f"Unsupported format: {path.suffix}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )
            
        try:
            with Image.open(path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Get image info
                width, height = img.size
                pixel_count = width * height
                
                # Convert image to RGB data array
                rgb_data = list(img.getdata())
                
                # Ensure RGB format for all colors (take only RGB components)
                rgb_tuples = [tuple(c[:3]) for c in rgb_data]
                
                # Count color frequencies
                colors = Counter(rgb_tuples)
                
                # Sort colors by frequency
                sorted_colors = sorted(colors.items(), key=lambda x: x[1], reverse=True)
                
                # Analyze colors within frequency range
                results = []
                total_analyzed = 0
                
                for color, count in sorted_colors:
                    frequency = (count / pixel_count) * 100
                    if frequency < self.min_frequency:
                        break
                    if frequency > self.max_frequency:
                        continue
                    
                    # Ensure color is a valid RGB tuple
                    rgb_color = tuple(int(c) for c in color[:3])
                    
                    analysis = {
                        "color": rgb_color,
                        "frequency": round(frequency, 2),
                        "analysis": self.color_analyzer.analyze_color(
                            rgb_color, 
                            output_format=output_format
                        )
                    }
                    results.append(analysis)
                    total_analyzed += frequency
                
                analysis_result = {
                    "image_info": {
                        "path": str(path),
                        "dimensions": (width, height),
                        "total_pixels": pixel_count,
                        "analyzed_percentage": round(total_analyzed, 2),
                        "color_count": len(results)
                    },
                    "color_analysis": results
                }
                
                if output_format == "txt":
                    return self._format_analysis_as_text(analysis_result)
                return analysis_result
                
        except Exception as e:
            logger.error(f"Error analyzing image {path}: {str(e)}")
            raise  # Raise inside the except block

    def _format_analysis_as_text(self, analysis: Dict[str, Any]) -> str:
        """Convert analysis results to formatted text."""
        image_info = analysis["image_info"]
        result = [
            "Image Analysis Results",
            "====================\n",
            f"Image Information:",
            f"  Path: {image_info['path']}",
            f"  Dimensions: {image_info['dimensions'][0]}x{image_info['dimensions'][1]}",
            f"  Total Pixels: {image_info['total_pixels']:,}",
            f"  Analyzed Colors: {image_info['color_count']}",
            f"  Coverage: {image_info['analyzed_percentage']:.2f}%\n",
            "Color Analysis:",
        ]
        
        for idx, color_data in enumerate(analysis["color_analysis"], 1):
            result.extend([
                f"\nColor #{idx}:",
                f"  Frequency: {color_data['frequency']:.2f}%",
                color_data['analysis']  # Already formatted as text
            ])
            
        return "\n".join(result)

    def save_analysis(self, analysis: Union[Dict[str, Any], str], output_path: Union[str, Path]) -> None:
        """
        Save analysis results to file.
        
        Args:
            analysis: Analysis results (dictionary or formatted string)
            output_path: Path to save results
            
        Raises:
            Exception: If saving fails
        """
        output_path = Path(output_path)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(analysis, str):
                # Text format
                with output_path.with_suffix('.txt').open('w', encoding='utf-8') as f:
                    f.write(analysis)
            else:
                # JSON format
                with output_path.with_suffix('.json').open('w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2, ensure_ascii=False)
                    
            logger.info(f"Analysis saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving analysis to {output_path}: {str(e)}")
            raise

class BatchAnalyzer:
    """Class for handling batch processing of multiple images."""

    def __init__(self, min_frequency: float = 5.0, max_frequency: float = 100.0) -> None:
        """
        Initialize batch analyzer.
        
        Args:
            min_frequency: Minimum color frequency percentage to analyze (default: 5.0)
            max_frequency: Maximum color frequency percentage to analyze (default: 100.0)
            
        Raises:
            ValueError: If frequency values are invalid
        """
        self.analyzer = ImageAnalyzer(
            min_frequency=min_frequency,
            max_frequency=max_frequency
        )
        self.results: List[Dict[str, str]] = []
        self.errors: List[Dict[str, str]] = []

    def process_directory(self, input_dir: Path, output_dir: Path, output_format: str = "json") -> None:
        """
        Process all supported images in a directory.
        
        Args:
            input_dir: Directory containing images
            output_dir: Directory to save analysis results
            output_format: Output format ("json" or "txt")
            
        Raises:
            ValueError: If no supported images found
            Exception: For other processing errors
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        
        # Get all image files
        image_files = [
            f for f in input_dir.rglob('*') 
            if f.suffix.lower() in self.analyzer.supported_formats
        ]
        
        if not image_files:
            raise ValueError(
                f"No supported image files found in {input_dir}. "
                f"Supported formats: {', '.join(self.analyzer.supported_formats)}"
            )

        # Process files with progress bar
        for file_path in tqdm(image_files, desc="Processing images", unit="file"):
            try:
                analysis = self.analyzer.analyze_image(file_path, output_format=output_format)
                
                if output_format == "txt":
                    output_file = output_dir / f"{file_path.stem}_analysis.txt"
                else:
                    output_file = output_dir / f"{file_path.stem}_analysis.json"
                    
                self.analyzer.save_analysis(analysis, output_file)
                self.results.append({
                    "file": str(file_path),
                    "status": "success",
                    "output": str(output_file)
                })
            except Exception as e:
                error_msg = str(e)
                self.errors.append({
                    "file": str(file_path),
                    "error": error_msg
                })
                logger.error(f"Error processing {file_path}: {error_msg}")
                continue

    def save_summary(self, output_path: Path, output_format: str = "json") -> None:
        """
        Save processing summary to file.
        
        Args:
            output_path: Directory to save summary
            output_format: Output format ("json" or "txt")
        """
        summary = {
            "summary": {
                "total_files": len(self.results) + len(self.errors),
                "successful": len(self.results),
                "failed": len(self.errors),
                "success_rate": f"{(len(self.results) / (len(self.results) + len(self.errors)) * 100):.1f}%"
            },
            "successful_files": self.results,
            "failed_files": self.errors
        }
        
        if output_format == "txt":
            output_path = output_path / "analysis_summary.txt"
            with output_path.open('w', encoding='utf-8') as f:
                f.write("Batch Processing Summary\n")
                f.write("======================\n\n")
                f.write(f"Total Files Processed: {summary['summary']['total_files']}\n")
                f.write(f"Successfully Processed: {summary['summary']['successful']}\n")
                f.write(f"Failed to Process: {summary['summary']['failed']}\n")
                f.write(f"Success Rate: {summary['summary']['success_rate']}\n\n")
                
                if self.results:
                    f.write("Successfully Processed Files:\n")
                    for result in self.results:
                        f.write(f"  • {result['file']} -> {result['output']}\n")
                
                if self.errors:
                    f.write("\nFailed Files:\n")
                    for error in self.errors:
                        f.write(f"  • {error['file']}: {error['error']}\n")
        else:
            output_path = output_path / "analysis_summary.json"
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
                
        logger.info(f"Summary saved to {output_path}")

def validate_paths(input_path: Path, output_path: Path) -> None:
    """
    Validate input and output paths.
    
    Args:
        input_path: Input file or directory path
        output_path: Output directory path
        
    Raises:
        ValueError: If paths are invalid
    """
    if not input_path.exists():
        raise ValueError(f"Input path does not exist: {input_path}")
    
    if output_path.exists() and not output_path.is_dir():
        raise ValueError(f"Output path exists but is not a directory: {output_path}")

def main() -> None:
    """Command line interface for the tool."""
    parser = argparse.ArgumentParser(
        description=__doc__,  # Use the module's docstring
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "input_path",
        help="Path to input image or directory",
        type=Path
    )
    
    parser.add_argument(
        "output_path",
        help="Path to output directory",
        type=Path
    )

    parser.add_argument(
        "--min-frequency",
        help="Minimum color frequency percentage to analyze (default: 5.0)",
        type=float,
        default=5.0
    )
    
    parser.add_argument(
        "--max-frequency",
        help="Maximum color frequency percentage to analyze (default: 100.0)",
        type=float,
        default=100.0
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "txt"],
        default="json",
        help="Output format (default: json)"
    )

    parser.add_argument(
        "-v", "--verbose",
        help="Increase output verbosity",
        action="store_true"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Validate input/output paths
        validate_paths(args.input_path, args.output_path)
        
        # Validate frequency range
        if not 0 <= args.min_frequency <= args.max_frequency <= 100:
            raise ValueError(
                "Invalid frequency range. Must satisfy: "
                "0 <= min_frequency <= max_frequency <= 100"
            )
        
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = args.output_path / f"analysis_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if args.input_path.is_file():
            # Process single file
            analyzer = ImageAnalyzer(
                min_frequency=args.min_frequency,
                max_frequency=args.max_frequency
            )
            
            if args.input_path.suffix.lower() in analyzer.supported_formats:
                analysis = analyzer.analyze_image(args.input_path, output_format=args.format)
                if args.format == "txt":
                    output_file = output_dir / f"{args.input_path.stem}_analysis.txt"
                else:
                    output_file = output_dir / f"{args.input_path.stem}_analysis.json"
                    
                analyzer.save_analysis(analysis, output_file)
                logger.info(f"Successfully analyzed {args.input_path}")
            else:
                logger.error(f"Unsupported file format: {args.input_path.suffix}")
                sys.exit(1)
                
        elif args.input_path.is_dir():
            # Process directory
            batch_analyzer = BatchAnalyzer(
                min_frequency=args.min_frequency,
                max_frequency=args.max_frequency
            )
            try:
                batch_analyzer.process_directory(
                    args.input_path,
                    output_dir,
                    output_format=args.format
                )
                batch_analyzer.save_summary(output_dir, output_format=args.format)
                logger.info(
                    f"Batch processing complete. "
                    f"Processed {len(batch_analyzer.results)} files successfully, "
                    f"{len(batch_analyzer.errors)} failed. "
                    f"Results saved to {output_dir}"
                )
            except ValueError as e:
                logger.error(str(e))
                sys.exit(1)
        else:
            logger.error("Invalid input path")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
