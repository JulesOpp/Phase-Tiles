; Phase Tiles, the Windows installer.
;
;   pyinstaller --noconfirm packaging\windows.spec
;   iscc /DAppVersion=0.1.0 packaging\phase-tiles.iss
;
; Per-user (PrivilegesRequired=lowest): no UAC prompt, installs under
; {localappdata}\Programs, associations in HKCU -- a lab machine
; without admin rights can still install it.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName "Phase Tiles"
#define AppExeName "Phase Tiles.exe"
#define AppPublisher "Jules Oppenheim"
#define SourceDir "..\dist\Phase Tiles"

[Setup]
AppId={{6CACEDD0-4ECF-436F-9B5A-80C4BAD49D95}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=Phase-Tiles-{#AppVersion}-setup
SetupIconFile=icons\phase-tiles.ico
LicenseFile=..\LICENSE
AppPublisherURL=https://github.com/JulesOpp/Phase-Tiles
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; `lowest` + `autopf` = {localappdata}\Programs\Phase Tiles.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

; An upgrade must not leave the previous release's _internal beneath
; the new one (stale modules still import).  Nothing of the user's
; lives there: the cache and settings are in AppData\Roaming.
[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; \
    Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; \
    Tasks: desktopicon

[Registry]
; HKA under PrivilegesRequired=lowest is HKCU.  .phtiles is written
; only by this application, so the association is not optional.
Root: HKA; Subkey: "Software\Classes\PhaseTiles.phtiles"; \
    ValueType: string; ValueName: ""; \
    ValueData: "Phase Tiles diagram"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\PhaseTiles.phtiles\DefaultIcon"; \
    ValueType: string; ValueName: ""; \
    ValueData: "{app}\{#AppExeName},0"
Root: HKA; \
    Subkey: "Software\Classes\PhaseTiles.phtiles\shell\open\command"; \
    ValueType: string; ValueName: ""; \
    ValueData: """{app}\{#AppExeName}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\.phtiles"; ValueType: string; \
    ValueName: ""; ValueData: "PhaseTiles.phtiles"; \
    Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#AppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
