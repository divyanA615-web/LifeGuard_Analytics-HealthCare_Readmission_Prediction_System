# Build configuration for Vercel (frontend)
# Only added if user decides to re-engage Vercel later
vercel:
  version: 2
  name: lifeguard-readmission-frontend
  regions:
    - bom1
  # Rewrites map frontend proxy calls to external backend URL at runtime
  rewrites:
    - source: "/v1/(.*)"
      destination: "https://lifeguard-backend.onrender.com/v1/$1"
    - source: "/(.*)"
      destination: "/index.html"
  # Health endpoint checking post-deploy hook (external)
  github:
    enabled: true
    silent: false
    gitMatcher: "^(main|master)$"
