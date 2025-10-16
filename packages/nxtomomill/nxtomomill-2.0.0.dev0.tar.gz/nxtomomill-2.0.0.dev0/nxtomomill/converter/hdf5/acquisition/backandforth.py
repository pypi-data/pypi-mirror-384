from __future__ import annotations

from .multitomo import MultiTomoAcquisition


class BackAndForthAcquisition(MultiTomoAcquisition):
    """

        Back and forth acquisition is very similar to multi-tomo.

        In multi-tomo, the acquisition of projections begins when the rotation speed has reached an 'optimal' value.
    value.

        In back-and-forth acquisition, projections will be acquired in one rotation direction, then in the opposite direction, and so on.

        From the nxtomomill perspective, the constraints and processing remain the same.
        Nevertheless for clarity (and possible future evolution) a dedicated class has been created.
    """
