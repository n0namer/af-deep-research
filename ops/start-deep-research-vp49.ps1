$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Rafik\Documents\afdr-vp49-mvp-20261022'
$python = Join-Path $env:USERPROFILE 'Documents\DEV\universal-solver-site\.venvs\af-deep-research\Scripts\python.exe'
$envFile = Join-Path $root '.env'
if (-not (Test-Path -LiteralPath $root) -or -not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $envFile)) { throw 'AFDR runtime root, Python, or env missing' }
foreach ($line in [System.IO.File]::ReadAllLines($envFile)) {
    if ($line -match '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        $key = $Matches[1]; $value = $Matches[2].Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) { $value = $value.Substring(1, $value.Length - 2) }
        [Environment]::SetEnvironmentVariable($key, $value, 'Process')
    }
}
$env:AGENTFIELD_SERVER = 'http://127.0.0.1:18080'
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
$env:no_proxy = $env:NO_PROXY
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PORT = '8005'
$env:DR_LLM_TRANSPORT = 'opencodex'
$env:DR_OPENCODEX_BASE_URL = 'http://127.0.0.1:10100/v1'
$env:DEFAULT_MODEL = 'gpt-6-luna'
$env:SEARCH_MODE = 'federated'
$env:SEARCH_PROVIDERS = 'brave,perplexity,tavily,firecrawl'
$env:SEARCH_FEDERATED_MAX_PROVIDERS = '4'
$env:OPENAI_API_KEY = 'local-proxy'
Set-Location -LiteralPath $root
& $python main.py *>> (Join-Path $env:USERPROFILE '.agentfield\ops\logs\deep-research.log')
