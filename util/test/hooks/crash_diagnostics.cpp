// Verify that the optional observer leaves SEH handling and process exit unchanged.
#include <windows.h>

int main(int argc, char **argv)
{
  if(argc != 2 || !LoadLibraryA(argv[1]))
    return 1;
  __try
  {
    RaiseException(EXCEPTION_ACCESS_VIOLATION, 0, 0, NULL);
  }
  __except(EXCEPTION_EXECUTE_HANDLER)
  {
  }
  ExitProcess(999);
}
