[Setup]
AppName=Markdown to PDF Converter Pro
AppVersion=1.0.0
DefaultDirName={autopf}\MarkdownToPDF
DefaultGroupName=MarkdownToPDF
OutputDir=dist
OutputBaseFilename=MarkdownToPDF_Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\MarkdownToPDF.exe

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "MarkdownToPDF.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MarkdownToPDF"; Filename: "{app}\MarkdownToPDF.exe"
Name: "{group}\Uninstall MarkdownToPDF"; Filename: "{uninstallexe}"
Name: "{commondesktop}\MarkdownToPDF"; Filename: "{app}\MarkdownToPDF.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[CustomMessages]
english.CreateDesktopIcon=Create a &desktop icon
english.AdditionalIcons=Additional icons:
russian.CreateDesktopIcon=Создать &ярлык на Рабочем столе
russian.AdditionalIcons=Дополнительные значки:

[Run]
Filename: "{app}\MarkdownToPDF.exe"; Description: "{cm:LaunchProgram,Markdown to PDF Converter Pro}"; Flags: nowait postinstall skipifsilent
