import re
import subprocess

from solidipes.utils import solidipes_logging as logging
from solidipes.validators.validator import add_validation_error, validator

from .code_snippet import CodeSnippet

logger = logging.getLogger()


class GnuPlotExecutor:
    def __init__(self, terminal=None):
        self.terminal = terminal
        self.process = subprocess.Popen(
            ["gnuplot", "-p"], shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        logger.debug(self.process)
        self.write = self.process.stdin.write
        self.flush = self.process.stdin.flush
        self.image_fnames = []
        self.old_image_fnames = {}

    def modify_line(self, line):
        if self.terminal is None:
            return line

        line = re.sub(r"set terminal (.*)", f"set terminal {self.terminal}", line)

        m = re.match("set output ['\"](.+)['\"]", line)
        if m:
            import tempfile

            fp = tempfile.NamedTemporaryFile(delete=True)
            image_fname = f"{fp.name}.png"
            self.image_fnames.append(image_fname)
            line = re.sub("set output (.+)", f'set output "{image_fname}"', line)
            self.old_image_fnames[m.group(1).strip()] = image_fname.strip()
            logger.debug(f"replace {m.group(1)} -> {image_fname}")

        for old_f, new_f in self.old_image_fnames.items():
            if old_f in line:
                line = line.replace(old_f, new_f)

        if line[0] == "!":
            line = ""

        if line.strip() == "set output":
            line = ""

        return line

    def cmd(self, *args):
        from io import StringIO

        commands = []
        for cmd in args:
            cmd = filter(lambda x: (x.strip()) and (x.strip()[0] != "#"), StringIO(cmd.strip()).readlines())
            cmd = [self.modify_line(e) for e in cmd]
            commands += map(lambda x: x.strip(), cmd)

        for c in commands:
            logger.debug(f"execute: {c}")
            self.__call__("%s" % (c))

    def __call__(self, s):
        cmd = s + "\n"
        self.write(cmd.encode("utf-8"))
        self.flush()

    def exit(self):
        return self.process.communicate()


class GnuPlot(CodeSnippet):
    from ..viewers.image import Image
    from ..viewers.image_source import ImageSource as ImageSourceViewer

    supported_mime_types = {"drawing/gnuplot": ["gp", "gpu", "gih"]}
    _compatible_viewers = [ImageSourceViewer, Image]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._warnings = []
        self._errors = []

    @validator(description="Gnuplot script can generate an image")
    def _generated_image(self) -> bool:
        if not self.image:
            add_validation_error(["gnuplot error: image file was not created"])
            return False

    @validator(description="Gnuplot script has no error")
    def _check_gnuplot_errors(self) -> bool:
        _ = self.image
        if (not self._errors) and (not self._warnings):
            return True

        ret = True
        if self._errors:
            err = "\n".join(self._errors)
            add_validation_error([f"gnuplot errors:\n{err}"])
            ret = False
        return ret

    @validator(description="Gnuplot script has no warning", mandatory=False)
    def _check_gnuplot_warnings(self) -> bool:
        _ = self.image
        if (not self._errors) and (not self._warnings):
            return True

        ret = True
        if self._warnings:
            warn = "\n".join(self._warnings)
            add_validation_error([f"gnuplot warnings:\n{warn}"])
            ret = False
        return ret

    @CodeSnippet.loadable
    def image(self):
        import os

        cur_dir = os.getcwd()
        text = self.text
        images = []
        try:
            path = os.path.dirname(self.file_info.path)
            os.chdir(path)
            g = GnuPlotExecutor(terminal="pngcairo")
            g.cmd(text)
            _out, _err = g.exit()
            _out = _out.decode()
            _err = _err.decode()

            if _err and "warning" in _err.lower():
                self._warnings += _err.split("\n")
            elif _err:
                self._errors += _err.split("\n")

            for f in g.image_fnames:
                if not os.path.exists(f):
                    logger.error("no file generated")
                    continue
                if not os.path.getsize(f):
                    logger.error("empty file generated")
                    continue
                from PIL import Image as PILImage

                images.append(PILImage.open(f))
                os.remove(f)

            os.chdir(cur_dir)
        except Exception as e:
            logger.error(f"GGGG {e} {type(e)}")
            import traceback

            logger.error(f"{traceback.format_exc()}")

        os.chdir(cur_dir)
        return images
