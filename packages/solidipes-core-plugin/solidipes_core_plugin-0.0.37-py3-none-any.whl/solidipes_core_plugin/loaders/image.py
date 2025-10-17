from PIL import ExifTags
from PIL import Image as PILImage
from PIL.TiffImagePlugin import IFDRational
from solidipes.loaders.data_container import DataContainer
from solidipes.loaders.file import File
from solidipes.loaders.mime_types import make_from_text


class SVGWrapper:
    def __init__(self, filename):
        self.src = open(filename, "r").read()

    def _repr_svg_(self):
        return self.src

    def show(self):
        from io import BytesIO

        import cairosvg
        import matplotlib.pyplot as plt

        img_png = cairosvg.svg2png(self.src)
        img = Image.open(BytesIO(img_png))
        plt.imshow(img)


class Image(File):
    """Image loaded with PIL"""

    from ..viewers.image import Image as ImageViewer

    supported_mime_types = make_from_text("""
image/aces					exr
image/apng					apng
image/avci					avci
image/avcs					avcs
image/avif					avif hif
image/bmp					bmp
image/cgm					cgm
image/dicom-rle					drle
image/dpx					dpx
image/emf					emf
image/example
image/fits					fits fit fts
image/g3fax
image/gif					gif
image/heic					heic
image/heic-sequence				heics
image/heif					heif
image/heif-sequence				heifs
image/hej2k					hej2
image/hsj2					hsj2
image/ief					ief
image/jls					jls
image/jp2					jp2 jpg2
image/jpeg					jpeg jpg jpe jfif
image/jph					jph
image/jphc					jhc jphc
image/jpm					jpm jpgm
image/jpx					jpx jpf
image/jxl					jxl
image/jxr					jxr
image/jxrA					jxra
image/jxrS					jxrs
image/jxs					jxs
image/jxsc					jxsc
image/jxsi					jxsi
image/jxss					jxss
image/ktx					ktx
image/ktx2					ktx2
image/naplps
image/png					png
image/prs.btif					btif btf
image/prs.pti					pti
image/pwg-raster
image/svg+xml					svg svgz
image/t38
image/tiff					tiff tif
image/tiff-fx					tfx
image/vnd.adobe.photoshop			psd
image/vnd.airzip.accelerator.azv		azv
image/vnd.cns.inf2
image/vnd.dece.graphic				uvi uvvi uvg uvvg
image/vnd.djvu					djvu djv
image/vnd.dvb.subtitle
image/vnd.dwg					dwg
image/vnd.dxf					dxf
image/vnd.fastbidsheet				fbs
image/vnd.fpx					fpx
image/vnd.fst					fst
image/vnd.fujixerox.edmics-mmr			mmr
image/vnd.fujixerox.edmics-rlc			rlc
image/vnd.globalgraphics.pgb			PGB pgb
image/vnd.microsoft.icon			ico
image/vnd.mix
image/vnd.ms-modi				mdi
image/vnd.net-fpx
image/vnd.pco.b16				b16
image/vnd.radiance				hdr rgbe xyze
image/vnd.sealed.png				spng spn s1n
image/vnd.sealedmedia.softseal.gif		sgif sgi s1g
image/vnd.sealedmedia.softseal.jpg		sjpg sjp s1j
image/vnd.svf
image/vnd.tencent.tap				tap
image/vnd.valve.source.texture			vtf
image/vnd.wap.wbmp				wbmp
image/vnd.xiff					xif
image/vnd.zbrush.pcx				pcx
image/webp					webp
image/wmf					wmf
image/x-canon-cr2				cr2
image/x-canon-crw				crw
image/x-cmu-raster				ras
image/x-coreldraw				cdr
image/x-coreldrawpattern			pat
image/x-coreldrawtemplate			cdt
image/x-corelphotopaint				cpt
image/x-epson-erf				erf
image/x-jg					art
image/x-jng					jng
image/x-nikon-nef				nef
image/x-olympus-orf				orf
image/x-portable-anymap				pnm
image/x-portable-bitmap				pbm
image/x-portable-graymap			pgm
image/x-portable-pixmap				ppm
image/x-rgb					rgb
image/x-xbitmap					xbm
image/x-xcf					xcf
image/x-xpixmap					xpm
image/x-xwindowdump				xwd
application/postscript                          eps ps
""")

    _compatible_viewers = [ImageViewer]

    @File.loadable
    def image(self):
        if self.file_info.type == "image/svg+xml":
            return SVGWrapper(self.file_info.path)
        else:
            return PILImage.open(self.file_info.path)

    @File.cached_loadable
    def exif_data(self):
        try:
            return self.get_exif_data()
        except Exception as err:
            return str(err)

    def get_exif_data(self):
        pil_exif = self.image._getexif()
        if pil_exif is None:
            return DataContainer()

        exif = {ExifTags.TAGS[k]: v for k, v in pil_exif.items() if k in ExifTags.TAGS}

        # Convert PIL.TiffImagePlugin.IFDRational to float:
        for k, v in exif.items():
            if isinstance(v, IFDRational):
                exif[k] = float(v)

        return DataContainer(exif)
