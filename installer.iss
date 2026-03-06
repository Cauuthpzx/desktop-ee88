; installer.iss — Inno Setup script cho MaxHub
;
; Yeu cau: Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
;
; Cach dung:
;   1. Build app truoc: python build.py --version 1.0.0
;   2. Mo file nay trong Inno Setup Compiler
;   3. Bam Ctrl+F9 de compile thanh Setup_MaxHub_1.0.0.exe
;
; Hoac dung command line:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

#define MyAppName "MaxHub"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MaxHub Team"
#define MyAppURL "https://maxhub.app"
#define MyAppExeName "MaxHub.exe"
#define MyAppId "{{B7E3F4A1-9C2D-4E8F-A1B3-5D7E9F2C4A6B}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=Setup_{#MyAppName}_{#MyAppVersion}
SetupIconFile=icons\app\icon-taskbar.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Yeu cau quyen admin de cai vao Program Files
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Kich thuoc toi thieu cua o dia (bytes)
ExtraDiskSpaceRequired=0

; Thong tin version hien trong Properties cua Setup.exe
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Khoi dong cung Windows"; GroupDescription: "Tuy chon khac:"

[Files]
; Copy toan bo folder dist/MaxHub vao thu muc cai dat
Source: "dist\MaxHub\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Go {#MyAppName} {#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"

; Desktop shortcut (tuy chon)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Startup shortcut (tuy chon)
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
; Chay app sau khi cai dat xong (tuy chon)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Xoa cac file app tu tao (cache, settings, logs)
Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"

[Code]
// Kiem tra va dong app truoc khi cai dat/go cai dat
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
end;
