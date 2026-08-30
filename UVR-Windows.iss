#define AppName "Ultimate Vocal Remover"
#define AppVersion "6.0.0"
#define AppPublisher "Ultimate Vocal Remover"
#define AppExecutable "Ultimate Vocal Remover.exe"

[Setup]
; Keep the original UVR Windows installer identity so v6 upgrades an existing
; v5.6.1 installation instead of creating a second Installed Apps entry.
AppId={{652AA21C-E084-435C-8ED9-4A29AC2731F1}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/TacoLover619/ultimatevocalremovergui
AppSupportURL=https://github.com/TacoLover619/ultimatevocalremovergui/issues
AppUpdatesURL=https://github.com/TacoLover619/ultimatevocalremovergui/releases
DefaultDirName={localappdata}\Programs\Ultimate Vocal Remover
DefaultGroupName=Ultimate Vocal Remover
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=UVR_v6.0.0_setup
SetupIconFile=gui_data\img\GUI-Icon.ico
UninstallDisplayIcon={app}\{#AppExecutable}
Compression=lzma2/max
LZMANumBlockThreads=4
SolidCompression=yes
DiskSpanning=yes
DiskSliceSize=1900000000
SlicesPerDisk=1
WizardStyle=modern dynamic
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
CloseApplications=yes
RestartApplications=no
ChangesAssociations=no
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} Windows installer
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
VersionInfoCopyright=Ultimate Vocal Remover contributors

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\Ultimate Vocal Remover\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; These are the v5.6.1 entry points. Remove them during an in-place upgrade so
; an existing Start Menu or Desktop shortcut cannot launch the old application.
; Model directories, settings, and downloaded user data are left in place.
Type: files; Name: "{app}\UVR.exe"
Type: files; Name: "{app}\UVR_Launcher.exe"

[Icons]
Name: "{group}\Ultimate Vocal Remover"; Filename: "{app}\{#AppExecutable}"; WorkingDir: "{app}"
Name: "{group}\Uninstall Ultimate Vocal Remover"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Ultimate Vocal Remover"; Filename: "{app}\{#AppExecutable}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExecutable}"; Description: "Launch Ultimate Vocal Remover"; Flags: nowait postinstall skipifsilent
