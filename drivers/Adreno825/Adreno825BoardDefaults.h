/* SPDX-License-Identifier: MIT */
#ifndef ADRENO825_BOARD_DEFAULTS_H
#define ADRENO825_BOARD_DEFAULTS_H

#include "Adreno830Board.h"

/*
 * Fill the A825 board view from the stock luming DTB and the stock msm_kgsl.ko
 * tables. The caller may override any field before Adreno830Start consumes it.
 *
 * [missing] SCM waitq IRQ and the exact GPU/LPAC stream-match slot/CB mapping
 * are not in the stock firmware; this fill uses the documented Gen8 convention
 * and leaves the SCM waitq at 0 (the driver polls when it is absent).
 */
void Adreno825BoardFill(Adreno830Board *board);

#endif /* ADRENO825_BOARD_DEFAULTS_H */
