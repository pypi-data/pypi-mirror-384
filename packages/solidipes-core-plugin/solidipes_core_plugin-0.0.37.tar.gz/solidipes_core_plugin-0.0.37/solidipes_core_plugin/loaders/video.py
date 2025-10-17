from solidipes.loaders.file import File
from solidipes.loaders.mime_types import make_from_text


class Video(File):
    """Video file"""

    from ..viewers.video import Video as VideoViewer

    supported_mime_types = make_from_text("""
    video/1d-interleaved-parityfec
video/3gpp
video/3gpp-tt
video/3gpp2
video/annodex					axv
video/AV1
video/BMPEG
video/BT656
video/CelB
video/DV
video/dv					dif dv
video/encaprtp
video/example
video/FFV1
video/flexfec
video/fli					fli
video/gl					gl
video/H261
video/H263
video/H263-1998
video/H263-2000
video/H264
video/H264-RCDO
video/H264-SVC
video/H265
video/H266
video/iso.segment				m4s
video/JPEG
video/jpeg2000
video/jxsv
video/mj2					mj2 mjp2
video/MP1S
video/MP2P
video/MP2T
video/mp4					mp4 mpg4 m4v
video/MP4V-ES
video/mpeg					mpeg mpg mpe m1v m2v
video/mpeg4-generic
video/MPV
video/nv
video/ogg					ogv
video/parityfec
video/pointer
video/quicktime					qt mov
video/raptorfec
video/raw
video/rtp-enc-aescm128
video/rtploopback
video/rtx
video/scip
video/smpte291
video/SMPTE292M
video/ulpfec
video/vc1
video/vc2
video/vnd.CCTV
video/vnd.dece.hd				uvh uvvh
video/vnd.dece.mobile				uvm uvvm
video/vnd.dece.mp4				uvu uvvu
video/vnd.dece.pd				uvp uvvp
video/vnd.dece.sd				uvs uvvs
video/vnd.dece.video				uvv uvvv
video/vnd.directv.mpeg
video/vnd.directv.mpeg-tts
video/vnd.dlna.mpeg-tts
video/vnd.dvb.file				dvb
video/vnd.fvt					fvt
video/vnd.hns.video
video/vnd.iptvforum.1dparityfec-1010
video/vnd.iptvforum.1dparityfec-2005
video/vnd.iptvforum.2dparityfec-1010
video/vnd.iptvforum.2dparityfec-2005
video/vnd.iptvforum.ttsavc
video/vnd.iptvforum.ttsmpeg2
video/vnd.motorola.video
video/vnd.motorola.videop
video/vnd.mpegurl				mxu m4u
video/vnd.ms-playready.media.pyv		pyv
video/vnd.nokia.interleaved-multimedia		nim
video/vnd.nokia.mp4vr
video/vnd.nokia.videovoip
video/vnd.objectvideo
video/vnd.radgamettools.bink			bik bk2
video/vnd.radgamettools.smacker			smk
video/vnd.sealed.mpeg1				smpg s11
video/vnd.sealed.mpeg4				s14
video/vnd.sealed.swf				sswf ssw
video/vnd.sealedmedia.softseal.mov		smov smo s1q
video/vnd.uvvu.mp4
video/vnd.vivo					viv
video/vnd.youtube.yt				yt
video/VP8
video/VP9
video/webm					webm
video/x-flv					flv
video/x-la-asf					lsf lsx
video/x-matroska				mpv mkv
video/x-mng					mng
video/x-ms-wm					wm
video/x-ms-wmv					wmv
video/x-ms-wmx					wmx
video/x-ms-wvx					wvx
video/x-msvideo					avi
video/x-sgi-movie				movie""")

    _compatible_viewers = [VideoViewer]

    @File.loadable
    def video(self):
        return open(self.file_info.path, "rb")
