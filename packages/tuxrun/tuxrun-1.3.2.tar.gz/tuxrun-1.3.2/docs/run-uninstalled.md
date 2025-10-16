# Running TuxRun uninstalled

- TuxRun requires Python 3.6 or newer.
- The default runtime is podman, you should install it.
- TuxRun operates with Podman 4 inside the container. If the Podman version on the host mismatches, particularly with the FVP device type, this could lead to issues.


If you don't want to or can't install TuxRun, you can run it directly from the
source directory. After getting the sources via git or something else, there is
a `run` script that will do the right thing for you: you can either use that
script directly, or symlink it to a directory in your `PATH`.

```shell
/path/to/tuxrun/run --help
sudo ln -s /path/to/tuxrun/run /usr/local/bin/tuxrun && tuxrun --help
```
