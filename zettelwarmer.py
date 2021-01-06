import datetime
from functools import total_ordering
import os
import pickle
import subprocess
import sys
from argparse import ArgumentParser
from math import ceil, sqrt

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Issues: Age 0 gibt ärger mit probability = NaN, only when total age 0

plt.rcParams["toolbar"] = "None"
NOW = datetime.datetime.now()


def plot_age_heatmap(ages_mins):
    aspect_ratio = 16 / 9
    # Result of minimizing number of rows for min||nrows^2 * ncols - len||_2^2
    # Could be improved by cleverly chosing if we ceil rows or cols, depending
    #  on which yields better coverage (this is safe option).
    num_rows = ceil(sqrt(len(ages_mins) * aspect_ratio + 4) / aspect_ratio)
    num_cols = ceil(aspect_ratio * num_rows)

    padded_len = num_cols * num_rows
    padded_ages_mins = np.pad(
        [*ages_mins],
        (0, padded_len - len(ages_mins)),
        "constant",
        constant_values=np.nan,
    )
    padded_ages_days = np.round(padded_ages_mins / (60 * 24))

    fig, ax = plt.subplots(
        num=f"{len(ages_mins)} Zettels, Median Age {np.median(ages_mins/(60*24)):.0f} days."
    )
    ax.tick_params(left=False, bottom=False, labelbottom=False, labelleft=False)
    ax.set_title("Days Since Last Visit To Zettel")

    im = ax.imshow(np.reshape([padded_ages_days], (num_rows, num_cols)))
    cax = make_axes_locatable(ax).append_axes("right", size="5%", pad=0.1)
    fig.colorbar(im, cax=cax)
    fig.tight_layout()
    plt.show()


def get_file_suffix(filepath):
    _, suffix = os.path.splitext(filepath)
    return suffix


def get_selection_probabilities(ages, importance_function="linear"):
    """
    Returns the probability of a Zettel being selected. This is proportional
    to the Zettels age.

    If importance_function == linear, that means if a Zettel is twice as old as another,
    it is also twice as likely to be picked.

    If importance_function == quadratic, that means a Zettel twice as old as another is
    four times as likely to be picked. This leads to faster getting to know the old ones.

    If importance_function == log, that means a Zettel twice as old as another is only
    a little bit more likely to be opened for review. This is kind of like having a
    uniform probability of picking notes, with the exception of new notes.
    """
    ages = np.array(ages)

    if importance_function == "linear":
        ages_weighted = ages
    elif importance_function == "quadratic":
        ages_weighted = np.power(ages, 2)
    elif importance_function == "log":
        ages_weighted = np.log(ages + 1)  # age could be below 1
    else:
        raise LookupError(f"Unknown importance function: {importance_function}")

    total_age = np.sum(ages_weighted)
    if total_age == 0:
        return np.ones_like(ages_weighted)

    return ages_weighted / total_age


def main(
    folder, visualize, interactive, numzettels, picklename, suffixes, visualize_only
):
    if visualize_only:
        visualize = True

    os.chdir(folder)

    zettels = os.listdir()
    zettels = [
        zett
        for zett in zettels
        if os.path.isfile(zett) and get_file_suffix(zett) in suffixes
    ]

    if numzettels > len(zettels):
        numzettels = len(zettels)

    if not os.path.isfile(picklename):
        print(
            "Couldn't find zettelwarmer database at {}. Making new one.".format(
                os.path.realpath(picklename)
            ),
            file=sys.stderr,
        )
        with open(picklename, "wb+") as fh:
            zettel_dates = {}
            age_in_mins = {}
            pickle.dump(zettel_dates, fh)
    else:
        with open(picklename, "rb") as fh:
            zettel_dates = pickle.load(fh)
            age_in_mins = {
                zettel: (NOW - last_opened).total_seconds() // 60
                for zettel, last_opened in zettel_dates.items()
            }

    oldest_age = -1
    if len(age_in_mins.values()) > 0:
        oldest_age = np.max(list(age_in_mins.values()))

    for zett in zettels:
        if zett not in age_in_mins:
            age_in_mins[zett] = oldest_age

    ages = np.array([age_in_mins[zett] for zett in zettels])
    selection_probabilities = get_selection_probabilities(
        ages, importance_function="quadratic"
    )
    sample_zettels = np.random.choice(
        zettels, size=numzettels, replace=False, p=selection_probabilities
    )

    if visualize:
        plot_age_heatmap(ages)

    open_and_update_files = True
    if interactive:
        print("Today's Zettels:")
        for zett in sample_zettels:
            print("  -", zett)

        user_input = input("Do you wanna open the files?")
        open_and_update_files = (user_input == "") or (user_input.lower() == "y")

    if not visualize_only and open_and_update_files:
        for zettel in sample_zettels:
            zettel_dates[zettel] = datetime.datetime.now()
            subprocess.run(["open", zettel])

        with open(picklename, "wb+") as fh:
            pickle.dump(zettel_dates, fh)
    else:
        print("Ok, not opening anything...")


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Tool to revisit random Zettels from your collection. Gives more weight to old Zettels that you haven't seen in a while."
    )
    parser.add_argument(
        "-f",
        "--folder",
        help="Path to folder with all the zettels in it. Defaults to current directory.",
        default=".",
    )
    parser.add_argument(
        "-p",
        "--picklename",
        help="Name of the pickle file to save file ages into. Will be saved in the Zettel folder.",
        default="zettelwarmer.pickle",
    )
    parser.add_argument(
        "-n",
        "--numzettels",
        help="Number of Zettels to pick and open.",
        default=5,
        type=int,
    )
    parser.add_argument(
        "-s",
        "--suffixes",
        help="List of valid suffixes to consider as Zettel files. Defaults to .md",
        nargs="+",
        default=[".md"],
    )
    parser.add_argument(
        "-i",
        "--interactive",
        help="Print stuff and ask if files should be opened.",
        action="store_true",
    )
    parser.add_argument(
        "-v", "--visualize", help="Show a heatmap of Zettel ages", action="store_true",
    )
    parser.add_argument(
        "-vo",
        "--visualize-only",
        help="Do not open or modify anything, only show the heatmap",
        action="store_true",
    )

    args = parser.parse_args()
    params = vars(args)

    main(**params)
