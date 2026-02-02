# auto-rip-dvd

A python script to rip DVDs to ISO, MP4 and MKV file formats

## UV

It was chosen to use the [uv](https://docs.astral.sh/uv/) Python package manager for this project.

For the `uv` script to work, the package code must be within a `src` folder and the function that the script is to execute must be within `__init__.py`. The `uv` docs surrounding packaged applications can be found [here](https://docs.astral.sh/uv/concepts/projects/init/#packaged-applications).

Dev dependencies can be installed by `uv sync --frozen --dev`.

`uv run auto-rip-dvd` can be used to run the application.

### Ruff

[ruff](https://docs.astral.sh/ruff/) is the chosen linter for this project. It is built by astral, the same compony who manages `uv`. If using VS code, it is recommended to install the [ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) extension.

To run a check use the `uv run ruff check` command, and to automatically fix the errors add the `--fix` argument.

A list of it's rules can be found [here](https://docs.astral.sh/ruff/rules/).

### Pyright

`pyright` is the chosen type checker for this project. If using VS code, it is recommended to install the [pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) extension.

## MakeMKV

A free registration key can be found [here](https://forum.makemkv.com/forum/viewtopic.php?t=1053).

## Docker

If wishing to run the program using `docker compose` the 2 following commands must be used.

The environment variable `PLEX_CLAIM_CODE` is required for plex to set up. Go [here](https://account.plex.tv/en-GB/claim) to generate this claim code.

```console
docker compose up -d
docker exec -it auto-ripping uv run --frozen auto-rip-dvd
```

To stop the containers from running, use the command below.

```console
docker compose down
```

### Docker Windows Instructions

It is first important to note, that DVD drives are not supported with docker and Windows. This means that there must be inserted when the docker container is ran. It is possible to still use the `docker-compose.yaml` file to launch `plex` and `jellyfin` and simply let the `auto-rip` container fail, and the `auto-rip.py` script can be ran on the host system.

If wishing to use Docker on windows, it is important to note that you first must need to mount it to WSL.

This is due to WSL not automatically registering external drives.

You can do this with the below commands.

```console
wsl --distribution docker-desktop
mkdir /mnt/host/<<path-to-drive-lowercase>>
mount -t drvfs <<path-to-drive>> /mnt/host/<<path-to-drive-lowercase>>
```

## Useful Links

- <https://www.howtogeek.com/331053/how-to-mount-removable-drives-and-network-locations-in-the-windows-subsystem-for-linux/>

## Naming Conventions

How movies and TV shows are named are based of the advice given from Jellyfin and Plex. At the time of development, the naming convention is the same for both Plex and Jellyfin.

### Plex

- [TV Show Naming](https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/)
- [Movie Naming](https://support.plex.tv/articles/naming-and-organizing-your-movie-media-files/)

### Jellyfin

- [TV Show Naming](https://jellyfin.org/docs/general/server/media/shows/)
- [Movie Naming](https://jellyfin.org/docs/general/server/media/movies)

## TODO

- Get cast info for each episode
- Maybe create a shell/powershell script that detects the DVD, spins up docker container to do ripping, once container is finished, spin it back down and eject disc
- Maybe do the above all in the docker container so no starting required
- Test in linux machine
- Youtube to mp3, support?
  - This would require auth to the youtube API, to access playlists
- The below is not necessary and could probably allow the users to download and set these up themselves (may be considerable less complicated)
- Plex in docker-compose
- Jellyfin in docker-compose
- Add .plexmatch file [here](https://support.plex.tv/articles/plexmatch/)
- Disable auto update check [forum](https://forum.makemkv.com/forum/viewtopic.php?t=8397)
- Refactor the `auto-rip.py` script (especially the `dvd_rip_workflow`) function
- Add a `Getting Started` section