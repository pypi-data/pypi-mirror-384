from saber.filters.downsample import FourierRescale2D
from saber.segmenters.base import saber2Dsegmenter
import torch


class cryoMicroSegmenter(saber2Dsegmenter):
    def __init__(self,
        sam2_cfg: str = 'base', 
        deviceID: int = 0,
        classifier = None,
        target_class: int = 1,
        min_mask_area: int = 50,
        window_size: int = 256,
        overlap_ratio: float = 0.25,
    ):
        """
        Class for Segmenting Micrographs
        """
        super().__init__(sam2_cfg, deviceID, classifier, target_class, min_mask_area, window_size, overlap_ratio)

        # Max pixels for single inference
        self.max_pixels = 1280

    @torch.inference_mode()
    def segment(self,
        image0,
        display_image: bool = True,
        use_sliding_window: bool = False
    ):
        """
        Segment image using sliding window approach
        
        Args:
            image0: Input image
            display_image: Whether to display the result
            use_sliding_window: Whether to use sliding window (True) or single inference (False)
        """

        # Store the Original Image
        self.image0 = image0
        (nx, ny) = image0.shape

        # (Optional)Fourier Crop the Image to the Desired Resolution
        if not use_sliding_window and (nx > self.max_pixels or ny > self.max_pixels):
            scale_factor =  max(nx, ny) / self.max_pixels
            self.image0 = FourierRescale2D.run(self.image0, scale_factor)
            (nx, ny) = self.image0.shape
            
        # Segment Image
        self.segment_image(
            self.image0,
            display_image = display_image, 
            use_sliding_window = use_sliding_window)

        return self.masks