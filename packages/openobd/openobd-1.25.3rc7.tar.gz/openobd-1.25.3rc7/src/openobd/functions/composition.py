from openobd.functions.function import OpenOBDFunction
from openobd.core.exceptions import OpenOBDException

class OpenOBDComposition(OpenOBDFunction):

    def __enter__(self):
        if self._context_finished_:
            ''' We cannot continue when the constructor failed '''
            raise OpenOBDException("Failed to construct openOBD session")

        return self


