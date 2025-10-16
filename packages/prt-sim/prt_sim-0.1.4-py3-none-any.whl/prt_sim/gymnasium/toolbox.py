import torch
import torch.nn.functional as F
import numpy as np
from typing import List
from itertools import accumulate

# scikit-image
from skimage import exposure, color
from skimage.filters import gaussian, median, sobel, unsharp_mask
from skimage.restoration import denoise_bilateral, denoise_nl_means
from skimage.morphology import disk

# Toolbox Algorithms
def exposure(image: torch.Tensor, p: torch.Tensor)-> torch.Tensor:
    """
    Exposure compensation.

    Args:
        image: Tensor of shape (3, H, W). Values typically in [0, 1]. dtype float.
        p: Scalar or (B,) tensor with values in [-3.5, 3.5]
    Returns:
        Tensor of shape (B, 3, H, W), same dtype/device as img
    """
    if not -3.5 <= p <= 3.5:
        raise ValueError("p should be in the range [-3.5, 3.5]")
    
    return image * 2**p

def white_balance(
    image: torch.Tensor,
    pr: torch.Tensor,
    pg: torch.Tensor,
    pb: torch.Tensor,
) -> torch.Tensor:
    """
    Improved white balance with per-channel params and luminance normalization.

    Args:
        img: Tensor of shape (B, 3, H, W). Values typically in [0, 1]. dtype float.
        pr, pg, pb: Per-image/channel parameters [-0.5, 0.5]. Scalar tensor

    Returns:
        Tensor of shape (B, 3, H, W), same dtype/device as img.
    """
    eps = 1e-5
    B, C, H, W = image.shape
    device, dtype = image.device, image.dtype

    def to_batch(p: torch.Tensor) -> torch.Tensor:
        p = torch.as_tensor(p, device=device, dtype=dtype)
        if p.ndim == 0:            # scalar -> (B,)
            p = p.expand(B)
        elif p.ndim == 1:
            if p.shape[0] != B:
                raise ValueError(f"Param length {p.shape[0]} != batch size {B}")
        else:
            raise ValueError("Params must be scalar or (B,).")
        return p

    pr = to_batch(pr)
    pg = to_batch(pg)
    pb = to_batch(pb)

    gains = torch.exp(torch.stack([pr, pg, pb], dim=1))        # (B, 3)
    denom = (0.27 * gains[:, 0] + 0.67 * gains[:, 1] + 0.06 * gains[:, 2]).clamp_min(eps)  # (B,)
    gains = (gains / denom[:, None]).view(B, C, 1, 1)          # (B, 3, 1, 1)

    return image * gains

def gamma_correction(image: torch.Tensor, gamma: torch.Tensor) -> torch.Tensor:
    """
    Gamma correction.
    
    Args:
        image: Tensor of shape (B, 3, H, W). Values typically in [0, 1]. dtype float.
        gamma: Scalar or (B,) tensor with values in [0.3333, 3.0]
    Returns:
        Tensor of shape (B, 3, H, W), same dtype/device as img.
    """
    if not 0.3333 <= gamma <= 3.0:
        raise ValueError("gamma should be in the range [0.3333, 3.0]")
    return torch.pow(image, gamma)

def sharpen_blur(
    image: torch.Tensor,
    p: torch.Tensor | float,
) -> torch.Tensor:
    """
    Sharpen/Blur module.

    Implements:
        I_out = p * I + (1 - p) * I_blurred,  with  p in [0, 2]

    where I_blurred is computed using the kernel (1/13) * [[1,1,1],[1,5,1],[1,1,1]].

    Args:
        image: (B, C, H, W) tensor (float). Any value range. Gradient-safe.
        p:     Scalar float or tensor broadcastable to (B, 1, 1, 1).
               p=1 -> identity; p<1 -> blur; p>1 -> sharpen (unsharp mask).

    Returns:
        (B, C, H, W) tensor, same dtype/device as image.
    """
    if image.ndim != 4:
        raise ValueError(f"image must be (B,C,H,W), got {tuple(image.shape)}")

    B, C, H, W = image.shape
    device, dtype = image.device, image.dtype

    # Prepare p to broadcast over (B, C, H, W)
    if not torch.is_tensor(p):
        p = torch.tensor(p, device=device, dtype=dtype)
    else:
        p = p.to(device=device, dtype=dtype)
    # If p is (B,), make it (B,1,1,1)
    if p.ndim == 1 and p.shape[0] == B:
        p = p.view(B, 1, 1, 1)
    # If scalar, expand later by broadcasting

    # Build blur kernel (depthwise): same kernel per channel
    base_kernel = torch.tensor([[1, 1, 1],
                                [1, 5, 1],
                                [1, 1, 1]], device=device, dtype=dtype) / 13.0
    weight = base_kernel.view(1, 1, 3, 3).expand(C, 1, 3, 3)  # (C,1,3,3) depthwise

    # Replicate pad to avoid dark borders, then depthwise conv
    x_pad = F.pad(image, (1, 1, 1, 1), mode="replicate")  # (B,C,H+2,W+2)
    I_blurred = F.conv2d(x_pad, weight=weight, bias=None, stride=1, padding=0, groups=C)

    # Combine per formula
    I_out = p * image + (1 - p) * I_blurred

    I_out = I_out.clamp(0, 1)

    return I_out

# -------------------------
# Helpers
# -------------------------

def _check_image(image: torch.Tensor):
    if image.ndim != 4 or image.shape[1] != 3:
        raise ValueError(f"image must be (B,3,H,W); got {tuple(image.shape)}")
    if image.dtype not in (torch.float16, torch.float32, torch.float64):
        raise ValueError("image dtype must be float")
    if torch.any(image.isnan()):
        raise ValueError("image contains NaNs")

def _to_numpy_bhwc(image: torch.Tensor) -> np.ndarray:
    # (B,3,H,W) -> (B,H,W,3), float64 for skimage
    return image.detach().cpu().permute(0, 2, 3, 1).float().numpy()

def _to_torch_bchw(arr: np.ndarray, like: torch.Tensor) -> torch.Tensor:
    # (B,H,W,3) -> (B,3,H,W)
    out = torch.from_numpy(arr).permute(0, 3, 1, 2)
    return out.to(device=like.device, dtype=like.dtype)

def _clip01(x: np.ndarray) -> np.ndarray:
    return np.clip(x, 0.0, 1.0)

def _apply_per_batch(img_bhwc: np.ndarray, fn):
    # fn: (H,W,3) -> (H,W,3)
    B = img_bhwc.shape[0]
    out = []
    for b in range(B):
        out.append(fn(img_bhwc[b]))
    return np.stack(out, axis=0)

# -------------------------
# New algorithms
# -------------------------

def gaussian_blur(image: torch.Tensor, sigma: float) -> torch.Tensor:
    """
    Gaussian blur with std-dev 'sigma' (pixels). sigma in [0, 5].
    """
    _check_image(image)
    if not (0.0 <= float(sigma) <= 5.0):
        raise ValueError("sigma ∈ [0, 5]")

    x = _to_numpy_bhwc(image)
    def fn(frame):
        return _clip01(gaussian(frame, sigma=float(sigma), channel_axis=-1, preserve_range=True))
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

def bilateral_denoise(image: torch.Tensor, sigma_color: float, sigma_spatial: float) -> torch.Tensor:
    """
    Bilateral filter (edge-preserving).
    sigma_color ∈ [0, 0.2] (range in [0,1] space), sigma_spatial ∈ [1, 5] (pixels).
    """
    _check_image(image)
    if not (0.0 <= float(sigma_color) <= 0.2):
        raise ValueError("sigma_color ∈ [0, 0.2]")
    if not (1.0 <= float(sigma_spatial) <= 5.0):
        raise ValueError("sigma_spatial ∈ [1, 5]")

    x = _to_numpy_bhwc(image)
    def fn(frame):
        out = denoise_bilateral(
            frame,
            sigma_color=float(sigma_color),
            sigma_spatial=float(sigma_spatial),
            channel_axis=-1
        )
        return _clip01(out)
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

def nlm_denoise(image: torch.Tensor, h: float, patch_size: int = 5, patch_distance: int = 6, fast_mode: bool = True) -> torch.Tensor:
    """
    Non-Local Means denoising.
    h ∈ [0, 0.2], patch_size ∈ {3..7}, patch_distance ∈ {3..10}.
    """
    _check_image(image)
    if not (0.0 <= float(h) <= 0.2):
        raise ValueError("h ∈ [0, 0.2]")
    if not (3 <= int(patch_size) <= 7):
        raise ValueError("patch_size ∈ [3, 7]")
    if not (3 <= int(patch_distance) <= 10):
        raise ValueError("patch_distance ∈ [3, 10]")

    x = _to_numpy_bhwc(image)
    def fn(frame):
        out = denoise_nl_means(
            frame,
            h=float(h),
            patch_size=int(patch_size),
            patch_distance=int(patch_distance),
            fast_mode=bool(fast_mode),
            channel_axis=-1
        )
        return _clip01(out)
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

def median_blur(image: torch.Tensor, radius: int) -> torch.Tensor:
    """
    Median blur with circular footprint radius ∈ {1..5}. Applied per-channel.
    """
    _check_image(image)
    if not (1 <= int(radius) <= 5):
        raise ValueError("radius ∈ [1, 5]")

    x = _to_numpy_bhwc(image)
    fp = disk(int(radius))
    def fn(frame):
        # per-channel median
        out = np.empty_like(frame)
        for c in range(3):
            out[..., c] = median(frame[..., c], footprint=fp, mode="reflect")
        return _clip01(out)
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

def clahe_luma(image: torch.Tensor, clip_limit: float = 0.01, tile_grid_size: int = 8) -> torch.Tensor:
    """
    CLAHE on luminance (HSV V-channel). clip_limit ∈ [0.001, 0.1], tile_grid_size ∈ [4, 16].
    """
    _check_image(image)
    if not (0.001 <= float(clip_limit) <= 0.1):
        raise ValueError("clip_limit ∈ [0.001, 0.1]")
    if not (4 <= int(tile_grid_size) <= 16):
        raise ValueError("tile_grid_size ∈ [4, 16]")

    x = _to_numpy_bhwc(image)
    def fn(frame):
        hsv = color.rgb2hsv(frame)
        hsv[..., 2] = exposure.equalize_adapthist(
            hsv[..., 2],
            clip_limit=float(clip_limit),
            nbins=256,
            kernel_size=int(tile_grid_size)
        )
        out = color.hsv2rgb(hsv)
        return _clip01(out)
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

def hist_eq_luma(image: torch.Tensor) -> torch.Tensor:
    """
    Global histogram equalization on luminance (HSV V-channel).
    """
    _check_image(image)
    x = _to_numpy_bhwc(image)
    def fn(frame):
        hsv = color.rgb2hsv(frame)
        hsv[..., 2] = exposure.equalize_hist(hsv[..., 2])
        out = color.hsv2rgb(hsv)
        return _clip01(out)
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

def saturation(image: torch.Tensor, s: float) -> torch.Tensor:
    """
    Saturation scale: S' = clip((1+s) * S), with s ∈ [-1, 1], where s=-1 -> grayscale, s=0 -> no change.
    """
    _check_image(image)
    if not (-1.0 <= float(s) <= 1.0):
        raise ValueError("s ∈ [-1, 1]")

    x = _to_numpy_bhwc(image)
    scale = 1.0 + float(s)
    def fn(frame):
        hsv = color.rgb2hsv(frame)
        hsv[..., 1] = np.clip(hsv[..., 1] * scale, 0.0, 1.0)
        out = color.hsv2rgb(hsv)
        return _clip01(out)
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

def hue_shift(image: torch.Tensor, degrees: float) -> torch.Tensor:
    """
    Hue shift in degrees, degrees ∈ [-180, 180].
    """
    _check_image(image)
    if not (-180.0 <= float(degrees) <= 180.0):
        raise ValueError("degrees ∈ [-180, 180]")

    shift = float(degrees) / 360.0
    x = _to_numpy_bhwc(image)
    def fn(frame):
        hsv = color.rgb2hsv(frame)
        hsv[..., 0] = (hsv[..., 0] + shift) % 1.0
        out = color.hsv2rgb(hsv)
        return _clip01(out)
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

def linear_contrast(image: torch.Tensor, alpha: float) -> torch.Tensor:
    """
    Linear contrast around 0.5: y = (x - 0.5)*alpha + 0.5, alpha ∈ [0, 3].
    alpha=1 no change; alpha<1 lowers contrast; alpha>1 increases.
    """
    _check_image(image)
    if not (0.0 <= float(alpha) <= 3.0):
        raise ValueError("alpha ∈ [0, 3]")
    x = _to_numpy_bhwc(image)
    y = np.clip((x - 0.5) * float(alpha) + 0.5, 0.0, 1.0)
    return _to_torch_bchw(y, image)

def sobel_edges_blend(image: torch.Tensor, alpha: float = 0.5) -> torch.Tensor:
    """
    Blend Sobel edges (on luminance) with the original image:
    out = (1 - alpha) * image + alpha * edges_gray
    alpha ∈ [0, 1]
    """
    _check_image(image)
    if not (0.0 <= float(alpha) <= 1.0):
        raise ValueError("alpha ∈ [0, 1]")

    x = _to_numpy_bhwc(image)
    a = float(alpha)
    def fn(frame):
        gray = color.rgb2gray(frame)  # (H,W)
        e = sobel(gray)               # normalized to [0,1] (approx)
        e3 = np.repeat(e[..., None], 3, axis=-1)
        out = (1.0 - a) * frame + a * e3
        return _clip01(out)
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

def skimage_unsharp_mask(image: torch.Tensor, radius: float = 1.0, amount: float = 1.0) -> torch.Tensor:
    """
    Unsharp masking from skimage. radius ∈ [0.5, 5], amount ∈ [0, 3].
    """
    _check_image(image)
    if not (0.5 <= float(radius) <= 5.0):
        raise ValueError("radius ∈ [0.5, 5]")
    if not (0.0 <= float(amount) <= 3.0):
        raise ValueError("amount ∈ [0, 3]")

    x = _to_numpy_bhwc(image)
    def fn(frame):
        out = unsharp_mask(frame, radius=float(radius), amount=float(amount), channel_axis=-1, preserve_range=True)
        return _clip01(out)
    y = _apply_per_batch(x, fn)
    return _to_torch_bchw(y, image)

# Name, Parameters with ranges
ALGORITHM_LIST = [
    (lambda img: img, {}),
    (exposure, {"p": (-3.5, 3.5)}),
    (white_balance, {"pr": (-0.5, 0.5), "pg": (-0.5, 0.5), "pb": (-0.5, 0.5)}),
    (gamma_correction, {"gamma": (0.3333, 3.0)}),
    # ("sharpen_blur", {"p": (0.0, 2.0)}),
    # ("gaussian_blur", {"sigma": (0.0, 5.0)}),
    # ("bilateral_denoise", {"sigma_color": (0.0, 0.2), "sigma_spatial": (1.0, 5.0)}),
    # ("nlm_denoise", {"h": (0.0, 0.2), "patch_size": (3, 7), "patch_distance": (3, 10)}),
    # ("median_blur", {"radius": (1, 5)}),
    # ("clahe_luma", {"clip_limit": (0.001, 0.1), "tile_grid_size": (4, 16)}),
    # ("hist_eq_luma", {}),
    # ("saturation", {"s": (-1.0, 1.0)}),
    # ("hue_shift", {"degrees": (-180.0, 180.0)}),
    # ("linear_contrast", {"alpha": (0.0, 3.0)}),
    # ("sobel_edges_blend", {"alpha": (0.0, 1.0)}),
    # ("skimage_unsharp_mask", {"radius": (0.5, 5.0), "amount": (0.0, 3.0)}),
]

class Toolbox:
    """
    A collection of image processing algorithms with parameter ranges.

    Each algorithm is a function that takes an image tensor and parameters, and returns a processed image tensor.
    """
    def __init__(self, algorithm_list: List = ALGORITHM_LIST) -> None:
        self.algorithm_list = algorithm_list
        self.parameter_list = [len(params) for _, params in self.algorithm_list]
        self.parameter_indices = [slice(s, s+n) 
                         for s, n in zip([0, *accumulate(self.parameter_list)][:-1],
                                         self.parameter_list)]
        self.parameter_mins = torch.tensor(
            [lo for _, params in self.algorithm_list for (lo, hi) in params.values()],
            dtype=torch.float32,
        )
        self.parameter_maxs = torch.tensor(
            [hi for _, params in self.algorithm_list for (lo, hi) in params.values()],
            dtype=torch.float32,
        )

    def apply_algorithm(self, choice: torch.Tensor, params: torch.Tensor, image: torch.Tensor) -> torch.Tensor:
        """
        Apply the selected algorithm with given parameters to the image.

        Args:
            choice: Tensor of shape (,) with integer in [0, num_algorithms-1]
            params: Tensor of shape (num_parameters,) with values in [0, 1]
            image:  Tensor of shape (B, 3, H, W) with values in [0, 1]

        Returns:
            Processed image tensor of shape (B, 3, H, W) with values in [0, 1]
        """
        # Get the algorithm choice
        alg, _ = self.algorithm_list[int(choice)]

        # Scale the parameters from [0, 1] to their actual ranges
        params = (self.parameter_maxs - self.parameter_mins) * params + self.parameter_mins

        # Extract the masked parameters
        params = params[self.parameter_indices[int(choice)]]

        return alg(image, *params)
    
    def get_num_algorithms(self) -> int:
        return len(self.algorithm_list)
    
    def get_num_parameters(self) -> int:
        return sum(self.parameter_list)