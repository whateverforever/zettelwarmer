import datetime
import os
import pickle
import subprocess
import sys
from argparse import ArgumentParser

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Issues: Age 0 gibt ärger mit probability = NaN, only when total age 0

plt.rcParams["toolbar"] = "None"
NOW = datetime.datetime.now()


def plot_age_heatmap(ages_mins):
    """
    Only qualitative, since entries can repeat themselves. This is due to
    forcing the heatmap into a specific aspect ratio and padding the data
    with np.resize
    """
    VIS_WIDTH = 16
    VIS_HEIGHT = 9
    x = int(np.ceil(np.sqrt(len(ages_mins) / (VIS_HEIGHT * VIS_WIDTH))))
    padded_ages_mins = np.resize([*ages_mins], VIS_HEIGHT * VIS_WIDTH * x * x)
    padded_ages_days = padded_ages_mins / (60 * 24)

    fig, ax = plt.subplots()
    ax.tick_params(left=False, bottom=False, labelbottom=False, labelleft=False)
    ax.set_title("Time Since Last Visit To Zettel [Days]")

    im = ax.imshow(np.reshape([padded_ages_days], (VIS_HEIGHT * x, VIS_WIDTH * x)))
    cax = make_axes_locatable(ax).append_axes("right", size="5%", pad=0.1)
    fig.colorbar(im, cax=cax)
    fig.tight_layout()
    plt.show()


def get_file_suffix(filepath):
    _, suffix = os.path.splitext(filepath)
    return suffix


def main(folder, visualize, interactive, numzettels, picklename, suffixes):
    os.chdir(folder)

    zettels = os.listdir()
    zettels = [
        zett
        for zett in zettels
        if os.path.isfile(zett) and get_file_suffix(zett) in suffixes
    ]

    if not os.path.isfile(picklename):
        print("Couldn't find zettelwarmer database at {}. Making new one.".format(
            os.path.realpath(picklename)
        ), file=sys.stderr)
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
    total_age = np.sum(ages)
    selection_probabilities = ages / total_age
    sample_zettels = np.random.choice(
        zettels, size=numzettels, replace=False, p=selection_probabilities
    )

    if visualize:
        plot_age_heatmap(ages)

    open_files = True
    if interactive:
        print("Today's Zettels:")
        for zett in sample_zettels:
            print("  -", zett)

        user_input = input("Do you wanna open the files?")
        open_files = (user_input == "") or (user_input.lower() == "y")

    if open_files:
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

    args = parser.parse_args()
    params = vars(args)

    main(**params)
