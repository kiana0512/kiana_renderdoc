// GPU integration fixture: two independent VkInstances / devices, both offscreen.
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#define VK_NO_PROTOTYPES
#include "renderdoc/driver/vulkan/official/vulkan.h"
#include "renderdoc/api/app/renderdoc_app.h"

#define CHECK(x) do { if(!(x)) { printf("FAIL line %d: %s\n", __LINE__, #x); return 1; } } while(0)
#define VKCHECK(x) CHECK((x) == VK_SUCCESS)
static const char *(__cdecl *getLogFile)() = NULL;
static char logDestination[2048] = {};
static void SaveLog() { if(getLogFile) CopyFileA(getLogFile(), logDestination, FALSE); }
#define FUNCTIONS(F) F(vkDestroyInstance) F(vkEnumeratePhysicalDevices) F(vkGetPhysicalDeviceQueueFamilyProperties) \
 F(vkCreateDevice) F(vkDestroyDevice) F(vkGetDeviceQueue) F(vkCreateBuffer) F(vkGetBufferMemoryRequirements) \
 F(vkAllocateMemory) F(vkBindBufferMemory) F(vkCreateCommandPool) F(vkAllocateCommandBuffers) \
 F(vkBeginCommandBuffer) F(vkCmdFillBuffer) F(vkEndCommandBuffer) F(vkQueueSubmit) F(vkDeviceWaitIdle) \
 F(vkDestroyBuffer) F(vkFreeMemory) F(vkDestroyCommandPool)
#define DECLARE(fn) PFN_##fn fn = NULL;
FUNCTIONS(DECLARE)

struct Device
{
  VkInstance instance = VK_NULL_HANDLE;
  VkDevice device = VK_NULL_HANDLE;
  VkQueue queue = VK_NULL_HANDLE;
  VkBuffer buffer = VK_NULL_HANDLE;
  VkDeviceMemory memory = VK_NULL_HANDLE;
  VkCommandPool pool = VK_NULL_HANDLE;
  VkCommandBuffer command = VK_NULL_HANDLE;
};

void Cleanup(Device &d)
{
  if(d.device)
  {
    vkDeviceWaitIdle(d.device);
    vkDestroyCommandPool(d.device, d.pool, NULL);
    vkDestroyBuffer(d.device, d.buffer, NULL);
    vkFreeMemory(d.device, d.memory, NULL);
    vkDestroyDevice(d.device, NULL);
    d.device = VK_NULL_HANDLE;
  }
}

int main(int argc, char **argv)
{
  setvbuf(stdout, NULL, _IONBF, 0);
  CHECK(argc == 4);
  const bool linked = strcmp(argv[3], "off") != 0;
  const bool destroyFollower = strcmp(argv[3], "destroy") == 0;
  SetEnvironmentVariableA("KIANA_VULKAN_MULTIDEVICE", linked ? "1" : "0");
  HMODULE capture = LoadLibraryA(argv[1]);
  CHECK(capture);
  getLogFile = (const char *(__cdecl *)())GetProcAddress(capture, "RENDERDOC_GetLogFile");
  snprintf(logDestination, sizeof(logDestination), "%s.diagnostics.log", argv[2]);
  atexit(SaveLog);
  auto getAPI = (pRENDERDOC_GetAPI)GetProcAddress(capture, "RENDERDOC_GetAPI");
  RENDERDOC_API_1_6_0 *api = NULL;
  CHECK(getAPI && getAPI(eRENDERDOC_API_Version_1_6_0, (void **)&api));
  api->SetCaptureFilePathTemplate(argv[2]);
  HMODULE loader = LoadLibraryA("vulkan-1.dll");
  CHECK(loader);
  auto getInstanceProc = (PFN_vkGetInstanceProcAddr)GetProcAddress(loader, "vkGetInstanceProcAddr");
  auto createInstance = (PFN_vkCreateInstance)getInstanceProc(NULL, "vkCreateInstance");
  CHECK(createInstance);
  Device devices[2];
  for(int i = 0; i < 2; ++i)
  {
    Device &d = devices[i];
    VkApplicationInfo app = {VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.pApplicationName = "Kiana linked capture regression";
    app.apiVersion = VK_API_VERSION_1_1;
    VkInstanceCreateInfo ci = {VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    ci.pApplicationInfo = &app;
    const char *layer = "VK_LAYER_KIANA_RENDERDOC_Capture";
    ci.enabledLayerCount = 1;
    ci.ppEnabledLayerNames = &layer;
    VKCHECK(createInstance(&ci, NULL, &d.instance));
#define LOAD(fn) fn = (PFN_##fn)getInstanceProc(d.instance, #fn); CHECK(fn);
    FUNCTIONS(LOAD)
    uint32_t count = 0;
    VKCHECK(vkEnumeratePhysicalDevices(d.instance, &count, NULL));
    CHECK(count > 0);
    std::vector<VkPhysicalDevice> physical(count);
    VKCHECK(vkEnumeratePhysicalDevices(d.instance, &count, physical.data()));
    vkGetPhysicalDeviceQueueFamilyProperties(physical[0], &count, NULL);
    std::vector<VkQueueFamilyProperties> queues(count);
    vkGetPhysicalDeviceQueueFamilyProperties(physical[0], &count, queues.data());
    uint32_t family = 0;
    while(family < count && !(queues[family].queueFlags & VK_QUEUE_GRAPHICS_BIT)) ++family;
    CHECK(family < count);
    float priority = 1;
    VkDeviceQueueCreateInfo qi = {VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    qi.queueFamilyIndex = family; qi.queueCount = 1; qi.pQueuePriorities = &priority;
    VkDeviceCreateInfo di = {VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    di.queueCreateInfoCount = 1; di.pQueueCreateInfos = &qi;
    VKCHECK(vkCreateDevice(physical[0], &di, NULL, &d.device));
    vkGetDeviceQueue(d.device, family, 0, &d.queue);
    VkBufferCreateInfo bi = {VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    bi.size = 256; bi.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT; bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VKCHECK(vkCreateBuffer(d.device, &bi, NULL, &d.buffer));
    VkMemoryRequirements req = {};
    vkGetBufferMemoryRequirements(d.device, d.buffer, &req);
    VkMemoryAllocateInfo ai = {VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    ai.allocationSize = req.size;
    while(!(req.memoryTypeBits & (1U << ai.memoryTypeIndex))) ++ai.memoryTypeIndex;
    VKCHECK(vkAllocateMemory(d.device, &ai, NULL, &d.memory));
    VKCHECK(vkBindBufferMemory(d.device, d.buffer, d.memory, 0));
    VkCommandPoolCreateInfo pi = {VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    pi.queueFamilyIndex = family;
    VKCHECK(vkCreateCommandPool(d.device, &pi, NULL, &d.pool));
    VkCommandBufferAllocateInfo cb = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    cb.commandPool = d.pool; cb.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY; cb.commandBufferCount = 1;
    VKCHECK(vkAllocateCommandBuffers(d.device, &cb, &d.command));
    printf("Ready device %d\n", i);
  }
  void *owner = RENDERDOC_DEVICEPOINTER_FROM_VKINSTANCE(devices[0].instance);
  api->StartFrameCapture(owner, NULL);
  CHECK(api->IsFrameCapturing());
  for(int i = 0; i < 2; ++i)
  {
    Device &d = devices[i];
    VkCommandBufferBeginInfo begin = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    VKCHECK(vkBeginCommandBuffer(d.command, &begin));
    vkCmdFillBuffer(d.command, d.buffer, 0, 256, 0x12340000U + i);
    VKCHECK(vkEndCommandBuffer(d.command));
    VkSubmitInfo submit = {VK_STRUCTURE_TYPE_SUBMIT_INFO};
    submit.commandBufferCount = 1; submit.pCommandBuffers = &d.command;
    VKCHECK(vkQueueSubmit(d.queue, 1, &submit, VK_NULL_HANDLE));
    VKCHECK(vkDeviceWaitIdle(d.device));
  }
  if(destroyFollower) Cleanup(devices[1]);
  CHECK(api->EndFrameCapture(owner, NULL));
  CHECK(!api->IsFrameCapturing());
  uint32_t expected = linked && !destroyFollower ? 2 : 1;
  printf("Captured %u files, expected %u\n", api->GetNumCaptures(), expected);
  CHECK(api->GetNumCaptures() == expected);
  for(Device &d : devices) { Cleanup(d); vkDestroyInstance(d.instance, NULL); }
  printf("PASS: linked Vulkan %s\n", argv[3]);
  return 0;
}
