// Regression fixture: call D3D12 before LoadLibrary returns, when the ordinary IAT scan
// has not yet had an opportunity to patch this DLL. No GPU is needed for this probe.
#include <d3d12.h>
#include <windows.h>

static const GUID UnsupportedDevice = {0x713cd154, 0x3c50, 0x4f25, {0x80, 0x13, 0, 0, 0, 0, 0, 1}};
static FARPROC tlsEntry = NULL;
static FARPROC attachEntry = NULL;
extern "C" FARPROC __imp_D3D12CreateDevice;

static void Probe(FARPROC &entry)
{
  entry = __imp_D3D12CreateDevice;
  void *device = NULL;
  D3D12CreateDevice(NULL, D3D_FEATURE_LEVEL_11_0, UnsupportedDevice, &device);
}

static void NTAPI TLSCallback(PVOID, DWORD reason, PVOID)
{
  if(reason == DLL_PROCESS_ATTACH)
    Probe(tlsEntry);
}

#pragma section(".CRT$XLB", long, read)
extern "C" __declspec(allocate(".CRT$XLB")) const PIMAGE_TLS_CALLBACK earlyExportTLS = TLSCallback;
#ifdef _WIN64
#pragma comment(linker, "/include:_tls_used")
#pragma comment(linker, "/include:earlyExportTLS")
#else
#pragma comment(linker, "/include:__tls_used")
#pragma comment(linker, "/include:_earlyExportTLS")
#endif

extern "C" __declspec(dllexport) FARPROC GetTLSEntry()
{
  return tlsEntry;
}
extern "C" __declspec(dllexport) FARPROC GetAttachEntry()
{
  return attachEntry;
}

BOOL WINAPI DllMain(HINSTANCE, DWORD reason, LPVOID)
{
  if(reason == DLL_PROCESS_ATTACH)
    Probe(attachEntry);
  return TRUE;
}
