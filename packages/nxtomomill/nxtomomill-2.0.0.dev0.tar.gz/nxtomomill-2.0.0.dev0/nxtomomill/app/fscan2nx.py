import sys
import logging
import argparse
from nxtomomill.converter.fscan.fscanconverter import from_fscan_to_nx


_logger = logging.getLogger(__name__)


def main(argv):
    parser = argparse.ArgumentParser(
        description="convert fscan dataset to nexus format. "
    )
    parser.add_argument(
        "input_file",
        help="Path to the master file of the acquisition, containing entries '1.1', '2.1', etc",
        default=None,
        nargs="?",
    )
    parser.add_argument(
        "output_file",
        help="Path to the output NX file",
        default=None,
        nargs="?",
    )
    parser.add_argument(
        "--halftomo",
        help="Whether to enable extended-field-of-view mode (half-tomography). Default is False.",
        dest="halftomo",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--ignore_last_n_projections",
        "--ignore-last-n-projections",
        default=0,
        help="Number of projections to ignore in the end of each series of projections",
    )

    parser.add_argument(
        "--detector-name",
        "--detector_name",
        default="pcoedgehs",
        help="Detector name. Default is pcoedgehs.",
    )
    parser.add_argument(
        "--rot_motor_name",
        "--rot-motor-name",
        default="hrrz",
        help="Rotation motor name. Default is hrrz.",
    )

    parser.add_argument("--energy", default=None, help="Incident beam energy in keV")
    parser.add_argument(
        "--distance", default=None, help="Sample-detector distance in meters"
    )

    options = parser.parse_args(argv[1:])

    if options.input_file is None or options.output_file is None:
        _logger.error("Need input file and output file. Type --help to see options")
        sys.exit(0)

    energy = options.energy
    distance = options.distance
    if energy is not None:
        energy = float(energy)
    if distance is not None:
        distance = float(distance)

    from_fscan_to_nx(
        options.input_file,
        options.output_file,
        detector_name=options.detector_name,
        rotation_motor_name=options.rot_motor_name,
        halftomo=options.halftomo,
        ignore_last_n_projections=options.ignore_last_n_projections,
        energy=energy,
        distance=distance,
    )


if __name__ == "__main__":
    main(sys.argv)
