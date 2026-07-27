#Requires -Version 5.1
<#
.SYNOPSIS
    Create a new GitHub repository from a local folder and push it, in one shot.
.DESCRIPTION
    Locates gh (even when it is not on PATH), verifies authentication, initializes
    a local git repo if needed, makes an initial commit, then creates the GitHub
    repo and pushes. Idempotent-ish: safe to re-run if a step already happened.
.PARAMETER Path
    Folder to publish. Defaults to the current directory.
.PARAMETER Name
    Repository name on GitHub. Defaults to the folder's name.
.PARAMETER Visibility
    'private' (default) or 'public'.
.PARAMETER Message
    Initial commit message. Used only if the repo has no commits yet.
.EXAMPLE
    .\publish.ps1 -Path 'C:\path\to\folder'
.EXAMPLE
    .\publish.ps1 -Path 'C:\path\to\my-app' -Name my-app -Visibility public
#>
[CmdletBinding()]
param(
    [string]$Path = (Get-Location).Path,
    [string]$Name,
    [ValidateSet('private', 'public')]
    [string]$Visibility = 'private',
    [string]$Message
)

# Keep native-command stderr (git/gh write progress there) from being promoted to
# terminating errors. We judge native calls by $LASTEXITCODE and use explicit
# `throw` for real failures; cmdlets that must hard-fail get -ErrorAction Stop.
$ErrorActionPreference = 'Continue'

function Find-Gh {
    $cmd = Get-Command gh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidates = @(
        "$env:ProgramFiles\GitHub CLI\gh.exe",
        "${env:ProgramFiles(x86)}\GitHub CLI\gh.exe",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\gh.exe"
    )
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    $pkg = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter gh.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pkg) { return $pkg.FullName }
    return $null
}

# Resolve and validate the folder.
$Path = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
    throw "Path is not a folder: $Path"
}
if (-not $Name)    { $Name = Split-Path -Leaf $Path }
if (-not $Message) { $Message = "Initial commit" }

Write-Host "Folder     : $Path"
Write-Host "Repo name  : $Name"
Write-Host "Visibility : $Visibility"
Write-Host ""

# 1. Locate gh.
$gh = Find-Gh
if (-not $gh) {
    throw "GitHub CLI (gh) not found. Install with:  winget install --id GitHub.cli"
}
Write-Host "gh         : $gh"

# 2. Confirm authentication. gh writes status to stderr; capture both streams.
$null = & $gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "gh is not authenticated. Run:  & '$gh' auth login   (then re-run this script)."
}

# 3. Initialize git if this folder is not already a repo.
$insideRepo = $false
Push-Location $Path
try {
    & git rev-parse --is-inside-work-tree 2>$null | Out-Null
    $insideRepo = ($LASTEXITCODE -eq 0)

    if (-not $insideRepo) {
        Write-Host "git init   : creating new repo on branch 'main'"
        & git init -b main | Out-Null
    }

    # 4. Stage and commit only if there is nothing committed yet, or there are changes.
    & git rev-parse HEAD 2>$null | Out-Null
    $hasCommit = ($LASTEXITCODE -eq 0)

    & git add -A
    $pending = (& git status --porcelain)
    if (-not $hasCommit -or $pending) {
        Write-Host "commit     : $Message"
        # Disable GPG signing for this commit so it never blocks on a missing key.
        & git -c commit.gpgsign=false commit -m $Message | Out-Null
    } else {
        Write-Host "commit     : nothing to commit (working tree clean)"
    }

    # 5. Create the GitHub repo and push. If 'origin' already exists, just push.
    $hasOrigin = (& git remote) -contains 'origin'
    if ($hasOrigin) {
        Write-Host "remote     : 'origin' already set; pushing existing repo"
        & git push -u origin HEAD 2>&1 | Out-Null
    } else {
        Write-Host "creating   : github.com/<you>/$Name ($Visibility) and pushing..."
        $visFlag = if ($Visibility -eq 'public') { '--public' } else { '--private' }
        # gh prints the new URL to stdout and push progress to stderr (not an error).
        & $gh repo create $Name $visFlag --source $Path --remote origin --push 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "gh repo create failed (exit $LASTEXITCODE)." }
    }

    # 6. Report the canonical URL.
    $url = (& $gh repo view --json url -q .url 2>$null)
    Write-Host ""
    if ($url) {
        Write-Host "Done -> $url"
    } else {
        Write-Host "Done. Repository created and pushed."
    }
}
finally {
    Pop-Location
}
