param(
  [string]$Distro = "Ubuntu",
  [switch]$SmokeTest
)

$scriptPath = "/mnt/tagmdl_repo/HomesPlatformRepos/concierge/scripts/session-bootstrap.sh"
$smokeValue = if ($SmokeTest) { "1" } else { "0" }

$bashCommand = @"
set -e
export SMOKE_TEST=$smokeValue
if [ ! -f '$scriptPath' ]; then
  echo "[bootstrap] Script not found at $scriptPath"
  echo "[bootstrap] Attempting initial mount"
  sudo mkdir -p /mnt/tagmdl_repo
  sudo mount -t drvfs '\\10.1.1.11\TAGMDL-Repo' /mnt/tagmdl_repo
fi
source '$scriptPath'
exec bash -i
"@

wsl.exe -d $Distro -- bash -ic $bashCommand
