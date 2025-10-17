# Retrophase

Retrophase is a software to retrospectively change the phase of measurements recorded with a lock-in amplifier.
The input files are expected to be tab-separated \*.csv files with three columns: The frequency, the in-phase (X) and quadrature (Y) signals of the lock-in amplifier.

Retrophase can be started with a GUI by running
```bash
retrophase
```
in the terminal.
Files can be loaded via drag-and-drop or via the menu.
The phases of the loaded files can be modified either manually or can be set automatically to the value that results in the highest intensity in the spectrum (*Auto Phase*).

To automatically optimize files without opening a GUI, retrophase can be run with the additional *-a* flag
```bash
retrophase -a path/to/files/*.dat
```