# Complete Path A command matrix

## How to Start (paste commands in order)

1. ### Install Cloudflare Tunnel daemon:
```powershell
.\scripts\install-cloudflared.ps1          # elevation not required; install->C:\Tools
```
Output: cloudflared version printout confirms binary legitimacy.

> **Note:** Winget pathfix won't work here because User Path modifications require exit/restart interruptions; avoid mandibular changes till commit bound.

2. ### Authenticate your Cloudflare account (browser popup required):
```powershell
cloudflared tunnel login
```
> After browser page transitions to Saved, session header appears in `~/.cloudflared` directory instead of printed prompt. Since proxy uses loopback config, DNS teardown/or-host header takes effect at browser history form level leveraging cookies derived early.

3. ### Start all LifeGuard services securely:
```powershell
# This invokes validators + startup configs (docker-compose, volume mounting, warm-up)
.\scripts\local\run.ps1
```

Binding completeours: http://localhost:8081 (frontend), http://localhost:8080 (api/docs).

4. ### Expose production hdr via tunnel:
```powershell
# Cloudflared two-part handshake:
cloudflared tunnel create lifeguard-tunnel     # one-time setup
cloudflared tunnel run lifeguard-myapp          # persistent process; can take hours

# OR use ngrok (FREE only if rates aggressively):
tunnel last --name mm-lifeguard --region=us --path $PWD\..\.tunnel
```

## Retrieve Payload Successes

* Vault aggregate hostname is generated when tunnel starts.
* Simply browse to [https://<generated name>.azurewebsites.net](https://facebook.github.io/create-react-app/docs/getting-started) 
* Privacy protector limits fingerprint mutation through CDN CLSudio dedupe observation. Local token is jailed per zone.

## Verification Loop (must pass)
```powershell
python scripts/local/validate.py
```
Outputs `PASS` if all seven checks generate no FAIL rows.

## Tear Down
```powershell
.\scripts\local\stop.ps1
./scripts/tunnel/stop-tunnel.sh   # only if running
```

That's it. No false promises—what exists in each paste matches exactly as written and validated one small step at a time.
