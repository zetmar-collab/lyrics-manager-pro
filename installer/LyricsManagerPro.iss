; Instalator Lyrics Manager Pro (Inno Setup 6)
;
; Kompilacja:  powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
; Wynik:       dist\LyricsManagerPro-Setup-<wersja>.exe
;
; Instalacja jest per uzytkownik - nie wymaga praw administratora. Uzytkownik
; moze podniesc uprawnienia i zainstalowac dla wszystkich (PrivilegesRequiredOverridesAllowed).

#define AppName        "Lyrics Manager Pro"
#define AppVersion     "1.0.0"
#define AppPublisher   "Marek Zettel"
#define AppURL         "https://github.com/zetmar-collab/lyrics-manager-pro"
#define AppExeName     "LyricsManagerPro.exe"
#define SourceDir      ".."

[Setup]
; Identyfikator musi zostac staly miedzy wersjami - po nim Windows rozpoznaje
; aktualizacje zamiast instalowac program drugi raz.
AppId={{8F3A6C21-5D74-4E0B-9A2F-1C7B4E9D6A38}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} - warsztat autora tekstow piosenek

DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

OutputDir={#SourceDir}\dist
OutputBaseFilename=LyricsManagerPro-Setup-{#AppVersion}
SetupIconFile={#SourceDir}\assets\app.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=yes
LicenseFile={#SourceDir}\LICENSE
InfoBeforeFile={#SourceDir}\installer\info_before.txt

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
Name: "polski";  MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
polski.CreateDesktopIcon=Utworz skrot na pulpicie
english.CreateDesktopIcon=Create a desktop shortcut
polski.AssociateFiles=Otwieraj pliki .lyr tym programem
english.AssociateFiles=Open .lyr files with this program
polski.LaunchApp=Uruchom {#AppName}
english.LaunchApp=Launch {#AppName}
polski.ViewReadme=Pokaz plik README
english.ViewReadme=Show the README file
polski.DictNote=Slowniki pisowni pobierzesz w programie: panel Pisownia, przycisk Slowniki.
english.DictNote=Download spelling dictionaries in the app: Spelling panel, Dictionaries button.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "associate";   Description: "{cm:AssociateFiles}";    GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#SourceDir}\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\README.md";          DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "{#SourceDir}\LICENSE";            DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\assets\app.ico";     DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";                  Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";            Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; Skojarzenie plikow .lyr. HKA kieruje do HKCU przy instalacji per uzytkownik
; i do HKLM przy instalacji dla wszystkich - bez tego skojarzenie wymagaloby admina.
Root: HKA; Subkey: "Software\Classes\.lyr"; ValueType: string; ValueName: ""; \
    ValueData: "LyricsManagerPro.Song"; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\LyricsManagerPro.Song"; ValueType: string; ValueName: ""; \
    ValueData: "Lyrics Manager Pro - tekst piosenki"; Flags: uninsdeletekey; Tasks: associate
Root: HKA; Subkey: "Software\Classes\LyricsManagerPro.Song\DefaultIcon"; ValueType: string; ValueName: ""; \
    ValueData: "{app}\{#AppExeName},0"; Tasks: associate
Root: HKA; Subkey: "Software\Classes\LyricsManagerPro.Song\shell\open\command"; ValueType: string; ValueName: ""; \
    ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExeName}\SupportedTypes"; \
    ValueType: string; ValueName: ".lyr"; ValueData: ""; Flags: uninsdeletekey

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchApp}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Katalog aplikacji po deinstalacji ma zniknac takze wtedy, gdy zostaly w nim
; pliki utworzone po instalacji.
Type: dirifempty; Name: "{app}"

[Code]
{ Dane uzytkownika (ustawienia, historia, slowniki, wlasny slownik) leza poza
  katalogiem programu. Przy deinstalacji pytamy, czy je usunac - domyslnie nie,
  zeby aktualizacja albo ponowna instalacja nie kasowala dorobku autora. }

function DataDir(): String;
begin
  Result := ExpandConstant('{userappdata}\LyricsManagerPro');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Question: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if DirExists(DataDir()) then
    begin
      if ActiveLanguage() = 'polski' then
        Question := 'Usunac takze Twoje dane: ustawienia, historie zmian, slowniki'
                  + ' i wlasny slownik pisowni?' + #13#10#13#10
                  + DataDir() + #13#10#13#10
                  + 'Wybierz Nie, jesli planujesz zainstalowac program ponownie.'
      else
        Question := 'Also remove your data: settings, change history, dictionaries'
                  + ' and your personal spelling dictionary?' + #13#10#13#10
                  + DataDir() + #13#10#13#10
                  + 'Choose No if you plan to install the program again.';

      { SuppressibleMsgBox, a nie MsgBox: przy deinstalacji z /SILENT lub
        /VERYSILENT zwykly MsgBox i tak wyswietla okno i blokuje proces
        w nieskonczonosc. Ostatni argument to odpowiedz przyjmowana w trybie
        cichym - IDNO, czyli dane uzytkownika zostaja. }
      if SuppressibleMsgBox(Question, mbConfirmation,
                            MB_YESNO or MB_DEFBUTTON2, IDNO) = IDYES then
        DelTree(DataDir(), True, True, True);
    end;
  end;
end;
