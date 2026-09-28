#pragma once

#include "common/common.h"
#include "os/os_specific.h"

// Opt-in observations only. Preserve Win32 last-error state around every log.
#define CAPTURE_PATH_DIAG(...)                                                        \
  do                                                                                 \
  {                                                                                  \
    const DWORD diagnosticLastError = GetLastError();                                 \
    static const bool diagnosticEnabled =                                            \
        Process::GetEnvVariable("RENDERTEST_CAPTURE_DIAGNOSTICS") == "1" ||             \
        Process::GetEnvVariable("KIANA_CAPTURE_DIAGNOSTICS") == "1";                    \
    if(diagnosticEnabled)                                                            \
      RDCLOG("Capture path: " __VA_ARGS__);                                            \
    SetLastError(diagnosticLastError);                                                \
  } while(0)
