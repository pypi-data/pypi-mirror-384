"""
Detection dataset interface
===========================

All datasets under ``prt_datasets.tasks.detection`` are **map-style** PyTorch
datasets. Each ``__getitem__(idx)`` returns a **tuple** ``(image, target)`` with
the following canonical schema and conventions.

Returned sample
---------------

- **image** (``torch.Tensor``):
  - Shape: ``(3, H, W)``
  - Dtype: ``torch.uint8`` by default (RGB).  Downstream transforms may convert
    to ``float32`` and normalize, but the *canonical pre-transform contract* is
    ``uint8``.
  - Color space: RGB.

- **target** (``dict``):
  - **"boxes"** → ``torch.FloatTensor`` of shape ``[N, 4]`` (XYXY, absolute pixels).
    - Ordering: ``[x1, y1, x2, y2]``.
    - Domain/invariants (half-open box convention):
      ``0 <= x1 < x2 <= W`` and ``0 <= y1 < y2 <= H``.
      Width/height are computed as ``x2 - x1`` / ``y2 - y1``.
    - Empty images are represented by a zero-length tensor of shape ``[0, 4]``.
  - **"labels"** → ``torch.LongTensor`` of shape ``[N]``.
    - **Contiguous class indices** in ``[0, num_classes-1]`` (dataset-specific
      category IDs may be remapped).
  - **"image_id"** → ``int`` unique within the split.

Transforms
----------

If a ``transforms`` callable is provided at construction, it is applied as
``image, target = transforms(image, target)`` and **must** preserve the schema.
Transforms that resize, flip, or crop are expected to update ``"boxes"`` and
``"size"`` accordingly.  If pre-transform dimensions are needed, use
``target["orig_size"]`` when available.

Notes
-----

- Datasets **must** return valid boxes (non-empty width/height).  Images without
  objects should return ``"boxes"`` and ``"labels"`` with zero rows.
- Class indices are contiguous; the mapping from original dataset IDs is exposed
  via optional fields or dataset-level metadata (e.g., ``dataset.classes``).

Example
-------

.. code-block:: python

    ds = SomeDetectionDataset(root=Path("/data/prt"), split="val")
    image, target = ds[0]
    assert image.dtype == torch.uint8 and image.ndim == 3
    assert target["boxes"].shape[1] == 4
    print(target["image_id"], target.get("size"))

"""
from .bdd100k import BDD100KDataset
from .coco import COCODataset

__all__ = [
    "BDD100KDataset",
    "COCODataset",
]