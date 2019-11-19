; Helper defines. Update PRODUCT_VERSION as needed for release.
!define PRODUCT_NAME "SPMT"
!define PRODUCT_VERSION "0.5.0a"
!define PRODUCT_PUBLISHER "PIVX"
!define PRODUCT_WEB_SITE "https://github.com/PIVX-Project/PIVX-SPMT"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\SecurePivxMasternodeTool.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor /SOLID lzma

; MUI 1.67 compatible ------
!include "MUI.nsh"
!include "x64.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "img\spmt.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\app\SecurePivxMasternodeTool.exe"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; Reserve files
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS

; MUI end ------

Name "${PRODUCT_NAME}"
OutFile "SPMT-v${PRODUCT_VERSION}-Win64-Setup.exe"
InstallDir "$PROGRAMFILES64\SPMT"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  ; Convert the markdown file to plain text as windows doesn't understand markdown files natively.
  ; TODO: Make this more pretty
  File /oname=README.txt "SPMT-v${PRODUCT_VERSION}-Win64\README.md"
  SetOutPath "$INSTDIR\app"
  File /r "SPMT-v${PRODUCT_VERSION}-Win64\app\*.*"
  SetOutPath "$INSTDIR\docs"
  File /r "SPMT-v${PRODUCT_VERSION}-Win64\docs\*.*"

  CreateDirectory "$SMPROGRAMS\SPMT"
  CreateShortCut "$SMPROGRAMS\SPMT\SPMT.lnk" "$INSTDIR\app\SecurePivxMasternodeTool.exe"
  CreateShortCut "$DESKTOP\SPMT.lnk" "$INSTDIR\app\SecurePivxMasternodeTool.exe"
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\SPMT\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\SPMT\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\app\SecurePivxMasternodeTool.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\app\SecurePivxMasternodeTool.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd


Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\README.txt"
  RMDir /r "$INSTDIR\docs"
  RMDir /r "$INSTDIR\app"

  Delete "$SMPROGRAMS\SPMT\Uninstall.lnk"
  Delete "$SMPROGRAMS\SPMT\Website.lnk"
  Delete "$DESKTOP\SPMT.lnk"
  Delete "$SMPROGRAMS\SPMT\SPMT.lnk"

  RMDir "$SMPROGRAMS\SPMT"
  RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd

# Installer functions
Function .onInit
    InitPluginsDir
    ${If} ${RunningX64}
      ; disable registry redirection (enable access to 64-bit portion of registry)
      SetRegView 64
    ${Else}
      MessageBox MB_OK|MB_ICONSTOP "Cannot install SPMT on a 32-bit system."
      Abort
    ${EndIf}
FunctionEnd