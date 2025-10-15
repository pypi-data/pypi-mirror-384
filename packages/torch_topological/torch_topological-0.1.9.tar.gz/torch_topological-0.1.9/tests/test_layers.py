from torch_topological.datasets import SphereVsTorus

from torch_topological.nn.data import make_tensor

from torch_topological.nn import VietorisRipsComplex
from torch_topological.nn.layers import StructureElementLayer

from torch.utils.data import DataLoader

batch_size = 32


class TestStructureElementLayer:
    data_set = SphereVsTorus(n_point_clouds=2 * batch_size)
    loader = DataLoader(
        data_set,
        batch_size=batch_size,
        shuffle=True,
        drop_last=False,
    )

    vr = VietorisRipsComplex(dim=1)

    layer = StructureElementLayer(10)

    def test_processing(self):
        for (x, y) in self.loader:
            pers_info = make_tensor(self.vr(x))
            output = self.layer(pers_info)

            assert pers_info is not None
            assert output is not None
