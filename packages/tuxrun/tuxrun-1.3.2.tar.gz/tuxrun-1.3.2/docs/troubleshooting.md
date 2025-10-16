# Troubleshooting

## Failure on ubuntu

On Ubuntu, trying to update the root-filesystem will not work by default. You
will see the following error:

```
Unable to update image rootfs: "/usr/bin/supermin exited with error status 1.
To see full error messages you may need to enable debugging.
Do:
  export LIBGUESTFS_DEBUG=1 LIBGUESTFS_TRACE=1
and run the command again.

For further information, read:
  http://libguestfs.org/guestfs-faq.1.html#debugging-libguestfs
You can also run 'libguestfs-test-tool' and post the *complete* output
into a bug report or message to the libguestfs mailing list.
```

This is due to the Ubuntu bug
[759725](https://bugs.launchpad.net/ubuntu/+source/linux/+bug/759725). Under
Ubuntu, the kernel image are only readable by root. Having read-only access to
the host kernel image is required for TuxRun to update the rootf filesystem.

To workaround the issue you should execute:

```shell
dpkg-statoverride --force-statoverride-add \
                  --update \
                  --add root root 0644 \
                  "/boot/vmlinuz-$(uname -r)"
```

In order to fix the issue for the next kernels add `/etc/kernel/postinst.d/statoverride` with:

```shell
#!/bin/sh

set -e
version="$1"
if [ -z "$version" ]; then
    exit 0
fi
exec dpkg-statoverride --force-statoverride-add \
                       --update \
                       --add root root 0644 \
                       "/boot/vmlinuz-${version}"
```
