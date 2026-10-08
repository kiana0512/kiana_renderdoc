#pragma once

// Opt-in, observation-only diagnostics. Never handles or suppresses an exception.
bool KianaCrashDiagnosticsEnabled();
void KianaInstallCrashDiagnostics();
void KianaLogDiagnosticExit(const char *function, unsigned long code, unsigned long targetPID);
