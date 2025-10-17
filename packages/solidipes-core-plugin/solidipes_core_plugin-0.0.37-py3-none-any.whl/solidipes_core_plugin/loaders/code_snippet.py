import os

import pylint.lint
from pylint.reporters.collecting_reporter import CollectingReporter as Reporter
from solidipes.utils import solidipes_logging as logging
from solidipes.validators.validator import add_validation_error, validator

from .text import Text

logger = logging.getLogger()


class CodeSnippet(Text):
    from ..viewers.code_snippet import Code as CodeViewer

    supported_mime_types = {
        "text/x-python": "py",
        "text/x-shellscript": "sh",
        "text/x-tex": ["tex", "latex", "sty"],
        "text/x-script.python": "py",
        "text/x-sh": "sh",
        "program/C": ["c", "h"],
        "program/C++": ["cc", "cpp", "hh"],
        "program/matlab": ["m"],
        "program/xfig": ["fig", "xfig"],
        "application/mathematica-notebook": ["nb"],
    }

    _compatible_viewers = [CodeViewer]

    @Text.loadable
    def text(self):
        _text = super().text
        return _text

    @Text.cached_loadable
    def lint(self):
        fname = self.file_info.path
        lint_messages = []
        for msg in self.lint_raw:
            formatted_msg = f"{fname}:{msg['line']}:{msg['column']}:{msg['msg_id']}:{msg['symbol']}: {msg['msg']}"
            lint_messages.append((msg["msg_id"], formatted_msg))
        return lint_messages

    @Text.cached_loadable
    def lint_errors(self):
        fname = self.file_info.path
        lint_messages = []
        for msg in self.lint_raw:
            formatted_msg = f"{fname}:{msg['line']}:{msg['column']}:{msg['msg_id']}:{msg['symbol']}: {msg['msg']}"
            if msg["msg_id"][0] in ["E", "F"]:
                lint_messages.append((msg["msg_id"], formatted_msg))
        return lint_messages

    @validator(description="No lint errors", mandatory=False)
    def has_no_lint_errors(self) -> bool:
        errors = [e[1] for e in self.lint_errors]

        if len(errors) > 0:
            add_validation_error(errors)
            return False

        return True

    @Text.cached_loadable
    def lint_raw(self):
        logger.info(f"re-lint {self.file_info.path}")
        fname = self.file_info.path

        if os.path.splitext(fname)[1] == ".py":
            rep = Reporter()
            pylint.lint.Run(
                [fname, "--extension-pkg-allow-list=scipy", "--clear-cache-post-run", "y"], reporter=rep, exit=False
            )
            dict_messages = []

            for message in rep.messages:
                dict_message = message.__dict__

                if "confidence" in dict_message:
                    dict_message["confidence"] = dict_message["confidence"]._asdict()

                dict_messages.append(dict_message)

            return dict_messages

        return []
