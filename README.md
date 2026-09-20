# TraceLink — Automated VASP Attribution Engine
### Dedicated Forensic Workstation for Cyber Crime & Law Enforcement Units

TraceLink is an institutional, hardened blockchain forensic intelligence and wallet-to-VASP attribution workstation engineered for **State Cyber Police Cells, Central Law Enforcement Agencies (LEAs), and Cyber Security Investigators**.

---

## Key Capabilities

1. **Global Multi-Entity Transaction Ledger**: Aggregated cross-case transaction monitoring across all suspects with instant one-click **"Trace Back in Graph"** pivot.
2. **Deterministic & ML Attribution Engine**: BFS, DFS, Dijkstra confidence routing, Union-Find address clustering, Isolation Forest smurfing detection, and calibrated XGBoost attribution scoring (0–100).
3. **Statutory Lawful Notice Generator**: Section 94 BNSS (2023) and Section 79(3)(b) IT Act (2000) lawful request drafting with Section 105 BNSS digital asset seizure memos.
4. **Tamper-Evident SHA-256 Audit Trail**: Append-only cryptographic hash chaining for all investigative actions and officer sign-offs.
5. **Dual-Mode Operation**: Fully functional offline air-gapped lab mode with bundled offline fixtures, VASP directory, and daily INR price tables; plus online Covalent/Chainalysis live mode.
6. **Institutional Police UI**: Clean, light-theme forensic terminal (`#FFFFFF`, `#0F2C59`, `#166534`, `#991B1B`) with full-screen kiosk support and officer clearance controls.

---

## Quickstart (Local Forensic Workstation)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Default Officer Credentials (Local Dev / Offline Lab)
- **Service/Badge Number**: `IND-CYBER-8841`
- **Password**: `Police@Secure2026`
- **Clearance**: `L3_ADMIN_DIRECTOR`
- **Station**: `Special Cyber Operations, State Crime Branch`
"# TraceLink-Automated-VASP-Attribution-Engine" 
