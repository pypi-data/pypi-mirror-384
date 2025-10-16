## Generic issues

Booting a kernel with a custom firmware may end up with a kernel that doesn't
boot or a call trace when trying to access something that isn't supported in
that firmware.

## Device specific issues

### qemu-arm64

When booting kernels older than 5.10, `tuxrun ... --parameters cpu.lpa2=off`
needs to be passed in to tuxrun too.
