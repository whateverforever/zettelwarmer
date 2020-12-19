# Zettelwarmer

> An additional tool to Zettlr to randomly show you Zettels. Useful if you want to be reminded
> of what you have stored, and to find new possible interconnections.
>
> Gives more weight to Zettels that haven't been seen (by this tool) in a while. The older the
> Zettel, the more probable it will be picked.

```
(base) ➜  ~ python zettelwarmer.py --help
usage: zettelwarmer.py [-h] [-f FOLDER] [-p PICKLENAME] [-n NUMZETTELS]
                       [-s SUFFIXES [SUFFIXES ...]] [-i] [-v]

Tool to revisit random Zettels from your collection. Gives more weight to old
Zettels that you haven't seen in a while.

optional arguments:
  -h, --help            show this help message and exit
  -f FOLDER, --folder FOLDER
                        Path to folder with all the zettels in it. Defaults to
                        current directory.
  -p PICKLENAME, --picklename PICKLENAME
                        Name of the pickle file to save file ages into. Will
                        be saved in the Zettel folder.
  -n NUMZETTELS, --numzettels NUMZETTELS
                        Number of Zettels to pick and open.
  -s SUFFIXES [SUFFIXES ...], --suffixes SUFFIXES [SUFFIXES ...]
                        List of valid suffixes to consider as Zettel files.
                        Defaults to .md
  -i, --interactive     Print stuff and ask if files should be opened.
  -v, --visualize       Show a heatmap of Zettel ages
```

## Requirements

As of now, it's specific to macOS by using the built-in `open` command. This command is used
to launch a markdown viewer to open the Zettels. This also requires you to have a markdown viewer
like Typora or MacDown setup as the standard tool to open markdown files.