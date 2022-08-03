###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################

param(
    [Parameter(Mandatory)]
    [String]$Target,
    [Parameter(Mandatory)]
    [String]$Name,
    [String]$Arguments,
    [String]$Description,
    [String]$Icon,
    [String]$WorkingDirectory,
    [String]$Extension = ".lnk",
    [Boolean]$Desktop = $True,
    [Boolean]$StartMenu = $True
)


# Start creating shortcuts.
# If neither Desktop nor StartMenu are enabled, skip functionality.
if ( $Desktop -or $StartMenu) {
    $WshShell = New-Object -comObject WScript.Shell

    Function CreateShortcut($Path) {
        $Shortcut = $WshShell.CreateShortcut($Path)
        $Shortcut.TargetPath = $Target

        Write-Output $Path

        if ( $Arguments )        { $Shortcut.Arguments = $Arguments }
        if ( $Description )      { $Shortcut.Description = $Description }
        if ( $Icon )             { $Shortcut.IconLocation = $Icon }
        if ( $WorkingDirectory ) { $Shortcut.Arguments = $WorkingDirectory }

        $Shortcut.Save()
    }


    if ( $Desktop ) {
        $DesktopPath = [Environment]::GetFolderPath("Desktop")
        CreateShortcut("$DesktopPath\$Name$Extension")
    }

    if ( $StartMenu ) {
        $StartMenuPath = [Environment]::GetFolderPath("StartMenu")
        CreateShortcut("$StartMenuPath\Programs\$Name$Extension")
    }

}
