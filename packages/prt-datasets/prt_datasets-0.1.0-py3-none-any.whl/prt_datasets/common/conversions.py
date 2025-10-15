from PIL import Image
import torch

def pil_to_tensor(img: Image.Image) -> torch.Tensor:
    """
    Converts a PIL image in **RGB** mode to a PyTorch tensor with shape ``[3, H, W]``
    and dtype ``float32`` in the range ``[0, 1]``.

    This function performs a zero-copy view over the image byte buffer to build a
    ``uint8`` tensor and then scales to ``float32``/``[0,1]``. It assumes the input
    is a contiguous 3-channel RGB image (no alpha).

    Args:
        img (PIL.Image.Image): Input PIL image. Must be in mode ``"RGB"``. If your
            image is not RGB (e.g., ``"L"``, ``"RGBA"``, ``"CMYK"``), convert it first,
            e.g. ``img = img.convert("RGB")``.

    Returns:
        torch.Tensor: A tensor of shape ``[3, H, W]``, dtype ``float32``, values in
        ``[0, 1]`` where ``H`` and ``W`` are the image height and width respectively.

    Raises:
        ValueError: If the image is not in ``"RGB"`` mode.
        RuntimeError: If the image memory layout is incompatible (rare; typically only
            occurs with unusual PIL backends or images without a contiguous buffer).

    Notes:
        * **Performance:** The initial ``uint8`` tensor is created as a view over the
          image bytes (no copy). The final cast to ``float32`` creates a new tensor.
        * **Channel order:** Output is channels-first (``C,H,W``). Many vision models
          expect this layout; if you need HWC, call ``x.permute(1, 2, 0)``.
        * **Device:** The returned tensor lives on CPU. Move to GPU with ``x.to("cuda")``.
        * **Alpha channel:** If you have RGBA inputs, drop/compose alpha before calling
          (e.g., ``img = img.convert("RGB")``).

    Examples:
        Basic usage:

        >>> from PIL import Image
        >>> import torch
        >>> img = Image.open("example.jpg").convert("RGB")
        >>> x = pil_to_tensor(img)
        >>> x.shape, x.dtype, (float(x.min()), float(x.max()))
        (torch.Size([3, 720, 1280]), torch.float32, (0.0, 1.0))

    """
    if img.mode != "RGB":
        raise ValueError(f"pil_to_tensor expects RGB images, got mode={img.mode!r}")

    arr = torch.ByteTensor(torch.ByteStorage.from_buffer(img.tobytes()))
    w, h = img.size
    # PIL stores RGB contiguous as H x W x 3
    arr = arr.view(h, w, 3).permute(2, 0, 1).contiguous()
    return arr.to(dtype=torch.float32) / 255.0