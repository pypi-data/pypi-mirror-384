# face-embeddings-lib

A minimal library for extracting face embeddings from images using YOLO (for face detection) and Facenet (for embedding extraction). Useful for any application needing facial embeddings or face search.

## Installation

Install dependencies with Poetry:

```bash
poetry install
```

Or directly with pip:

```bash
pip install ultralytics facenet-pytorch torch opencv-python numpy
```

## Usage Example

```python
from face_embeddings_lib import EmbeddingEngine

with open("image.jpg", "rb") as f:
    image_bytes = f.read()

engine = EmbeddingEngine()
embeddings = engine.generate_face_embeddings(image_bytes)

print("Number of faces:", embeddings.get("face_count"))
print("Embeddings:", embeddings.get("face_embedding"))
```

- `face_embedding` will be a list of 512-float vectors averaged across faces found.
- `face_count` is the number of faces detected.
- `annotated_bytes` is the JPEG-encoded annotated image (you can save it or display it).

## Requirements

- Python 3.10 or 3.11
- Torch with CUDA enabled for best performance (optional)

## License

MIT

# face-embeddings-lib

repo for embeddings functions package
