# kits/ — board kits

Format 2 places the device `package/` as `kits/luming` in the resolved tree. This directory is for
additional board-owned kit directories (a kit is a directory with `Kit.toml`; see
UniXNU docs/porting/device-repository.md "Package and kits").

[placeholder] No separate luming kit is authored yet. The format-1 `LumingKit` stub was copied into
`package/LumingKit/Kit.toml` as reference; it must be re-derived for the format-2 package layout
before it is enabled.
