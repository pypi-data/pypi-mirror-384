# Reva Coregistration

A Python package for image coregistration and coordinate transformation, specifically designed for medical imaging applications.

## Features

- **Image Coregistration**: Align images using landmark-based transformations
- **Coordinate Transformation**: Convert coordinates between different image spaces
- **Non-linear Warping**: Apply advanced warping techniques for precise alignment
- **Slice Management**: Handle multi-slice image data
- **Tile Processing**: Efficient processing of large images using tiling

## Installation

```bash
pip install reva-coregistration
```

## Quick Start

```python
from reva_coregistration import get_associated_coordinates

# Define landmarks for coregistration
landmarks = [
    {"target": {"x": 100, "y": 200}, "source": {"x": 150, "y": 250}},
    {"target": {"x": 300, "y": 400}, "source": {"x": 350, "y": 450}},
    # ... more landmark pairs
]

# Get associated coordinates
coordinates = get_associated_coordinates(
    x_percentage=0.5,
    y_percentage=0.3,
    source_image_width=1024,
    source_image_height=768,
    source_is_photograph=True,
    target_image_width=2048,
    target_image_height=1536,
    apply_nonlinear_warping=True,
    landmarks=landmarks
)

print(coordinates)
```

## Documentation

For detailed documentation, please visit the [project repository](https://github.com/yourusername/reva-coregistration).

## Development

To set up the development environment:

```bash
git clone https://github.com/yourusername/reva-coregistration.git
cd reva-coregistration
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 