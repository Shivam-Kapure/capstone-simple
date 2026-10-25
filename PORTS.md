# Port Audit — Capstone-Simple

Checked on 2026-10-25 from Windows PowerShell (`Get-NetTCPConnection -State Listen`, `docker ps -a`, `kubectl get svc -A`). Nothing that was already using a port was stopped or changed.

| Port | Layer | Purpose | Result | Conflict |
|------|-------|---------|--------|----------|
| 38080 | Host → `capstone-frontend` container :80 | Docker Compose dashboard | Free before use. `http://localhost:38080/` returns 200 | None |
| 38081 | Host → `capstone-backend` container :8000 | Docker Compose API (direct) | Free before use. `http://localhost:38081/health` returns 200 | None |
| 8000 | Host | — | **Occupied** (pids 19032 and 17692; `obs-pipeline-app`). That's why the backend is published on 38081 instead | Avoided |
| 8000 | Container / Pod | Backend uvicorn port and `capstone-backend` ClusterIP | Internal only | None |
| 80 | Container / Pod | Frontend nginx | Internal only; host port 80 has no listener | None |
| 30099 | Kubernetes NodePort (`capstone-simple` profile) | `capstone-nodeport` → frontend | Free before the first apply (the cluster only had `kubernetes` and `kube-dns`). Now `80:30099/TCP`. `curl http://192.168.58.2:30099/health` run inside the node returns 200 | None |
| 30099 | Host (Windows) | — | `http://localhost:30099` gives "Unable to connect". The Minikube Docker driver on Windows does not publish NodePorts to the host | None |
| 54772 | Host 127.0.0.1 | Tunnel from `minikube -p capstone-simple service capstone-nodeport --url` | Dashboard, `/health` and `/api/*` all return 200. The port is random per run and exists only while that command keeps running | None |
| 8080 | Host | Existing Jenkins (java.exe). Used, not modified | In use by Jenkins (expected) | Not used by this project |

Notes:
- Other running containers (`obs-*` on 3000/8000/9090/48173, `payment-engine-*` on 28080/28081) do not overlap and were not touched.
- `capstone.env` records `http://localhost:30099`, because `capstone.tf` specifies that value. On this Windows/Docker-driver setup the URL you can reach from the host is the minikube tunnel URL.
