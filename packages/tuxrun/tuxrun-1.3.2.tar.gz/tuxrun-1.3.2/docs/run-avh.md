# Running under AVH

TuxRun allows to run a linux kernel under AVH (Arm Virtual Hardware).

> Note: See the [architecture matrix](devices.md#avh-devices) for the supported devices.

## AVH API Authentication

AVH API token is required to authorize tuxrun for API access to AVH.

Log in to AVH with your Arm account at https://app.avh.arm.com. Navigate to
your profile by clicking on your name at the top right corner. Change to API
tab. Then click the GENERATE button to generate your AVH API Token.

The token can be passed to tuxrun using the `--secrets` option.

## Boot testing

To run a simple boot test on AVH i.mx93:

```shell
tuxrun --device avh-imx93 \
       --secrets avh_api_token=<token> \
       --kernel https://example.com/Image \
       --dtb https://example.com/devicetree \
       --rootfs https://example.com/rootfs.ext4 \
```

> Tip:
    "--kernel" needs a Linux kernel in the `Image` format.
    "--rootfs" needs a OS disk image in the `ext4` format.

## Modules overlay

TuxRun allows to provide a custom **modules.tar.xz** archive that will be
extracted on top of the rootfs.

```shell
tuxrun --device avh-imx93 \
       --secrets avh_api_token=<token> \
       --kernel https://example.com/Image \
       --dtb https://example.com/devicetree \
       --rootfs https://example.com/rootfs.ext4 \
       --modules modules.tar.xz \
       --partition 1
```

> Warning: The modules archive should be a **tar archive**, compressed with **xz**.

> Tip: "--partition" specifies the disk image root partition index for applying overlays.

## Boot arguments

The `--boot_args` option allows you to override the default Kernel bootargs
provided by the AVH model.

```shell
tuxrun --device avh-imx93 \
       --secrets avh_api_token=<token> \
       --kernel https://example.com/Image \
       --dtb https://example.com/devicetree \
       --rootfs https://example.com/rootfs.ext4 \
       --partition 1 \
       --boot-args "console=ttyLP0,115200 earlycon= root=/dev/mmcblk0p2"
```

> Warning: All boot args should be provided. Providing partial boot args may
lead to boot failure.

## Running tests

You can run a specific test with:

```shell
tuxrun --device avh-imx93 \
       --secrets avh_api_token=<token> \
       --kernel https://example.com/Image \
       --dtb https://example.com/devicetree \
       --rootfs https://example.com/rootfs.ext4 \
       --partition 1 \
       --tests ltp-smoke
```

> Tip: "Multiple tests"
    Multiple tests can be specified after **--tests**.
    The tests will be executed one by one, in the order specified on the command-line.
