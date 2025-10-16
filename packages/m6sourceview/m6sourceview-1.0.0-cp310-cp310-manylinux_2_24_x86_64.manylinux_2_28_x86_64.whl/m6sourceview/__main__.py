from . import m6geo
import os
import sys
import numpy as np
import tarfile
import gzip
import re
from pathlib import Path
import argparse
import matplotlib.pyplot as plt


def get_line_intersections(coord, cos_dir):
    intersections = []
    m6geo.init_tracking(coord, cos_dir)

    while True:
        distance = m6geo.get_distance_to_next_interface()
        if distance > 1e300:
            break

        m6geo.actualize_coord_distance(distance)
        coord = m6geo.get_current_position()
        intersections.append(coord)

        volume_id = m6geo.get_volume_after_next_interface()
        if m6geo.is_void_volume(volume_id):
            break

    return intersections


def get_intersections(axis, altitude, minc, maxc, nb_max_pixel):
    lengths = [maxc[i] - minc[i] for i in range(3)]
    step_x = lengths[axis[0]] / nb_max_pixel
    step_y = lengths[axis[1]] / nb_max_pixel
    step = max(step_x, step_y)

    intersections = []

    for h in range(nb_max_pixel):
        coord_h = [0.0, 0.0, 0.0]
        coord_h[axis[0]] = minc[axis[0]]
        coord_h[axis[1]] = minc[axis[1]] + h * step
        coord_h[axis[2]] = altitude
        cos_dir_h = [0.0, 0.0, 0.0]
        cos_dir_h[axis[0]] = 1.0
        intersections.extend(get_line_intersections(coord_h, cos_dir_h))

        coord_v = [0.0, 0.0, 0.0]
        coord_v[axis[0]] = minc[axis[0]] + h * step
        coord_v[axis[1]] = minc[axis[1]]
        coord_v[axis[2]] = altitude
        cos_dir_v = [0.0, 0.0, 0.0]
        cos_dir_v[axis[1]] = 1.0
        intersections.extend(get_line_intersections(coord_v, cos_dir_v))

    return intersections


def get_last_cycle_start(tar):
    max_cycle = 0
    member = None

    for m in tar.getmembers():
        match = re.search(r"start\.(\d+)\.gz", m.name)
        if not match:
            continue

        cycle_number = int(match.group(1))
        if cycle_number > max_cycle:
            max_cycle = cycle_number
            member = m

    return member


def load_neutron_data(tar_path, bank_max_size):
    tar_path = Path(tar_path)

    if not tar_path.exists():
        raise FileNotFoundError(f"Fission data file not found: {tar_path}")

    x_pos, y_pos, z_pos = [], [], []

    with tarfile.open(tar_path, "r") as tar:
        tar_member = get_last_cycle_start(tar)

        if tar_member is None:
            raise ValueError(f"No cycle data found in {tar_path}")

        gz_file = tar.extractfile(tar_member)
        with gzip.open(gz_file, "rt") as f:
            lines = f.readlines()[1:]

            for line in lines:
                parts = line.split()
                if len(parts) != 5:
                    print(
                        f"Warning: bad format in line: {line.strip()}", file=sys.stderr
                    )
                    continue

                x_pos.append(float(parts[1]))
                y_pos.append(float(parts[2]))
                z_pos.append(float(parts[3]))

                if len(x_pos) == bank_max_size:
                    print(
                        f"Reached maximum bank size of {bank_max_size} fission sites. Stopping reading further."
                    )
                    break

    return x_pos, y_pos, z_pos


def calculate_center_of_mass(births):
    x_pos, y_pos, z_pos = births
    return np.array([np.mean(x_pos), np.mean(y_pos), np.mean(z_pos)])


def create_slice_plot(
    ax, axis, altitude, births, minc, maxc, nb_max_pixel, axis_label, altitude_label
):
    print(f"Building {axis_label} slice at altitude {altitude:.2f} cm")

    intersections = get_intersections(
        axis=axis,
        altitude=altitude,
        minc=minc,
        maxc=maxc,
        nb_max_pixel=nb_max_pixel,
    )

    cm = calculate_center_of_mass(births)

    x_coords = [point[axis[0]] for point in intersections]
    y_coords = [point[axis[1]] for point in intersections]

    ax.scatter(x_coords, y_coords, alpha=1.0, c="black", s=1, label=None)
    ax.scatter(
        births[axis[0]], births[axis[1]], alpha=0.4, c="red", s=1, label="Fissions"
    )
    ax.scatter(
        cm[axis[0]],
        cm[axis[1]],
        marker="+",
        s=100,
        c="blue",
        linewidths=2,
        label="Center of Mass",
    )
    ax.set_title(f"{axis_label} ({altitude_label}={altitude:.2f} cm)")
    ax.set_xlabel(f"{axis_label[0]} (cm)")
    ax.set_ylabel(f"{axis_label[1]} (cm)")
    ax.axis("equal")
    ax.legend()


def main():
    parser = argparse.ArgumentParser(
        description="Show MORET6 fission sites over the geometry"
    )
    parser.add_argument("input_file_path", type=Path, help="Path to the input M6 file")
    parser.add_argument(
        "--nb_max_pixel",
        type=int,
        default=500,
        help="Maximum number of pixels (default: 500)",
    )
    parser.add_argument(
        "--max_bank_size",
        type=int,
        default=10_000,
        help="Maximum fission site size (default: 10,000)",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not display the plot window",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: input_file.fission_sites.png)",
    )

    args = parser.parse_args()

    try:
        if not args.input_file_path.exists():
            print(
                f"Error: Input file not found: {args.input_file_path}", file=sys.stderr
            )
            sys.exit(1)

        print(f"Using MORET_XML_LIB_PATH: {os.environ.get('MORET_XML_LIB_PATH')}")
        print(
            "\n\033[1mImportant note:\033[0m if the input file contains errors, "
            "the program will stop without warning.\n"
            "If the input file is correctly loaded you will see: 'Jdd correctly loaded'\n"
        )

        m6geo.load_from_file(str(args.input_file_path))
        print("Jdd correctly loaded")

        minc = m6geo.get_min_coordinate()
        maxc = m6geo.get_max_coordinate()
        print(f"Bounding box: {minc} to {maxc}")

        tar_path = args.input_file_path.with_suffix(
            args.input_file_path.suffix + ".star.tar"
        )
        print(f"Loading fission sites from {tar_path}")

        births = load_neutron_data(tar_path, args.max_bank_size)
        birth_cm = calculate_center_of_mass(births)
        print(
            f"Fission site center of mass: [ {birth_cm[0]:.2f}, {birth_cm[1]:.2f}, {birth_cm[2]:.2f} ]"
        )

        axis_combinations = [[0, 1, 2], [1, 2, 0], [2, 0, 1]]
        axis_labels = ["XY", "YZ", "XZ"]
        altitude_labels = ["Z", "X", "Y"]

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        for i, axis in enumerate(axis_combinations):
            altitude = birth_cm[axis[2]]
            create_slice_plot(
                axes[i],
                axis,
                altitude,
                births,
                minc,
                maxc,
                args.nb_max_pixel,
                axis_labels[i],
                altitude_labels[i],
            )

        output_path = args.output or args.input_file_path.with_name(
            f"{args.input_file_path.name}.fission_sites.png"
        )

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"\nPlot saved to: {output_path}")

        if not args.no_show:
            plt.show()

        plt.close()

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
