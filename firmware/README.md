# Public firmware patch subset

Only the small, self-authored UniXNU boot-image header patch needed by the CI bootimg step is
mirrored here. Firmware builds, Mu-Silicium sources, vendor `Binaries/luming` and the 385 MB UEFI
bundle are deliberately absent from this public repository; the private CI downloads the UEFI
bundle from the private repository at run time.
