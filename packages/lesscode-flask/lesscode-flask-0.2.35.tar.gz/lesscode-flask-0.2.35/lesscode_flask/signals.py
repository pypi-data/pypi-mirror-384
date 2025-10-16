from __future__ import annotations

from blinker import Namespace

_signals = Namespace()

# 应用运行的信号
app_runed = _signals.signal("app-runed")
