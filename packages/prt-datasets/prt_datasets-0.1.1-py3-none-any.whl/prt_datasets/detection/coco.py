import json
import os
import numpy as np
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import torch
from PIL import Image
from prt_datasets.base import Dataset
import prt_datasets.common.utils as utils


class COCODataset(Dataset):
    """
    COCO Detection 2017 dataset.

    .. image:: /_static/coco-2017.png
        :alt: COCO 2017 Example
        :width: 100%
        :align: center

    On-disk layout after `download(root)`:
        <root>/
          coco/
            2017/
              images/
                train2017/
                val2017/
                test2017/
              annotations/
                instances_train2017.json
                instances_val2017.json

    __getitem__ returns:
        image:  torch.uint8 tensor of shape (3, H, W)
        target: dict with keys:
            boxes   -> FloatTensor [N, 4] in XYXY (abs pixel coords)
            labels  -> LongTensor  [N]
            image_id-> int

    Example:
        .. code-block:: python

            from pathlib import Path
            from prt_datasets.coco import COCODataset

            # Choose a local data root (create if missing)
            root = Path("~/data/prt").expanduser()

            # 1) Download
            COCODataset.download(
                root=root,
                splits=("val",),                # pick the splits you need: ("train","val","test")
                download_images=True,
                download_annotations=True,
            )

            # 2) Construct the dataset
            ds = COCODataset(root=root, split="val")

            # 3) Grab the first sample and display the image
            img, target = ds[0]
            print(img.shape, img.dtype)        # e.g., torch.Size([3, H, W]) torch.uint8
            print(target["image_id"], target["boxes"].shape)

            # Display with PIL (no need for matplotlib)
            from PIL import Image
            Image.fromarray(img.permute(1, 2, 0).numpy()).show()

            # (Optional) If you prefer matplotlib and want to draw boxes:
            # import matplotlib.pyplot as plt
            # import matplotlib.patches as patches
            # fig, ax = plt.subplots()
            # ax.imshow(img.permute(1, 2, 0).numpy())
            # for (x1, y1, x2, y2) in target["boxes"].tolist():
            #     rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, linewidth=1)
            #     ax.add_patch(rect)
            # ax.axis("off"); plt.show()              

    Args:
        root (Path): Root directory of the dataset
        split (str): One of {"train","val","test"}
        transforms (callable, optional): A function/transform that takes input sample and its target
        categories (list, optional): If provided, only load these category ids
        skip_empty (bool): If True, skip images without annotations (train/val only)

      
    """

    # -----------------------------
    # Construction / indexing
    # -----------------------------
    def __init__(
        self,
        root: Path | None,
        split: str = "train",
        transforms=None,
        categories: Optional[Sequence[int]] = None,  # filter to these category ids (optional)
        skip_empty: bool = True,                    # if True, drop images with no anns
    ):
        assert split in {"train", "val", "test"}, f"Unsupported split {split!r}"

        self.root = utils.resolve_root(root)
        self.split = split
        self.transforms = transforms
        self.year = int(2017)
        self.categories_filter = set(categories) if categories else None
        self.skip_empty = bool(skip_empty)

        base = Path(self.root) / "coco" / str(self.year)
        self._img_dir = base / "images" / f"{split}{self.year}"
        ann_file = (base / "annotations" / f"instances_{split}{self.year}.json") if split != "test" else None

        if split != "test":
            if not ann_file or not ann_file.exists():
                raise FileNotFoundError(
                    f"Missing annotations: {ann_file}. "
                    f"Run {type(self).__name__}.download(root={self.root!s}, year={self.year})"
                )
            with ann_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self._images_by_id = {img["id"]: img for img in data["images"]}
            self._cats_by_id = {c["id"]: c for c in data["categories"]}
            anns_by_img: Dict[int, List[dict]] = {}
            for ann in data["annotations"]:
                if self.categories_filter and ann["category_id"] not in self.categories_filter:
                    continue
                anns_by_img.setdefault(ann["image_id"], []).append(ann)

            # Build an index of valid image_ids honoring skip_empty
            image_ids = []
            for img_id, img in self._images_by_id.items():
                anns = anns_by_img.get(img_id, [])
                if self.skip_empty and len(anns) == 0:
                    continue
                image_ids.append(img_id)

            self._anns_by_img = anns_by_img
            self._image_ids: List[int] = image_ids
        else:
            # test split has no annotations
            if not self._img_dir.exists():
                raise FileNotFoundError(
                    f"Missing images dir: {self._img_dir}. "
                    f"Run {type(self).__name__}.download(root={self.root!s}, year={self.year}, splits=('test',))"
                )
            self._images_by_id = {}
            self._cats_by_id = {}
            # Use directory listing order as index for test
            self._image_paths = sorted(str(p) for p in self._img_dir.glob("*.jpg"))
            self._image_ids = list(range(len(self._image_paths)))
            self._anns_by_img = {}

    def __len__(self) -> int:
        return len(self._image_ids)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict[str, Any]]:
        if self.split == "test":
            img_path = self._image_paths[idx]
            image_id = idx
            boxes = torch.zeros((0, 4), dtype=torch.float32)
            labels = torch.zeros((0,), dtype=torch.int64)
        else:
            image_id = self._image_ids[idx]
            img_info = self._images_by_id[image_id]
            img_path = str(self._img_dir / img_info["file_name"])
            anns = self._anns_by_img.get(image_id, [])

            # COCO bbox is [x,y,w,h] in absolute pixels; convert to XYXY
            if len(anns) > 0:
                xyxy = []
                labels_list = []
                for a in anns:
                    x, y, w, h = a["bbox"]
                    xyxy.append([x, y, x + w, y + h])
                    labels_list.append(int(a["category_id"]))
                boxes = torch.tensor(xyxy, dtype=torch.float32)
                labels = torch.tensor(labels_list, dtype=torch.int64)
            else:
                boxes = torch.zeros((0, 4), dtype=torch.float32)
                labels = torch.zeros((0,), dtype=torch.int64)

        # Load image (RGB) -> torch.uint8 (C,H,W)
        with Image.open(img_path) as im:
            im = im.convert("RGB")
            np_img = np.array(im, dtype=np.uint8)          # (H, W, 3) uint8
            img = torch.from_numpy(np_img).permute(2, 0, 1).contiguous()  # (3, H, W) uint8

        target: Dict[str, Any] = {
            "boxes": boxes,
            "labels": labels,
            "image_id": image_id,
        }

        if self.transforms is not None:
            # Expect transforms to accept (img, target) and return (img, target)
            img, target = self.transforms(img, target)

        return img, target

    @classmethod
    def download(
        cls,
        root: Path | None,
        splits: Sequence[str] = ("train", "val", "test"),
        download_images: bool = True,
        download_annotations: bool = True,
        force: bool = False,
        checksums: Optional[Dict[str, str]] = None,  # filename -> sha256 hex
    ) -> Path:
        """
        Download and extract COCO 2017 images/annotations from official URLs.
        Only extracts if extraction hasn't already been done (unless force=True).
        """
        year = 2017
        root = utils.resolve_root(root, create=True)
        base = root / "coco" / str(year)
        img_dir = base / "images"
        ann_dir = base / "annotations"
        img_dir.mkdir(parents=True, exist_ok=True)
        ann_dir.mkdir(parents=True, exist_ok=True)

        def official_url(kind: str, split: str) -> str:
            if kind == "images":
                return f"http://images.cocodataset.org/zips/{split}{year}.zip"
            elif kind == "annotations":
                return f"http://images.cocodataset.org/annotations/annotations_trainval{year}.zip"
            raise ValueError(kind)

        # ---- helpers to detect prior extraction ----
        def _images_already_extracted(split: str) -> bool:
            d = img_dir / f"{split}{year}"
            # consider "done" if the directory exists and is non-empty
            return d.is_dir() and any(d.iterdir())

        def _annotations_already_extracted() -> bool:
            # we only require the detection JSONs to exist
            need = [
                ann_dir / f"instances_train{year}.json",
                ann_dir / f"instances_val{year}.json",
            ]
            return all(p.exists() for p in need)

        # ---- build plan of artifacts: (filename, kind) ----
        artifacts: List[Tuple[str, str]] = []
        if download_images:
            for s in splits:
                if s in {"train", "val", "test"}:
                    artifacts.append((f"{s}{year}.zip", "images"))
        if download_annotations and any(s in {"train", "val"} for s in splits):
            artifacts.append((f"annotations_trainval{year}.zip", "annotations"))

        for filename, kind in artifacts:
            # Early skip: if extracted content is already present and not forcing,
            # we don't need to download or extract again.
            if not force:
                if kind == "images":
                    split = filename.replace(".zip", "").replace(str(year), "")
                    if _images_already_extracted(split):
                        continue
                else:  # annotations
                    if _annotations_already_extracted():
                        continue

            # Determine destination zip path
            target_dir = img_dir if kind == "images" else ann_dir
            dst_zip = target_dir / filename

            # Handle existing zips
            if force and dst_zip.exists():
                dst_zip.unlink()

            # Download if needed (skip if zip exists and passes checksum)
            need_download = True
            if dst_zip.exists() and not force:
                if checksums and filename in checksums:
                    if utils.file_sha256(dst_zip) == checksums[filename]:
                        need_download = False
                    else:
                        dst_zip.unlink(missing_ok=True)
                        need_download = True
                else:
                    need_download = False

            if need_download:
                if kind == "images":
                    split = filename.replace(".zip", "").replace(str(year), "")
                    url = official_url("images", split)
                else:
                    url = official_url("annotations", "")
                downloaded = utils.download_from_url(url, str(target_dir))
                if Path(downloaded) != dst_zip:
                    Path(downloaded).replace(dst_zip)

                if checksums and filename in checksums:
                    got = utils.file_sha256(dst_zip)
                    want = checksums[filename]
                    if got != want:
                        os.remove(dst_zip)
                        raise RuntimeError(
                            f"Checksum mismatch for {filename}: got {got}, want {want}"
                        )

            # Extract only if needed (or forcing)
            need_extract = force
            if not need_extract:
                if kind == "images":
                    split = filename.replace(".zip", "").replace(str(year), "")
                    need_extract = not _images_already_extracted(split)
                else:
                    need_extract = not _annotations_already_extracted()

            if need_extract:
                utils.extract_file(str(dst_zip), extract_to=str(target_dir), delete_zip=True)

            # Always flatten the nested `annotations/` dir if it exists
            if kind == "annotations":
                nested = target_dir / "annotations"
                if nested.exists() and nested.is_dir():
                    for p in nested.iterdir():
                        shutil.move(str(p), str(target_dir / p.name))
                    try:
                        nested.rmdir()
                    except OSError:
                        pass

        # Ensure split folders exist (created by extraction, but make sure)
        for s in splits:
            if s in {"train", "val", "test"} and download_images:
                (img_dir / f"{s}{year}").mkdir(parents=True, exist_ok=True)

        return base

if __name__ == "__main__":
        from pathlib import Path

        # 1) Download (one-time, idempotent). You can pass mirrors=[...] if you host a mirror.
        COCODataset.download(
            root=None,
            splits=("val",),                # pick the splits you need: ("train","val","test")
            download_images=True,
            download_annotations=True,
        )

        # 2) Construct the dataset
        ds = COCODataset(root=None, split="val")

        # 3) Grab the first sample and display the image
        img, target = ds[0]
        print(img.shape, img.dtype)        # e.g., torch.Size([3, H, W]) torch.uint8
        print(target["image_id"], target["boxes"].shape)

        # Display with PIL (no need for matplotlib)
        from PIL import Image
        Image.fromarray(img.permute(1, 2, 0).numpy()).show()

        # (Optional) If you prefer matplotlib and want to draw boxes:
        # import matplotlib.pyplot as plt
        # import matplotlib.patches as patches
        # fig, ax = plt.subplots()
        # ax.imshow(img.permute(1, 2, 0).numpy())
        # for (x1, y1, x2, y2) in target["boxes"].tolist():
        #     rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, linewidth=1)
        #     ax.add_patch(rect)
        # ax.axis("off"); plt.show()     