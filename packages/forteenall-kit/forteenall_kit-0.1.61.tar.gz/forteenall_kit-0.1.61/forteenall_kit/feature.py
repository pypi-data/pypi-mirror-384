import inspect
from .invoke import Invoker


class KitFeature:
    def __init__(self, feature_type, **params):
        # check for who called this Class
        # caller frame on index=1 is Child of this class
        # caller frame on index=2 is target feature
        try:
            stack = inspect.stack()
            caller_frame = stack[2].frame
            locals_in_caller = caller_frame.f_locals
        except Exception:
            raise ValueError("YOU MUST USE FEATURE IN INVOKER")

        # Get another instance
        self.outer_instance: Invoker = locals_in_caller.get("self", None)

        # check parent is invoker
        # if parent not invoker we can't call execute command
        try:
            if not isinstance(self.outer_instance, Invoker):
                raise "NOT AN INVOKER"
        except Exception:
            raise ValueError("FEATURE NOT USED IN INVOKER")

        # execute from manager
        self.manager = self.outer_instance.manager
        self.manager.execute(feature_type=feature_type, **params)
