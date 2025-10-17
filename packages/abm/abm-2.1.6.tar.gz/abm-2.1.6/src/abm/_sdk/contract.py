from __future__ import annotations

__all__ = ["Contract"]

from dataclasses import dataclass

from .dataclass_helpers import ignore_extra_kwargs


@ignore_extra_kwargs
@dataclass(frozen=True, kw_only=True, slots=True)
class Contract:
    id: str
    deleted: bool
    fulfilled: bool

    @staticmethod
    def from_id(id: str, interval: float = 5.0, wait: bool = True) -> Contract:
        from . import client

        if not wait:
            interval = 0

        # Limit interval to 4 minutes since our infrastructure supports opened HTTP connections for up to 5 minutes.
        interval = min(4 * 60, interval)

        response = client.httpx_client.get(f"/contracts/{id}/", params={"wait": interval}).json()
        return Contract(**response)

    def refresh(self, force: bool = False, interval: float = 5.0, wait: bool = True) -> Contract:
        if force or not (self.fulfilled or self.deleted):
            return Contract.from_id(id=self.id, interval=interval, wait=wait)
        else:
            return self

    def stop(self) -> None:
        from . import client

        client.httpx_client.delete(f"/contracts/{self.id}/")

    def progress(self) -> str:
        try:
            from . import client

            response = client.httpx_client.get(f"/contracts/{self.id}/progress/").json()

            total = response["total"]
            succeeded = response["succeeded"]
            failed = response["failed"]
            running = total - succeeded - failed

            return f"Total: {total}, Running: {running}, Succeeded: {succeeded}, Failed: {failed}"
        except Exception:
            return ""
