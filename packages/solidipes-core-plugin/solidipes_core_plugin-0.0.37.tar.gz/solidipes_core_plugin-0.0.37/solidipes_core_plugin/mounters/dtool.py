################################################################
from solidipes.mounters.cloud import Mounter, parameter
from solidipes.utils import solidipes_logging as logging

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class DToolMounter(Mounter):
    """Create a remote dtool file system."""

    parser_key = "dtool"

    should_wait_mount = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def mount(self) -> None:
        logger.warning("This mounter only creates the hooks to scan a dtool repository")
        pass

    @parameter
    def endpoint() -> str:
        """Dtool URI (e.g. s3://bucket/dataset_id)."""
        pass

    def wait_mount(self) -> None:
        pass
