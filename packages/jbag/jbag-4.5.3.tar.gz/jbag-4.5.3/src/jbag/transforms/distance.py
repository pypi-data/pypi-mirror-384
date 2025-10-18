import jbag.metrics.SDF
from jbag.transforms.transform import Transform


class SDF(Transform):
    def __init__(self, keys, normalize):
        """
        Compute signed distance function.

        Args:
            keys (str or sequence): binary segmentation for computing SDF.
            normalize (bool): if `True`, normalize the SDF by min-max normalization.
        """
        super().__init__(keys)
        self.normalize = normalize

    def _call_fun(self, data):
        for key in self.keys:
            segmentation = data[key]
            sdf_map = jbag.metrics.SDF.SDF(segmentation, self.normalize)
            data[f"{key}_SDF"] = sdf_map
        return data
