import numpy


class _BoundingBox:
    def __init__(self, v1, v2):
        if not numpy.isscalar(v1):
            v1 = tuple(v1)
        if not numpy.isscalar(v2):
            v2 = tuple(v2)
        self._min = min(v1, v2)
        self._max = max(v1, v2)

    @property
    def min(self) -> float:
        return self._min

    @property
    def max(self) -> float:
        return self._max

    def __str__(self):
        return f"({self.min}, {self.max})"

    def __eq__(self, other):
        if not isinstance(other, _BoundingBox):
            return False
        else:
            return self.min == other.min and self.max == other.max

    def get_overlap(self, other_bb):
        raise NotImplementedError("Base class")


class BoundingBox1D(_BoundingBox):
    def get_overlap(self, other_bb):
        if not isinstance(other_bb, BoundingBox1D):
            raise TypeError(f"Can't compare a {BoundingBox1D} with {type(other_bb)}")
        if (
            (self.max >= other_bb.min and self.min <= other_bb.max)
            or (other_bb.max >= self.min and other_bb.min <= self.max)
            or (other_bb.min <= self.min and other_bb.max >= self.max)
        ):
            return BoundingBox1D(
                max(self.min, other_bb.min), min(self.max, other_bb.max)
            )
        else:
            return None

    def __eq__(self, other):
        if isinstance(other, (tuple, list)):
            return len(other) == 2 and self.min == other[0] and self.max == other[1]
        else:
            return super().__eq__(other)

    def __hash__(self):
        return hash((self._min, self._max))


class BoundingBox3D(_BoundingBox):
    def get_overlap(self, other_bb):
        if not isinstance(other_bb, BoundingBox3D):
            raise TypeError(f"Can't compare a {BoundingBox3D} with {type(other_bb)}")
        self_bb_0 = BoundingBox1D(self.min[0], self.max[0])
        self_bb_1 = BoundingBox1D(self.min[1], self.max[1])
        self_bb_2 = BoundingBox1D(self.min[2], self.max[2])

        other_bb_0 = BoundingBox1D(other_bb.min[0], other_bb.max[0])
        other_bb_1 = BoundingBox1D(other_bb.min[1], other_bb.max[1])
        other_bb_2 = BoundingBox1D(other_bb.min[2], other_bb.max[2])

        overlap_0 = self_bb_0.get_overlap(other_bb_0)
        overlap_1 = self_bb_1.get_overlap(other_bb_1)
        overlap_2 = self_bb_2.get_overlap(other_bb_2)
        if overlap_0 is not None and overlap_1 is not None and overlap_2 is not None:
            return BoundingBox3D(
                (overlap_0.min, overlap_1.min, overlap_2.min),
                (overlap_0.max, overlap_1.max, overlap_2.max),
            )


def get_subvolume_shape(chunk, volume_shape):
    """
    Get the shape of a sub-volume to extract in a volume.

    :param chunk: tuple of slice
    :param volume_shape: tuple of int
    """
    shape = []
    for c, v in zip(chunk, volume_shape):
        start = c.start or 0
        end = c.stop or v
        if end < 0:
            end += v
        shape.append(end - start)
    return tuple(shape)
