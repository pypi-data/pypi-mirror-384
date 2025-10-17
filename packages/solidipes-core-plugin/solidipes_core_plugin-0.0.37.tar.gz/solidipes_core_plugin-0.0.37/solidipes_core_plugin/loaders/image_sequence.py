from PIL import Image as PILImage
from solidipes.loaders.mime_types import make_from_text
from solidipes.loaders.sequence import Sequence

from .image import Image


class ImageSequence(Sequence, Image):
    """Sequence of images loaded with PIL"""

    from ..viewers.image import Image as ImageViewer

    supported_mime_types = make_from_text("""
image/apng                         apng
image/gif                          gif
image/heic-sequence                heics
image/heif-sequence                heifs
image/jpm                          jpm jpgm
image/tiff                         tiff tif
image/tiff-fx                      tfx
""")

    _compatible_viewers = [ImageViewer]

    @Image.loadable
    def image_sequence(self):
        return PILImage.open(self.file_info.path)

    @Image.loadable
    def n_frames(self):
        return self.image_sequence.n_frames

    @property
    def _element_count(self):
        return self.n_frames

    def _load_element(self, n):
        """Load a single frame"""

        self.image_sequence.seek(n)
        return self.image_sequence.copy()

    def select_frame(self, frame):
        self.select_element(frame)

    @property
    def image(self):
        # cannot be defined as loadable because it changes
        return self._current_element

    def _is_image_sequence(self):
        """In addition to File class checks, also check if the file is a sequence of images"""

        try:
            with PILImage.open(self.file_info.path) as im:
                return im.is_animated  # tests whether the file contains multiple frames

        except Exception:
            return False
