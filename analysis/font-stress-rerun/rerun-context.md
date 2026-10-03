# Full performance rerun

The user requested a full rerun after reporting that Crimson Desert had been
running for the preceding two to three minutes. This repeats the original
confirmation cohort without removing or replacing its observations. Potential
background-load contamination is a reason to repeat; overlap with the original
measurement interval has not been established.

The rerun began on 2026-10-02 at approximately 21:46 UTC. No matching renderer,
Cargo, rustc or Crimson Desert process was reported by the initial process-name
check. This limited check does not establish absence of all background load.

The collector, binaries, source snapshots, fonts, frozen selection and existing
pixel proof are reused unchanged. CPU and GPU run serially, with no concurrent
builds, downloads, statistical analysis or archive compression by this session.
Each backend retains all 12 balanced blocks for master and final, the same three
fonts and DPR 1 and 2. CPU uses five trials per process; GPU uses three. Any failed
attempt remains in its own directory, with no automatic retries or exclusions.

The original primary endpoint remains demo first-paint host CPU draw time at
DPR 2. GPU completion and the warm, zoom, pan and full reported sequences remain
secondary endpoints. All original confirmation data remain archived separately.
