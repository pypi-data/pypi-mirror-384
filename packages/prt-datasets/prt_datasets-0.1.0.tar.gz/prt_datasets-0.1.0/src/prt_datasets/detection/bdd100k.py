"""
BDD100K detection dataset
"""
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import torch
from PIL import Image
from prt_datasets.common.conversions import pil_to_tensor
from prt_datasets.base import Dataset
import prt_datasets.common.utils as utils


class BDD100KDataset(Dataset):
    """
    BDD100K detection dataset loader (images + 2D boxes).

    .. image:: /_static/bdd100k.gif
        :alt: BDD100K Dataset
        :width: 100%
        :align: center

    BDD100K is a large-scale, real-world driving dataset collected from dashcams, designed for many perception tasks. It contains 100K videos (with 1280×720 frames) and curated 100K images, with annotations for 2D object detection (10 traffic-related classes), semantic/instance/panoptic segmentation, lane markings, drivable area, and multi-object tracking (MOT/MOTS). The data span diverse cities, weather, and day/night conditions, making it a popular benchmark for robust, traffic-scene models.

    Object Classes:
        - pedestrian
        - rider
        - car
        - truck
        - bus
        - train
        - motorcycle
        - bicycle
        - traffic light
        - traffic sign

    __getitem__ returns:
      - image: torch.float32 tensor of shape [3,H,W] in [0,1] 
      - target: dict with keys:
          "boxes":  FloatTensor [N, 4] in XYXY(x1,y1,x2,y2),
          "labels": LongTensor  [N], 
          "image_id": int,

    Example:
        .. code-block:: python
            from prt_datasets import BDD100KDataset

            # 1) Download (if not already done)
            root = BDD100KDataset.download()

            # 2) Create dataset
            dataset = BDD100KDataset(root=root, split="train")

            # 3) Access samples
            img, target = dataset[0]  # get first sample
            print(img.shape)          # e.g. torch.Size([3, 720, 1280])
            print(target["image_id"], target["boxes"].shape, target["labels"].shape)

    Args:
        root (Path): Dataset root folder (see layout above).
        split: "train" | "val" | "test".
        transform: Optional callable applied to the *image* (after to_tensor if to_tensor=True).
        target_transform: Optional callable applied to the *target* dict.

    References:
        - https://github.com/bdd100k/bdd100k
        - https://arxiv.org/abs/1805.04687
    """
    # Default BDD100K det_20 classes in a common order (10 classes)
    CLASS_LABELS = {
        'pedestrian': 0,
        'rider': 1,
        'car': 2,
        'truck': 3,
        'bus': 4,
        'train': 5,
        'motorcycle': 6,
        'bicycle': 7,
        'traffic light': 8,
        'traffic sign': 9,
    }

    def __init__(
        self,
        root: Path | None,
        split: str = "train",
        transform: Optional[Callable] = None,
        target_transform: Optional[Callable] = None,
    ):
        assert split in ("train", "val", "test"), "split must be 'train', 'val' or 'test'"

        self.root = utils.resolve_root(root, create=False)
        self.base = self.root / "bdd100k"
        self.split = split
        self.transform = transform
        self.target_transform = target_transform

        # Create file paths
        self.images_dir = self.base / "images" / "100k" / self.split
        self.labels_file = self.base / "labels" / "det_20" / f"det_{self.split}.json"
        if not self.images_dir.exists():
            raise FileNotFoundError(f"BDD100K images folder not found: {self.images_dir}")
        if not self.labels_file.exists():
            raise FileNotFoundError(f"BDD100K labels file not found: {self.labels_file}")

        # Build index
        self.data = self._load_bdd_det_json(self.labels_file, self.images_dir)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[Any, Dict[str, Any]]:
        rec = self.data[idx]
        img_path = Path(rec["path"])

        # Load image
        img = Image.open(img_path).convert("RGB")
        
        # PIL -> Tensor [C,H,W] in [0,1]
        img = pil_to_tensor(img)

        # Apply transforms
        if self.transform is not None:
            img = self.transform(img)

        # Build target
        boxes = torch.tensor(rec["boxes"], dtype=torch.float32) if rec["boxes"] else torch.zeros((0, 4), dtype=torch.float32)
        labels = torch.tensor(rec["labels"], dtype=torch.long) if rec["labels"] else torch.zeros((0,), dtype=torch.long)
        target: Dict[str, Any] = {
            "boxes": boxes,
            "labels": labels,
            "image_id": rec["image_id"],
        }

        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

    def _load_bdd_det_json(self, labels_path: Path, images_dir: Path) -> List[Dict[str, Any]]:
        """
        Parse BDD100K det_20 JSON (train/val). It is a JSON array where each entry looks like:
            {
              "name": "000123.jpg",
              "labels": [
                 {"category": "car", "box2d": {"x1":..., "y1":..., "x2":..., "y2":...}},
                 ...
              ]
            }
        """
        # Read in the label json file
        with open(labels_path, "r", encoding="utf-8") as f:
            data = json.load(f)


        samples: List[Dict[str, Any]] = []
        for i, item in enumerate(data):
            name = item.get("name")
            # If there is no "name" field, skip this entry
            if name is None:
                continue

            # Construct the full image path
            img_path = images_dir / name
            # Double check the image file exists or skip this entry
            if not img_path.exists():
                continue

            # Parse boxes and labels
            boxes, labels = [], []
            for lab in item.get("labels", []):
                # Extract the class label (category) and bounding box (box2d)
                cat = lab.get("category")
                b = lab.get("box2d")

                # Skip if either is missing
                if cat is None or b is None:
                    continue

                # Check if this is a known class and skip unknown classes
                if cat not in self.CLASS_LABELS.keys():
                    continue

                # Extract box coordinates and validate
                x1, y1 = float(b["x1"]), float(b["y1"])
                x2, y2 = float(b["x2"]), float(b["y2"])
                if x2 <= x1 or y2 <= y1:
                    continue

                boxes.append([x1, y1, x2, y2])
                labels.append(self.CLASS_LABELS[cat])

            samples.append({
                "path": str(img_path),
                "boxes": boxes,
                "labels": labels,
                "image_id": i,
            })

        return samples

    @classmethod
    def download(
        cls, 
        root: Path | None = None, 
        force: bool = False,
        ) -> Path:
        """
        BDD100K is typically downloaded manually (license). This method just
        validates the expected layout and guides you.

        Returns:
            Path to the root if structure looks OK, otherwise raises with instructions.
        """
        SOURCE_URL = "https://dl.cv.ethz.ch/bdd100k/data/"
        train_file = SOURCE_URL + "100k_images_train.zip"
        val_file = SOURCE_URL + "100k_images_val.zip"
        test_file = SOURCE_URL + "100k_images_test.zip"
        label_file = SOURCE_URL + "bdd100k_det_20_labels_trainval.zip"

        root = utils.resolve_root(root, create=True)
        base = root / "bdd100k"
        train_images_dir = base / "images" / "100k" / "train"
        val_images_dir = base / "images" / "100k" / "val"
        test_images_dir = base / "images" / "100k" / "test"
        labels_dir = base / "labels" / "det_20"

        def download_if_missing(dir: Path, file: Path, root: Path):
            # Check if directory does not exist or is empty
            if not dir.is_dir() or not any(dir.iterdir()) or force:
                zip_file = utils.download_from_url(str(file), folder=str(root))
                utils.extract_file(zip_file_path=zip_file, extract_to=str(root), delete_zip=True)

        download_if_missing(train_images_dir, train_file, base)
        download_if_missing(val_images_dir, val_file, root)
        download_if_missing(test_images_dir, test_file, root)
        download_if_missing(labels_dir, label_file, root)

        return base
    
if __name__ == "__main__":
    # Simple test / usage example
    dataset = BDD100KDataset.download()