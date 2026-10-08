#ifndef PackageDir
  #define PackageDir "..\dist\Kiana-1.47-v12-release-x64"
#endif
[Setup]
AppId={{D3321239-C56C-4383-9120-45E874A79D3D}
AppName=Kiana RenderDoc
AppVersion=1.47.12
AppVerName=Kiana RenderDoc 1.47 v12
AppPublisher=Kiana contributors
DefaultDirName={localappdata}\Kiana RenderDoc
DefaultGroupName=Kiana RenderDoc
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\packages
OutputBaseFilename=kiana_RenderDoc_1.47.12_x64_Setup
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\kiana_qrenderdoc.exe
CloseApplications=no
RestartApplications=no
SetupLogging=yes
LicenseFile=..\LICENSE.md

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#PackageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pdb,*.lib,*.exp,*.pyc,__pycache__\*"

[Icons]
Name: "{group}\Kiana RenderDoc"; Filename: "{app}\kiana_qrenderdoc.exe"; WorkingDir: "{app}"
Name: "{group}\MCP connection settings"; Filename: "{app}\mcp-client.json"
Name: "{autodesktop}\Kiana RenderDoc"; Filename: "{app}\kiana_qrenderdoc.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\python_mcp\python.exe"; Parameters: """{app}\mcp\configure.py"""; Flags: runhidden waituntilterminated
