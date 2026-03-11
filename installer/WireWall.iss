#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDist
  #define SourceDist "..\\dist\\WireWall"
#endif
#ifndef ReleaseDir
  #define ReleaseDir "..\\release"
#endif
#ifndef BundleOllamaInstaller
  #define BundleOllamaInstaller 0
#endif
#ifndef OllamaInstallerSource
  #define OllamaInstallerSource "..\\build\\third_party\\OllamaSetup.exe"
#endif

#define AppName "WireWall"
#define AppPublisher "Ynov Campus"
#define AppExeName "WireWall.exe"
#define RecommendedModel "qwen2.5:3b"

[Setup]
AppId={{5A4E5F3D-6928-4A8C-95AB-B8C22FE367E2}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma
SolidCompression=yes
OutputDir={#ReleaseDir}
#if BundleOllamaInstaller
OutputBaseFilename=WireWall-Setup-{#AppVersion}-full
#else
OutputBaseFilename=WireWall-Setup-{#AppVersion}
#endif
PrivilegesRequired=admin
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked

[Files]
Source: "{#SourceDist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config.example.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\VERSION"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\scripts\check_target_prereqs.bat"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "..\scripts\check_target_prereqs.ps1"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "..\scripts\setup_ai.bat"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "..\scripts\check_ollama.ps1"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "..\scripts\install_ollama.ps1"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "..\scripts\install_ollama_model.ps1"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "..\scripts\setup_ai.ps1"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "{#OllamaInstallerSource}"; DestDir: "{app}\tools"; DestName: "OllamaSetup.exe"; Flags: ignoreversion skipifsourcedoesntexist

[Dirs]
Name: "{localappdata}\WireWall"; Permissions: users-modify
Name: "{localappdata}\WireWall\config"; Permissions: users-modify
Name: "{localappdata}\WireWall\logs"; Permissions: users-modify
Name: "{localappdata}\WireWall\exports"; Permissions: users-modify
Name: "{localappdata}\WireWall\data"; Permissions: users-modify
Name: "{localappdata}\WireWall\demo"; Permissions: users-modify

[Icons]
Name: "{autoprograms}\{#AppName}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autoprograms}\{#AppName}\Assistant IA locale"; Filename: "{app}\tools\setup_ai.bat"; WorkingDir: "{app}\tools"
Name: "{autoprograms}\{#AppName}\Diagnostic prerequis"; Filename: "{app}\tools\check_target_prereqs.bat"; WorkingDir: "{app}\tools"
#if BundleOllamaInstaller
Name: "{autoprograms}\{#AppName}\Installer Ollama local"; Filename: "{app}\tools\OllamaSetup.exe"; WorkingDir: "{app}\tools"
#endif
Name: "{autoprograms}\{#AppName}\Documentation"; Filename: "{app}\README.md"
Name: "{autoprograms}\{#AppName}\Desinstaller {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Lancer {#AppName}"; Flags: nowait postinstall skipifsilent unchecked
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\setup_ai.ps1"" -Model ""{#RecommendedModel}"""; Description: "Configurer Ollama et le modele IA local"; Flags: postinstall shellexec skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}\docs"
Type: filesandordirs; Name: "{app}\tools"

[Code]
function InitializeSetup(): Boolean;
begin
  MsgBox(
    'WireWall installe l''application locale et ses outils d''assistance.' + #13#10#13#10 +
    'Important :' + #13#10 +
    '- l''IA locale depend d''Ollama ; seul son installeur officiel peut etre embarque dans la variante full' + #13#10 +
    '- le modele recommande ({#RecommendedModel}) sera telecharge separement si vous lancez l''assistant' + #13#10 +
    '- les fonctions USBSTOR reelles restent conditionnees aux droits administrateur',
    mbInformation,
    MB_OK
  );
  Result := True;
end;
