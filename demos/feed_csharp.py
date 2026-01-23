from typing import Any
from xarp.express import AsyncXR, SyncXR
from xarp.server import run, show_qrcode_link

def sync_app(xr: SyncXR, kwargs: dict[str, Any]) -> None:
    xr.baseline_code("Hello")
    xr.say("Done sending")


if __name__ == '__main__':
    show_qrcode_link()
    run(sync_app)