# Standard library imports
import os
import importlib.metadata as metadata

# Third party imports
from opengeodeweb_viewer.utils_functions import get_schemas_dict, validate_schema
from vtk.web import protocols as vtk_protocols
from wslink import register as exportRpc

# Local application imports


class VtkVeaseViewerView(vtk_protocols.vtkWebProtocol):
    prefix = "vease_viewer."
    schemas_dict = get_schemas_dict(os.path.join(os.path.dirname(__file__), "schemas"))

    def __init__(self):
        super().__init__()

    @exportRpc(prefix + schemas_dict["microservice_version"]["rpc"])
    def microservice_version(self, params):
        print(
            self.prefix + self.schemas_dict["microservice_version"]["rpc"],
            f"{params=}",
            flush=True,
        )
        validate_schema(params, self.schemas_dict["microservice_version"])

        return {"microservice_version": metadata.distribution("vease_viewer").version}

    @exportRpc("kill")
    def kill(self) -> None:
        print("Manual viewer kill, shutting down...", flush=True)
        os._exit(0)
