# drivers/LumingDisplayTouch — [missing] display + input component

[placeholder] No display service or touch input component exists for luming in format 2 yet.
This is deliberately not on the first-boot path: the first boot targets the XNU video console
(DarwinBoot fills `boot_args.Video[6]` from the UEFI GOP, and pexpert draws the console — dada's
first boot does exactly this). The display component becomes necessary for userland SpringBoard
(`IOMobileFramebuffer` service), which dada also still lacks.

## Inputs that already exist

- Panel/framebuffer facts: `docs/KNOWN-VALUES.md` #6 - FB base `0xFC800000`, stride 4944 B,
  1236x2750, splash `0x2b00000`; stock panel command `qcom,mdss_dsi_o9_42_02_0a_dsc_cmd`.
- A-line/format-1 display evidence: `agents/ufs-ci` (framebuffer console, panic screen,
  `REPORT-CLEAN*.md`), `agents/f2-luming/docs/A-FIX-CROSSWALK.md` section (c).
- Stock DT touch node and panel node are in `backup/analysis/device-live/luming-live/dtb-dump.json`.
- sheng's input stack (ShengHidInput + ShengNovatekTouch) is the format-2 reference shape, but its
  Novatek touch is SM8550 hardware; luming's touch controller must be identified from the stock DT.

## Needed

1. Display: a format-2 component that publishes an `IOMobileFramebuffer`-compatible service for the
   luming panel (or first validates presentation with a minimal framebuffer service), plus the
   board backlight/power rails.
2. Input: a component for luming keys (PMIC/SPMI) and touch (controller from stock DT), delivered
   through the Apple HID stack (`IOHIDEventService` as in sheng's ShengHidInput).
3. Both are prerequisites for S7 (userland GUI), not for S1-S6 (console + root).
