###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################

param(
    [Parameter(Mandatory)]
    [String]$Target,
    [String]$Arguments,
    [String]$Name,
    [String]$Description,
    [String]$Icon,
    [String]$WorkingDirectory,
    [String]$Extension = ".lnk",
    [Boolean]$Desktop = $True,
    [Boolean]$StartMenu = $True
)

echo $Extension

$WshShell = New-Object -comObject WScript.Shell

Function CreateShortcut($Path) {
    $Shortcut = $WshShell.CreateShortcut($Path)
    $Shortcut.TargetPath = $Target

    if ($Arguments)        { $Shortcut.Arguments = $Arguments }
    if ($Description)      { $Shortcut.Description = $Description }
    if ($Icon)             { $Shortcut.IconLocation = $Icon }
    if ($WorkingDirectory) { $Shortcut.Arguments = $WorkingDirectory }

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
