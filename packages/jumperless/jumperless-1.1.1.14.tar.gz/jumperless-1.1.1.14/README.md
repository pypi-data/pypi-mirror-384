# Jumperless-App
An app to talk to your Jumperless V5

## Make Targets

List of useful `make` targets:
- `make app`: Runs the Jumperless App `JumperlessWokwiBridge.py` from source.
    All python dependencies are installed in a virtual environment.
    Also the default target, same as running bare `make`.
- `make package`: Builds the distributable packages, same as running `python3 Packager/JumperlessAppPackager.py`.
    All python dependencies are instaled in a dedicated virtual environment.

## Packager pip Versions

Specific package versions are stipulated in `Packager/constraints.txt`.
This keeps `Packager/packagerRequirements.txt` a little cleaner and allows for easier updating of versions.
To update package versions, just run `make Packager/constraints.txt`
