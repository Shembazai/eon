!define APP_NAME "EON PFA"
!define PRODUCT_VERSION "1.0.0"
!define COMPANY_NAME "EON Labs"
!define OUTPUT_PATH "dist"
!define STAGING_DIR "dist\\windows_installer_src"
!ifndef OUTPUT_EXE
!define OUTPUT_EXE "dist\\eon_pfa_installer_${__TIME__}.exe"
!endif

Name "${APP_NAME}"
OutFile "${OUTPUT_EXE}"
InstallDir "$LOCALAPPDATA\\EON_PFA"
SetCompress auto
SetCompressor /SOLID lzma
RequestExecutionLevel user

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "${STAGING_DIR}\\*"

    CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\Launch ${APP_NAME}.lnk" "$INSTDIR\\.venv\\Scripts\\python.exe" "$INSTDIR\\EON_PFA.py"
    CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\Open Installation Folder.lnk" "$INSTDIR"

    DetailPrint "Installation completed to $INSTDIR"
    DetailPrint "Running post-install configuration..."
    nsExec::ExecToStack 'powershell.exe -ExecutionPolicy Bypass -File "$INSTDIR\\windows_install.ps1"'
    Pop $0
SectionEnd

Section "Uninstall"
    Delete "$SMPROGRAMS\\${APP_NAME}\\Launch ${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\\${APP_NAME}\\Open Installation Folder.lnk"
    RMDir "$SMPROGRAMS\\${APP_NAME}"
    Delete "$INSTDIR\\.venv\\Scripts\\python.exe"
    RMDir /r "$INSTDIR"
SectionEnd
