# Stage24 dual UI stackshot

Page 8 prints backboardd (B) and SpringBoard (S) from each snapshot. It
prints the selected thread ID and state, wait-info presence and kind,
recorded owner and context, and up to four user return addresses.
Ordinal 0 uses the existing main-thread-first ranking. Compare thread
IDs between samples. Stack frames start at index 2, or at 0 for short
stacks. The capture ends with an intentional diagnostic panic.
