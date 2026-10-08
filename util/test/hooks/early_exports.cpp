// Run in a fresh process with the capture DLL and early_exports_consumer.dll paths.
// The host intentionally caches the real loader/resolver before capture is loaded.
#include <d3d11.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include "renderdoc/api/app/renderdoc_app.h"

#define CHECK(condition)                                                              \
  do                                                                                  \
  {                                                                                   \
    if(!(condition))                                                                  \
    {                                                                                 \
      printf("FAIL line %d: %s (error %lu)\n", __LINE__, #condition, GetLastError()); \
      return 1;                                                                       \
    }                                                                                 \
  } while(0)

static decltype(&GetProcAddress) nativeResolve = NULL;

// The cached system resolver is CFG-suppressed on the test OS. Bypass the compiler check
// only for this deliberate raw resolver call; calls to graphics exports remain CFG-checked.
__declspec(guard(nocf)) static FARPROC Resolve(HMODULE module, LPCSTR name)
{
  return nativeResolve(module, name);
}

int main(int argc, char **argv)
{
  setvbuf(stdout, NULL, _IONBF, 0);
  CHECK(argc >= 3);
  auto load = &LoadLibraryA;
  nativeResolve = &GetProcAddress;
  auto resolve = &Resolve;
  HMODULE provider = NULL;
  FARPROC original = NULL;
  BYTE originalCode[16] = {};
  if(argc > 3 && !strcmp(argv[3], "warm"))
  {
    provider = load("d3d12.dll");
    CHECK(provider);
    original = resolve(provider, "D3D12CreateDevice");
    CHECK(original);
    memcpy(originalCode, (void *)original, sizeof(originalCode));
  }
  else
  {
    CHECK(GetModuleHandleA("d3d12.dll") == NULL);
  }

  SetEnvironmentVariableA("RENDERTEST_CAPTURE_DIAGNOSTICS", "1");
  printf("Native loader=%p resolver=%p\n", load, resolve);
  printf("Loading capture DLL\n");
  HMODULE capture = load(argv[1]);
  CHECK(capture);
  printf("Capture DLL loaded\n");
  provider = GetModuleHandleA("d3d12.dll");
  CHECK(provider);
  printf("Resolving early export through %p, provider=%p\n", resolve, provider);
  FARPROC early = resolve(provider, "D3D12CreateDevice");
  printf("Resolved early export %p\n", early);
  CHECK(early);
  char identityValue[2] = {};
  const bool identity = GetEnvironmentVariableA("KIANA_EXPORT_IDENTITY", identityValue, 2) == 1 &&
                        identityValue[0] == '1';
  if(identity)
  {
    CHECK(GetProcAddress(provider, "D3D12CreateDevice") == early);
    HMODULE dxgi = GetModuleHandleA("dxgi.dll");
    CHECK(GetProcAddress(dxgi, "CreateDXGIFactory") == resolve(dxgi, "CreateDXGIFactory"));
    HMODULE d3d11 = GetModuleHandleA("d3d11.dll");
    CHECK(d3d11);
    CHECK(GetProcAddress(d3d11, "D3D11CreateDevice") == resolve(d3d11, "D3D11CreateDevice"));
    printf("PASS: hooked resolver retains DXGI, D3D11 and D3D12 provider export addresses\n");
  }
  BYTE patchedCode[16] = {};
  memcpy(patchedCode, (void *)early, sizeof(patchedCode));
  CHECK(!original || (original == early && memcmp(originalCode, patchedCode, sizeof(patchedCode))));
  CHECK(resolve(provider, "KianaMissingExport") == NULL);
  printf("Checked missing export\n");

  // Resolve the same export by ordinal through the unhooked resolver as well.
  BYTE *base = (BYTE *)provider;
  auto dos = (IMAGE_DOS_HEADER *)base;
  auto nt = (IMAGE_NT_HEADERS *)(base + dos->e_lfanew);
  auto exports =
      (IMAGE_EXPORT_DIRECTORY *)(base + nt->OptionalHeader.DataDirectory[0].VirtualAddress);
  auto names = (DWORD *)(base + exports->AddressOfNames);
  auto ordinals = (WORD *)(base + exports->AddressOfNameOrdinals);
  bool checkedOrdinal = false;
  for(DWORD i = 0; i < exports->NumberOfNames; i++)
    if(!strcmp((char *)(base + names[i]), "D3D12CreateDevice"))
    {
      CHECK(resolve(provider, MAKEINTRESOURCEA(exports->Base + ordinals[i])) == early);
      checkedOrdinal = true;
    }
  CHECK(checkedOrdinal);

  for(int attempt = 0; attempt < 2; attempt++)
  {
    printf("Loading consumer %d\n", attempt);
    HMODULE consumer = load(argv[2]);
    CHECK(consumer);
    auto tls = (FARPROC(*)())resolve(consumer, "GetTLSEntry");
    auto attach = (FARPROC(*)())resolve(consumer, "GetAttachEntry");
    CHECK(tls && attach);
    printf("TLS entry=%p attach entry=%p expected=%p\n", tls(), attach(), early);
    CHECK(tls() == early);
    CHECK(attach() == early);
    CHECK(FreeLibrary(consumer));
  }
  printf("PASS: TLS, DllMain, DLL reload, name/ordinal lookup through original loader/resolver\n");

  // Exercise D3D12GetInterface's SDK configuration path, not just D3D12CreateDevice.
  auto getInterface = (PFN_D3D12_GET_INTERFACE)resolve(provider, "D3D12GetInterface");
  CHECK(getInterface);
  ID3D12SDKConfiguration *configuration = NULL;
  CHECK(SUCCEEDED(getInterface(CLSID_D3D12SDKConfiguration, IID_PPV_ARGS(&configuration))));
  CHECK(configuration);
  configuration->Release();

  auto getAPI = (pRENDERDOC_GetAPI)resolve(capture, "RENDERDOC_GetAPI");
  CHECK(getAPI);
  RENDERDOC_API_1_6_0 *api = NULL;
  CHECK(getAPI(eRENDERDOC_API_Version_1_6_0, (void **)&api) == 1);

  // A real WARP device verifies onward pointers and device wrapping without depending on a
  // particular GPU. Factory creation must also work through the patched DXGI export.
  auto factoryFn = (HRESULT(WINAPI *)(REFIID, void **))resolve(GetModuleHandleA("dxgi.dll"),
                                                               "CreateDXGIFactory1");
  CHECK(factoryFn);
  IDXGIFactory4 *factory = NULL;
  CHECK(SUCCEEDED(factoryFn(IID_PPV_ARGS(&factory))));
  IDXGIAdapter *warp = NULL;
  CHECK(SUCCEEDED(factory->EnumWarpAdapter(IID_PPV_ARGS(&warp))));
  ID3D12Device *device = NULL;
  CHECK(SUCCEEDED(
      ((PFN_D3D12_CREATE_DEVICE)early)(warp, D3D_FEATURE_LEVEL_11_0, IID_PPV_ARGS(&device))));
  api->StartFrameCapture(device, NULL);
  CHECK(api->IsFrameCapturing() == 1);
  CHECK(api->DiscardFrameCapture(device, NULL) == 1);
  device->Release();
  warp->Release();
  factory->Release();
  printf("PASS: SDK configuration, DXGI factory, WARP device, capture start/discard\n");

  if(identity)
  {
    auto create11 =
        (PFN_D3D11_CREATE_DEVICE)GetProcAddress(GetModuleHandleA("d3d11.dll"), "D3D11CreateDevice");
    ID3D11Device *device11 = NULL;
    ID3D11DeviceContext *context11 = NULL;
    CHECK(SUCCEEDED(create11(NULL, D3D_DRIVER_TYPE_WARP, NULL, 0, NULL, 0, D3D11_SDK_VERSION,
                             &device11, NULL, &context11)));
    api->StartFrameCapture(device11, NULL);
    CHECK(api->IsFrameCapturing() == 1);
    CHECK(api->DiscardFrameCapture(device11, NULL) == 1);
    context11->Release();
    device11->Release();
    printf("PASS: preserved D3D11 export still registers a wrapped frame capturer\n");

    // Applications opting out of device wrapping still require every requested API output.
    const UINT rawFlags = D3D11_CREATE_DEVICE_PREVENT_ALTERING_LAYER_SETTINGS_FROM_REGISTRY;
    device11 = NULL;
    context11 = NULL;
    CHECK(SUCCEEDED(create11(NULL, D3D_DRIVER_TYPE_WARP, NULL, rawFlags, NULL, 0, D3D11_SDK_VERSION,
                             &device11, NULL, &context11)));
    CHECK(device11 && context11);
    char overrideValue[2] = {};
    const bool overrideEnabled =
        GetEnvironmentVariableA("KIANA_D3D11_CAPTURE_OVERRIDE", overrideValue, 2) == 1 &&
        overrideValue[0] == '1';
    HMODULE implementation = NULL;
    CHECK(GetModuleHandleExA(
        GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        (LPCSTR)(*(void ***)device11)[0], &implementation));
    CHECK((implementation == capture) == overrideEnabled);
    ID3D11Device *contextDevice = NULL;
    context11->GetDevice(&contextDevice);
    CHECK(contextDevice == device11);
    context11->ClearState();
    contextDevice->Release();
    context11->Release();
    device11->Release();

    // D3D11 permits requesting only the immediate context, with no device output.
    context11 = NULL;
    CHECK(SUCCEEDED(create11(NULL, D3D_DRIVER_TYPE_WARP, NULL, rawFlags, NULL, 0, D3D11_SDK_VERSION,
                             NULL, NULL, &context11)));
    CHECK(context11);
    context11->ClearState();
    context11->Release();
    printf("PASS: D3D11 opt-out/override preserves device/context and context-only outputs\n");
  }

  api->RemoveHooks();
  FARPROC restored = resolve(provider, "D3D12CreateDevice");
  CHECK(restored == early);
  CHECK(memcmp(patchedCode, (void *)restored, sizeof(patchedCode)) != 0);
  CHECK(!original || original == restored);
  CHECK(!original || memcmp(originalCode, (void *)restored, sizeof(originalCode)) == 0);
  // A pointer obtained before RemoveHooks remains callable after export restoration.
  CHECK(SUCCEEDED(((PFN_D3D12_CREATE_DEVICE)early)(NULL, D3D_FEATURE_LEVEL_11_0,
                                                   __uuidof(ID3D12Device), NULL)));
  api->RemoveHooks();
  CHECK(resolve(provider, "D3D12CreateDevice") == restored);
  printf("PASS: original code restoration, cached pointer, repeated RemoveHooks\n");
  return 0;
}
