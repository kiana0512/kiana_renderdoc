#include "win32_crash_diagnostics.h"
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>

static HANDLE s_DiagnosticFile = INVALID_HANDLE_VALUE;
static thread_local bool s_Logging = false;

bool KianaCrashDiagnosticsEnabled()
{
  DWORD error = GetLastError();
  char enabled[2] = {};
  bool result =
      GetEnvironmentVariableA("KIANA_CRASH_DIAGNOSTICS", enabled, 2) == 1 && enabled[0] == '1';
  SetLastError(error);
  return result;
}

static void Append(char *text, size_t capacity, size_t &used, const char *format, ...)
{
  if(used >= capacity - 1)
    return;
  va_list args;
  va_start(args, format);
  int length = _vsnprintf_s(text + used, capacity - used, _TRUNCATE, format, args);
  va_end(args);
  if(length >= 0)
    used += length;
  else
    used = capacity - 1;
}

static void AppendAddress(char *text, size_t capacity, size_t &used, void *address)
{
  HMODULE module = NULL;
  char path[MAX_PATH] = {};
  if(GetModuleHandleExA(
         GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
         (LPCSTR)address, &module))
    GetModuleFileNameA(module, path, MAX_PATH);
  const char *name = strrchr(path, '\\');
  name = name ? name + 1 : path;
  Append(text, capacity, used, "  %p %s+0x%llx\r\n", address, name[0] ? name : "unknown",
         (unsigned long long)((uintptr_t)address - (uintptr_t)module));
}

static void Log(const char *reason, DWORD code, DWORD targetPID, EXCEPTION_POINTERS *exception)
{
  if(s_DiagnosticFile == INVALID_HANDLE_VALUE || s_Logging)
    return;
  DWORD error = GetLastError();
  s_Logging = true;
  char text[16384] = {};
  size_t used = 0;
  SYSTEMTIME now = {};
  GetSystemTime(&now);
  Append(text, sizeof(text), used,
         "\r\n%02u:%02u:%02u.%03u UTC pid=%lu tid=%lu %s code=0x%08lx (%lu) target=%lu\r\n",
         now.wHour, now.wMinute, now.wSecond, now.wMilliseconds, GetCurrentProcessId(),
         GetCurrentThreadId(), reason, code, code, targetPID);
  if(exception)
  {
    Append(text, sizeof(text), used, "exception address:\r\n");
    AppendAddress(text, sizeof(text), used, exception->ExceptionRecord->ExceptionAddress);
    if(code == EXCEPTION_ACCESS_VIOLATION && exception->ExceptionRecord->NumberParameters >= 2)
      Append(text, sizeof(text), used, "access=%llu address=%p\r\n",
             (unsigned long long)exception->ExceptionRecord->ExceptionInformation[0],
             (void *)exception->ExceptionRecord->ExceptionInformation[1]);
#if defined(_WIN64)
    CONTEXT context = *exception->ContextRecord;
    __try
    {
      for(int i = 0; i < 32 && context.Rip; i++)
      {
        AppendAddress(text, sizeof(text), used, (void *)context.Rip);
        DWORD64 imageBase = 0;
        PRUNTIME_FUNCTION function = RtlLookupFunctionEntry(context.Rip, &imageBase, NULL);
        if(function)
        {
          PVOID handlerData = NULL;
          DWORD64 establisherFrame = 0;
          RtlVirtualUnwind(UNW_FLAG_NHANDLER, imageBase, context.Rip, function, &context,
                           &handlerData, &establisherFrame, NULL);
        }
        else
        {
          context.Rip = *(DWORD64 *)context.Rsp;
          context.Rsp += sizeof(DWORD64);
        }
      }
    }
    __except(EXCEPTION_EXECUTE_HANDLER)
    {
      Append(text, sizeof(text), used, "stack unwind stopped at unreadable frame\r\n");
    }
#endif
  }
  else
  {
    void *frames[32] = {};
    USHORT count = CaptureStackBackTrace(2, 32, frames, NULL);
    for(USHORT i = 0; i < count; i++)
      AppendAddress(text, sizeof(text), used, frames[i]);
  }
  DWORD written = 0;
  WriteFile(s_DiagnosticFile, text, (DWORD)used, &written, NULL);
  FlushFileBuffers(s_DiagnosticFile);
  s_Logging = false;
  SetLastError(error);
}

static LONG CALLBACK ObserveException(EXCEPTION_POINTERS *exception)
{
  DWORD code = exception->ExceptionRecord->ExceptionCode;
  if(code == EXCEPTION_ACCESS_VIOLATION || code == EXCEPTION_ILLEGAL_INSTRUCTION ||
     code == EXCEPTION_STACK_OVERFLOW || code == 0xC0000409 || code == 0xC0000374)
    Log("first-chance exception", code, GetCurrentProcessId(), exception);
  return EXCEPTION_CONTINUE_SEARCH;
}

void KianaInstallCrashDiagnostics()
{
  if(!KianaCrashDiagnosticsEnabled() || s_DiagnosticFile != INVALID_HANDLE_VALUE)
    return;
  DWORD error = GetLastError();
  wchar_t path[1024] = {};
  DWORD length = GetEnvironmentVariableW(L"KIANA_CRASH_LOG", path, 1024);
  if(length > 0 && length < 1024)
  {
    s_DiagnosticFile =
        CreateFileW(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                    NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if(s_DiagnosticFile != INVALID_HANDLE_VALUE)
    {
      AddVectoredExceptionHandler(1, ObserveException);
      Log("diagnostic observer installed", 0, GetCurrentProcessId(), NULL);
    }
  }
  SetLastError(error);
}

void KianaLogDiagnosticExit(const char *function, unsigned long code, unsigned long targetPID)
{
  Log(function, code, targetPID, NULL);
}
