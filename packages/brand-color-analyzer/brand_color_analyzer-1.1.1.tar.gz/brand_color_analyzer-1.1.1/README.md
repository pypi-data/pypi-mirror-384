# Brand Color Analyzer

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17375219.svg)](https://doi.org/10.5281/zenodo.17375219)
[![PyPI version](https://badge.fury.io/py/brand-color-analyzer.svg)](https://badge.fury.io/py/brand-color-analyzer)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A comprehensive tool for analyzing brand colors based on empirical research in color psychology and marketing. The tool provides detailed analysis of colors including brand personality dimensions, emotional responses, and cultural associations.

## Features

- Research-based color analysis using established theories
- Brand personality dimension analysis (sincerity, excitement, competence, sophistication, ruggedness)
- Emotional response evaluation (arousal, pleasure, dominance, warmth, calmness)
- Cultural association analysis (trust, quality, premium, innovation, tradition)
- Support for multiple image formats: PNG, JPG, JPEG, TIFF, WebP
- Batch processing capabilities
- Multiple output formats (JSON, TXT)
- Progress tracking and detailed summaries
- Comprehensive error handling

## Research Foundation

The tool implements research findings and methodologies from:

- Labrecque & Milne (2012): "Exciting Red and Competent Blue: The Importance of Color in Marketing"
- Singh (2006): "Impact of Color on Marketing"
- Elliot & Maier (2014): "Color Psychology: Effects of Perceiving Color on Psychological Functioning in Humans"

## Installation

### From PyPI (Recommended)

```bash
pip install brand-color-analyzer
```

### From Source

1. Clone the repository:

```bash
git clone https://github.com/MichailSemoglou/brand-color-analyzer.git
cd brand-color-analyzer
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install requirements:

```bash
pip install -r requirements.txt
```

## Usage

### Python API

```python
from brand_color_analyzer import ColorAnalyzer, ImageAnalyzer
from pathlib import Path

# 1. Analyze a specific RGB color
analyzer = ColorAnalyzer()
color_results = analyzer.analyze_color((255, 0, 0))  # Analyze red
print(color_results)

# 2. Analyze an image
img_analyzer = ImageAnalyzer(
    min_frequency=0.5,    # Analyze colors appearing in at least 0.5% of pixels
    max_frequency=100.0   # Include colors up to 100% of pixels
)

# Analyze and get results in text format
analysis = img_analyzer.analyze_image("path/to/image.jpg", output_format="txt")

# Save the analysis
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
img_analyzer.save_analysis(analysis, output_dir / "color_analysis")  # Will add .txt extension
```

### Command Line Interface

Single image analysis:

```bash
python brand_color_analyzer.py path/to/image.jpg output/directory
```

Batch processing:

```bash
python brand_color_analyzer.py path/to/image/directory output/directory
```

### Options

- `--min-frequency`: Minimum color frequency to analyze (default: 5.0)
- `--max-frequency`: Maximum color frequency percentage (default: 100.0)
- `--format`: Output format: json or txt (default: json)
- `-v, --verbose`: Increase output verbosity
- `--version`: Show program version
- `-h, --help`: Show help message

## Output Examples

This tool generates easy-to-understand reports about the psychological and marketing aspects of colors. Below are examples of what you'll get when analyzing a color.

### Text Output (TXT Format)

When using the `--format txt` option or `output_format="txt"` in the code, you'll get a human-readable report like this:

```
Color Analysis Results
======================

Color Information:
  Name: Red
  RGB: (255, 0, 0)
  HSV: (0, 1.000, 1.000)
  HEX: #FF0000
  CMYK: (0.00, 100.00, 100.00, 0.00)

Brand Personality Dimensions:
  Sincerity: 25.0%        // How genuine and wholesome the color appears
  Excitement: 85.0%       // How energetic and dynamic the color feels
  Competence: 30.0%       // How reliable and intelligent the color seems
  Sophistication: 40.0%   // How elegant and prestigious the color appears
  Ruggedness: 45.0%       // How tough and outdoorsy the color feels

Emotional Responses:
  Arousal: 95.0%          // How stimulating and attention-grabbing the color is
  Pleasure: 65.0%         // How enjoyable and positive the color feels
  Dominance: 80.0%        // How powerful and influential the color appears
  Warmth: 90.0%           // How warm vs. cool the color feels
  Calmness: 10.0%         // How relaxing and peaceful the color is

Cultural Associations:
  Trust: 25.0%            // How trustworthy the color appears
  Quality: 55.0%          // How high-quality the color seems
  Premium: 40.0%          // How luxurious the color feels
  Innovation: 65.0%       // How modern and forward-thinking the color appears
  Tradition: 35.0%        // How traditional and established the color seems
```

#### What This Means for Design Students:

- **Color Information:** Technical details about the exact color being analyzed
- **Brand Personality:** How the color influences perception of a brand's character
- **Emotional Responses:** The feelings and reactions the color is likely to evoke
- **Cultural Associations:** Common meanings and perceptions associated with the color

### JSON Output (Default)

When using the default JSON format, you'll get structured data that's ideal for further processing:

```json
{
  "color_attributes": {
    "rgb": [255, 0, 0],
    "hsv": [0, 1, 1],
    "hex": "#FF0000",
    "cmyk": [0, 100, 100, 0],
    "name": "Red"
  },
  "brand_personality": {
    "sincerity": 25.0,
    "excitement": 85.0,
    "competence": 30.0,
    "sophistication": 40.0,
    "ruggedness": 45.0
  },
  "emotional_response": {
    "arousal": 95.0,
    "pleasure": 65.0,
    "dominance": 80.0,
    "warmth": 90.0,
    "calmness": 10.0
  },
  "cultural_associations": {
    "trust": 25.0,
    "quality": 55.0,
    "premium": 40.0,
    "innovation": 65.0,
    "tradition": 35.0
  }
}
```

### Interpreting the Results

- **High percentages (70-100%)** indicate strong alignment with that attribute
- **Medium percentages (40-70%)** indicate moderate alignment
- **Low percentages (0-40%)** indicate minimal alignment

For example, the red color above scores high on "Excitement" (85%) and "Arousal" (95%), making it excellent for brands wanting to appear energetic and attention-grabbing, but may not be ideal for brands focusing on calmness (10%) or trustworthiness (25%).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this software in your research, please cite it using the DOI:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17375219.svg)](https://doi.org/10.5281/zenodo.17375219)

```
Semoglou, M. (2025). Brand Color Analyzer: A Research-Based Tool for Color Psychology in Marketing (Version 1.1.0). Zenodo. https://doi.org/10.5281/zenodo.17375219
```

You can also use the "Cite this repository" feature on GitHub or refer to the [CITATION.cff](CITATION.cff) file for other citation formats.

## Contact

- Author: Michail Semoglou
- Email: m.semoglou@tongji.edu.cn
