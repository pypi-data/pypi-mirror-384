from __future__ import annotations

import os
from tempfile import TemporaryDirectory

import pytest

from nxtomo.nxobject.nxobject import NXobject


class test_nx_object:
    """Test API of the NXobject."""

    with pytest.raises(TypeError):
        NXobject(node_name=12)
    with pytest.raises(TypeError):
        NXobject(node_name="test", parent=12)

    nx_object = NXobject(node_name="NXobject")
    with pytest.raises(NotImplementedError):
        nx_object.to_nx_dict(nexus_path_version=1.0)
    assert nx_object.is_root is True

    with pytest.raises(TypeError):
        nx_object.node_name = 12

    with pytest.raises(AttributeError):
        nx_object.test = 12

    class MyNXObject(NXobject):
        def to_nx_dict(
            self,
            nexus_path_version: float | None = None,
            data_path: str | None = None,
        ) -> dict:
            return {
                f"{self.path}/test": "toto",
            }

    my_nx_object = MyNXObject(node_name="NxObject2")

    with TemporaryDirectory() as folder:
        file_path = os.path.join(folder, "my_nexus.nx")
        assert not os.path.exists(file_path)
        my_nx_object.save(
            file_path=file_path, data_path="/object", nexus_path_version=1.0
        )
        assert os.path.exists(file_path)

        with pytest.raises(KeyError):
            my_nx_object.save(
                file_path=file_path,
                data_path="/object",
                nexus_path_version=1.0,
                overwrite=False,
            )

        my_nx_object.save(
            file_path=file_path,
            data_path="/object",
            nexus_path_version=1.0,
            overwrite=True,
        )
