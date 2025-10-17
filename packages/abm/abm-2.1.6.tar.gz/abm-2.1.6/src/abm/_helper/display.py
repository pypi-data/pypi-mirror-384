__all__ = ["Display"]

from dataclasses import dataclass
from uuid import uuid4

from IPython import get_ipython
from IPython.display import DisplayObject, display, update_display


@dataclass(kw_only=True, slots=True)
class Display:
    display_id: str | None = None

    def display(self, display_object: DisplayObject) -> None:
        if get_ipython() is None:
            message = display_object.data
        else:
            message = display_object

        if self.display_id is None:
            self.display_id = str(uuid4())
            display(message, display_id=self.display_id)
        else:
            update_display(message, display_id=self.display_id)
