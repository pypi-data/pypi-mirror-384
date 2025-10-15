import os
import shutil

from openmodule import sentry
from openmodule.config import settings
from openmodule.core import core
from openmodule.models.base import OpenModuleModel


@sentry.trace
def upload(src, dst, rpc_client=None):
    """
    Use the service-databox to upload a file. The file is first copied as hidden file (not uploaded)
    and then renamed to assert an atomic move. The upload directory needs to be mounted correctly in the compose file
    :param src: source file, must not be a directory
    :param dst: destination where the file should be uploaded to.
                If dst ends with a slash, the basename of src is appended to dst
                path is relative to settings.DATABOX_UPLOAD_DIR
    :param rpc_client: rpc client to use, defaults to the core rpc client
    """

    assert os.path.exists(src), "src does not exist"
    assert os.path.isfile(src), "src must be a file and no directory"
    if dst.endswith("/"):
        dst = os.path.join(dst, os.path.basename(src))
    dst = os.path.join(settings.DATABOX_UPLOAD_DIR, dst.strip("/"))
    directory = os.path.dirname(dst)
    os.makedirs(directory, exist_ok=True)
    tmp_dst = os.path.join(directory, "." + os.path.basename(dst))
    shutil.move(src, tmp_dst)
    os.rename(tmp_dst, dst)
    rpc_client = rpc_client or core().rpc_client

    rpc_client.rpc_non_blocking("databox", "trigger_upload", OpenModuleModel())
