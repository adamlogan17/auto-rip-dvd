# auto-rip-dvd

A python script to rip DVDs to ISO, MP4 and MKV file formats

## Docker Windows Instructions

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
