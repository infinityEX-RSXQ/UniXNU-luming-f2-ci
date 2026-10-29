# f2-luming format-2 CI wiring (route ① — sheng/dada shape)
#
# Prepares and dispatches the adapted macOS workflow for the format-2 luming port.
#
# Audit summary (full report: ../REPORT-F2-LUMING-CI.md):
#   * official format-2 device repos (UniXNU-sheng, UniXNU-dada) contain no macOS build
#     workflow; they only run the reusable "Device documentation" porting-record workflow.
#   * the authoritative format-2 macOS build workflow is UniXNU/UniXNU:.github/workflows/macos.yml,
#     which is dispatched on the UniXNU core repository and checks out a device repo.
#   * unlike sheng/dada, the luming skeleton has its own self-contained device-repo workflow
#     (.github/workflows/macos.yml): it checks out a pinned UniXNU format-2 core (unixnu_repository/
#     unixnu_ref) as a sibling checkout and runs `./unixnu … -D ../device`. That keeps the device
#     repository publishable/dispatchable on its own (picasso-yincql pattern) while still using the
#     official format-2 CLI.
#   * therefore this script installs the **device repository** (whole agents/f2-luming tree,
#     including .github/workflows/macos.yml and scripts/ci/f2-luming-ci.sh) into a GitHub fork and
#     dispatches that workflow. No fork of the UniXNU core is required for a build (the workflow
#     checks out UniXNU/UniXNU at the pinned format-2 commit).
#
# Credentials (from the previous kernel-CI runs; never printed):
#   %LOCALAPPDATA%\unixnu-luming\github-token.xml  (DPAPI-protected, created by
#   agents/ufs-ci/ci_run.ps1 / github-upload/auto-sync-and-run.ps1), or $env:GITHUB_TOKEN.
#   Required scopes: repo + workflow (classic PAT) or Contents+Workflows (fine-grained).
# Repository secrets to configure in the device repository
# (Settings -> Secrets and variables -> Actions):
#   UNIXNU_UNIQUE_CHIP_ID  platform seed required by the payload step (never committed)
#   UNIXNU_IPSW            optional pinned IPSW URL/path, alternative to the kernelcache inputs
#   UNIXNU_DEVICE_TOKEN    only if the UEFI/device repositories are private (checkout token)
# Proprietary URLs (kernelcache/IPSW/trust-cache/Data seed/FD/DTB) are workflow-dispatch
# inputs, masked by the workflow and deleted at the end.
#
# Examples (nothing is changed unless -Prepare/-Dispatch/-Wait is passed):
#   pwsh -File agents/f2-luming/ci/ci-wiring.ps1 -DryRun
#   pwsh -File agents/f2-luming/ci/ci-wiring.ps1 -Prepare -Dispatch -Wait
#   pwsh -File agents/f2-luming/ci/ci-wiring.ps1 -Dispatch -NoWait -DryRunWorkflow
param(
    [switch]$Prepare,
    [switch]$Dispatch,
    [switch]$Wait,
    [switch]$NoWait,
    [switch]$DryRun,
    [switch]$DryRunWorkflow,
    [string]$DeviceRepo = 'infinityEX-RSXQ/UniXNU-luming-f2',
    [string]$UpstreamDeviceRepo = '',                       # empty: create a new private repository
    [string]$DeviceBranch = 'f2-luming-ci',
    [string]$Workflow = 'macos.yml',
    [string]$UnixnuRepository = 'UniXNU/UniXNU',
    [string]$UnixnuRef = '33da81310819b86d3ea62cb704f156c56407764a',
    [string]$Defconfig = 'luming_defconfig',
    [string]$Steps = 'kernel package firmware payload bootimg',
    [string]$UefiRepo = 'infinityEX-RSXQ/uefi-luming',
    [string]$UefiRef = 'main',
    [string]$UefiArchiveReleaseTag = '',
    [string]$UefiArchiveSha256 = '',
    [string]$KernelcacheUrl = '',
    [string]$KernelcacheSha256 = '',
    [string]$KernelcacheReleaseTag = '',
    [string]$IpswUrl = '',
    [string]$TrustCacheUrl = '',
    [string]$DataSeedUrl = '',
    [string]$Xcode = '16.4',
    [string]$OutDir = 'runs',
    [int]$MaxWaitMinutes = 6 * 60
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$here = $PSScriptRoot
$deviceRoot = (Resolve-Path (Join-Path $here '..')).Path          # agents/f2-luming

function Get-Token {
    if ($env:GITHUB_TOKEN) { return $env:GITHUB_TOKEN }
    $tokenFile = Join-Path (Join-Path $env:LOCALAPPDATA 'unixnu-luming') 'github-token.xml'
    if (-not (Test-Path -LiteralPath $tokenFile)) {
        throw "missing GitHub token: set GITHUB_TOKEN or create $tokenFile with the previous kernel-CI token"
    }
    $encrypted = (Get-Content -LiteralPath $tokenFile -Raw).Trim()
    $secure = ConvertTo-SecureString $encrypted
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

$script:token = $null
try { $script:token = Get-Token } catch {
    if (-not $DryRun) { throw }
    Write-Host 'warning: no GitHub token available; -DryRun will only show the local plan'
}
$script:headers = @{
    Authorization          = "Bearer $($script:token)"
    Accept                 = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
    'User-Agent'           = 'luming-f2-ci-task328'
}

function Invoke-Api {
    param([string]$Method, [string]$Uri, $Body, [string]$OutFile, [int[]]$ExpectStatus = @(200, 201, 204))
    $params = @{ Method = $Method; Uri = $Uri; Headers = $script:headers; ErrorAction = 'Stop' }
    if ($null -ne $Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10); $params.ContentType = 'application/json' }
    if ($OutFile) { $params.OutFile = $OutFile }
    try { return Invoke-RestMethod @params }
    catch {
        $status = $null
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        if ($status -and $ExpectStatus -contains $status) { return $null }
        throw
    }
}

function Get-Repo($Repo) { return Invoke-Api -Method GET -Uri "https://api.github.com/repos/$Repo" -ExpectStatus @(200, 404) }

function Ensure-DeviceRepo {
    $repo = Get-Repo $DeviceRepo
    if ($repo) { Write-Host "device repo exists: $DeviceRepo (default branch $($repo.default_branch))"; return $repo }
    if ($UpstreamDeviceRepo) {
        Write-Host "creating fork $DeviceRepo from $UpstreamDeviceRepo"
        Invoke-Api -Method POST -Uri "https://api.github.com/repos/$UpstreamDeviceRepo/forks" -Body @{ default_branch_only = $false } | Out-Null
    } else {
        $name = $DeviceRepo.Split('/')[1]
        Write-Host "creating private device repository $DeviceRepo"
        Invoke-Api -Method POST -Uri 'https://api.github.com/user/repos' -Body @{
            name = $name; private = $true; auto_init = $true; default_branch = 'main'
            description = 'UniXNU format-2 luming device repository (Xiaomi Civi 5 Pro, SM8735)'
        } | Out-Null
    }
    $deadline = (Get-Date).AddMinutes(3)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5
        $repo = Get-Repo $DeviceRepo
        if ($repo) { Start-Sleep -Seconds 2; return (Get-Repo $DeviceRepo) }
    }
    throw "device repo $DeviceRepo was not ready within 3 minutes"
}

function Ensure-Branch([string]$Repo, [string]$Name, [string]$From) {
    $base = Invoke-Api -Method GET -Uri "https://api.github.com/repos/$Repo/git/ref/heads/$From"
    $sha = $base.object.sha
    $existing = Invoke-Api -Method GET -Uri "https://api.github.com/repos/$Repo/git/ref/heads/$Name" -ExpectStatus @(200, 404)
    if ($existing) {
        if ($existing.object.sha -ne $sha) {
            Invoke-Api -Method PATCH -Uri "https://api.github.com/repos/$Repo/git/refs/heads/$Name" -Body @{ sha = $sha; force = $true } | Out-Null
            Write-Host "branch $Repo@$Name force-moved to $($sha.Substring(0,10))"
        } else { Write-Host "branch $Repo@$Name already at $($sha.Substring(0,10))" }
        return
    }
    Invoke-Api -Method POST -Uri "https://api.github.com/repos/$Repo/git/refs" -Body @{ ref = "refs/heads/$Name"; sha = $sha } | Out-Null
    Write-Host "branch $Repo@$Name created at $($sha.Substring(0,10))"
}

function Put-RepoFile([string]$Repo, [string]$RepoPath, [string]$LocalPath, [string]$BranchName, [string]$Message) {
    if (-not (Test-Path -LiteralPath $LocalPath)) { throw "missing local file $LocalPath" }
    $bytes = [IO.File]::ReadAllBytes($LocalPath)
    $content = [Convert]::ToBase64String($bytes)
    $sha = (Get-FileHash -LiteralPath $LocalPath -Algorithm SHA256).Hash.ToLower()
    $uri = "https://api.github.com/repos/$Repo/contents/$RepoPath"
    $body = @{ message = $Message; content = $content; branch = $BranchName }
    $existing = Invoke-Api -Method GET -Uri "$uri`?ref=$BranchName" -ExpectStatus @(200, 404)
    if ($existing) { $body.sha = $existing.sha; $verb = 'updated' } else { $verb = 'created' }
    Invoke-Api -Method PUT -Uri $uri -Body $body | Out-Null
    Write-Host ("{0,-7} {1} ({2} B, sha256 {3})" -f $verb, $RepoPath, $bytes.Length, $sha.Substring(0,16))
}

function Put-DeviceTree([string]$Repo, [string]$BranchName) {
    $root = $deviceRoot
    $files = Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object {
        $rel = $_.FullName.Substring($root.Length + 1).Replace('\', '/')
        # Never upload local UEFI/EDK2 checkouts or build outputs (~1.1 GiB / 31k files);
        # firmware/README.md, firmware/ci and firmware/patches are skeleton files and stay.
        if ($rel -match '^(firmware/(build-tree|uefi|out)/|out/|ci-artifacts/|node_modules/|\.cache/|\.git/|\.check/|deep-graft/)') { return $false }
        if ($_.Name -eq '.DS_Store' -or $_.Name -like '_dryrun_test*' -or $_.Name -like '_final_*' -or $_.Name -like '_exec_*') { return $false }
        return $true
    }
    Write-Host "uploading $($files.Count) skeleton files to $Repo@$BranchName"
    foreach ($file in $files) {
        $rel = $file.FullName.Substring($root.Length + 1).Replace('\', '/')
        Put-RepoFile -Repo $Repo -RepoPath $rel -LocalPath $file.FullName -BranchName $BranchName -Message "f2-luming CI: $rel"
    }
}

function Dispatch-Workflow {
    $deadline = (Get-Date).AddSeconds(180)
    $match = $null
    while ((Get-Date) -lt $deadline) {
        $workflows = Invoke-Api -Method GET -Uri "https://api.github.com/repos/$DeviceRepo/actions/workflows?per_page=100"
        $match = $workflows.workflows | Where-Object { $_.path -eq ".github/workflows/$Workflow" } | Select-Object -First 1
        if ($match) { break }
        Write-Host 'workflow not registered yet (GitHub registration delay); retrying in 5s...'
        Start-Sleep -Seconds 5
    }
    if (-not $match) { throw "workflow .github/workflows/$Workflow is not registered on $DeviceRepo after 180s; check that it exists on the default branch" }
    $script:workflowId = $match.id
    $body = @{
        ref = $DeviceBranch
        inputs = @{
            unixnu_repository = $UnixnuRepository
            unixnu_ref        = $UnixnuRef
            device_ref        = $DeviceBranch
            defconfig         = $Defconfig
            steps             = $Steps
            dry_run           = $(if ($DryRunWorkflow) { 'true' } else { 'false' })
            uefi_repository   = $UefiRepo
            uefi_ref          = $UefiRef
            uefi_archive_release_tag = $UefiArchiveReleaseTag
            uefi_archive_sha256 = $UefiArchiveSha256
            kernelcache_url   = $KernelcacheUrl
            kernelcache_sha256 = $KernelcacheSha256
            kernelcache_release_tag = $KernelcacheReleaseTag
            ipsw_url          = $IpswUrl
            trust_cache_url   = $TrustCacheUrl
            data_seed_url     = $DataSeedUrl
            xcode             = $Xcode
        }
    }
    $dispatched = $false
    for ($attempt = 1; $attempt -le 6; $attempt++) {
        try {
            Invoke-Api -Method POST -Uri "https://api.github.com/repos/$DeviceRepo/actions/workflows/$($match.id)/dispatches" -Body $body | Out-Null
            $dispatched = $true
            break
        } catch {
            $status = $null
            if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
            if ($status -eq 422 -and $attempt -lt 6) {
                Write-Host "dispatch returned 422 (workflow registration/index delay); retry $attempt/5"
                Start-Sleep -Seconds 10
                continue
            }
            throw
        }
    }
    if (-not $dispatched) { throw "could not dispatch $Workflow after retries" }
    Write-Host "dispatched $Workflow on $DeviceRepo@$DeviceBranch (dry_run=$DryRunWorkflow)"
}

function Wait-Run($Run) {
    $deadline = (Get-Date).AddMinutes($MaxWaitMinutes)
    $last = ''
    while ((Get-Date) -lt $deadline) {
        $current = Invoke-Api -Method GET -Uri "https://api.github.com/repos/$DeviceRepo/actions/runs/$($Run.id)"
        $line = "$(Get-Date -Format HH:mm:ss) $($current.status) $($current.conclusion)"
        if ($line -ne $last) { Write-Host $line; $last = $line }
        if ($current.status -eq 'completed') { return $current }
        Start-Sleep -Seconds 15
    }
    throw "run $($Run.id) did not complete within $MaxWaitMinutes minutes"
}

function Save-Run($Run) {
    $dir = Join-Path (Join-Path $here $OutDir) ("f2-" + $Run.id)
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $record = [ordered]@{
        workflow = $Workflow; device_repository = $DeviceRepo; device_branch = $DeviceBranch
        unixnu_repository = $UnixnuRepository; unixnu_ref = $UnixnuRef
        run_id = $Run.id; run_number = $Run.run_number; run_url = $Run.html_url
        status = $Run.status; conclusion = $Run.conclusion
        created_at = $Run.created_at; updated_at = $Run.updated_at; artifacts = @()
    }
    $artifacts = Invoke-Api -Method GET -Uri "https://api.github.com/repos/$DeviceRepo/actions/runs/$($Run.id)/artifacts"
    foreach ($artifact in $artifacts.artifacts) {
        $zip = Join-Path $dir ($artifact.name + '.zip')
        Invoke-Api -Method GET -Uri $artifact.archive_download_url -OutFile $zip
        $extract = Join-Path $dir ('extracted\' + $artifact.name)
        if (Test-Path -LiteralPath $extract) { Remove-Item -Recurse -Force $extract }
        Expand-Archive -LiteralPath $zip -DestinationPath $extract -Force
        $record.artifacts += [ordered]@{
            name = $artifact.name; bytes = (Get-Item $zip).Length
            sha256 = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLower(); extracted = $extract
        }
        Write-Host "artifact $($artifact.name) -> $zip"
    }
    try {
        $logsZip = Join-Path $dir 'logs.zip'
        Invoke-Api -Method GET -Uri "https://api.github.com/repos/$DeviceRepo/actions/runs/$($Run.id)/logs" -OutFile $logsZip
        $logsExtract = Join-Path $dir 'logs'
        if (Test-Path -LiteralPath $logsExtract) { Remove-Item -Recurse -Force $logsExtract }
        Expand-Archive -LiteralPath $logsZip -DestinationPath $logsExtract -Force
        $record.artifacts += [ordered]@{ name = 'logs'; bytes = (Get-Item $logsZip).Length
            sha256 = (Get-FileHash -LiteralPath $logsZip -Algorithm SHA256).Hash.ToLower(); extracted = $logsExtract }
    } catch { Write-Host "logs download failed: $($_.Exception.Message)" }
    $json = Join-Path $dir 'run-summary.json'
    [pscustomobject]$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $json -Encoding UTF8
    Write-Host "run summary: $json"
    return $record
}

if ($DryRun) {
    Write-Host 'f2-luming format-2 CI wiring plan (no changes made)'
    Write-Host "  device repo       : $DeviceRepo, branch $DeviceBranch"
    Write-Host "  workflow          : .github/workflows/$Workflow (device repo; self-contained: checks out UniXNU core)"
    Write-Host "  unixnu core       : $UnixnuRepository @ $UnixnuRef (format-2 pinned snapshot)"
    Write-Host "  UEFI repo         : $UefiRepo @ $UefiRef (firmware/bootimg; may be empty for kernel-only)"
    Write-Host "  local tree        : $deviceRoot"
    Write-Host "  token             : DPAPI file %LOCALAPPDATA%\unixnu-luming\github-token.xml (or GITHUB_TOKEN)"
    if ($script:token) {
        try {
            $repo = Get-Repo $DeviceRepo
            Write-Host ("  repo {0,-42} {1}" -f $DeviceRepo, $(if ($repo) { 'exists (default ' + $repo.default_branch + ')' } else { 'MISSING (would be created/forked)' }))
        } catch {
            Write-Host "  repo state: API unreachable from this host ($($_.Exception.Message)); planned repo is shown above"
        }
    } else {
        Write-Host '  repo state: not queried (no token); planned repo is shown above'
    }
    Write-Host '  secrets: UNIXNU_UNIQUE_CHIP_ID, optional UNIXNU_IPSW / UNIXNU_DEVICE_TOKEN'
    Write-Host '  dry-run dispatch input: dry_run=true (builds nothing, uploads preflight checklist)'
    Write-Host '  next: -Prepare then -Dispatch -Wait (or GitHub UI Actions -> macOS build (format-2 luming))'
    return
}

if ($Prepare) {
    $repo = Ensure-DeviceRepo
    $default = if ($repo.default_branch) { $repo.default_branch } else { 'main' }
    Ensure-Branch -Repo $DeviceRepo -Name $DeviceBranch -From $default
    Put-DeviceTree -Repo $DeviceRepo -BranchName $DeviceBranch
    # Ensure workflow + device helper exist on the default branch too so workflow_dispatch can see it.
    Put-RepoFile -Repo $DeviceRepo -RepoPath ".github/workflows/$Workflow" `
        -LocalPath (Join-Path $deviceRoot ".github\workflows\$Workflow") -BranchName $default -Message "f2-luming CI: workflow on $default"
    Put-RepoFile -Repo $DeviceRepo -RepoPath 'scripts/ci/f2-luming-ci.sh' `
        -LocalPath (Join-Path $deviceRoot 'scripts\ci\f2-luming-ci.sh') -BranchName $default -Message 'f2-luming CI: device helper on default branch'
    Write-Host 'prepare: done'
}

if ($Dispatch) {
    Dispatch-Workflow
    if ($NoWait) { Write-Host 'dispatched (not waiting)'; return }
    $started = (Get-Date).ToUniversalTime()
    $deadline = (Get-Date).AddMinutes(5)
    $run = $null
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5
        $runs = Invoke-Api -Method GET -Uri "https://api.github.com/repos/$DeviceRepo/actions/workflows/$($script:workflowId)/runs?event=workflow_dispatch&branch=$DeviceBranch&per_page=10"
        $run = $runs.workflow_runs | Where-Object { $_.created_at -and ([DateTime]$_.created_at) -ge $started.AddMinutes(-2) } |
            Sort-Object { [DateTime]$_.created_at } -Descending | Select-Object -First 1
        if ($run) { break }
    }
    if (-not $run) { throw 'dispatched run did not appear within 5 minutes' }
    Write-Host "run #$($run.run_number) id $($run.id): $($run.html_url)"
    if ($Wait) {
        $final = Wait-Run $run
        $summary = Save-Run $final
        Write-Host "conclusion: $($summary.conclusion)"
        if ($summary.conclusion -ne 'success') { exit 2 }
    }
}
