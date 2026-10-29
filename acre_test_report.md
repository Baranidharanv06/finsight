# VaultSight RAG - ACRE Validation Report

## Test Parameters
- **Backend Server:** `http://52.90.103.190:8000`
- **Test Query:** `"any pending litigation or regulatory issues?"` (Ticker: `AAPL`)

## Results Summary
1. **Executive Role (`EXECUTIVE`)**
   - **Decision:** `FULL`
   - **Behavior:** Retrieved unredacted text chunks and returned full legal details.
2. **Employee Role (`EMPLOYEE`)**
   - **Decision:** `SUMMARY`
   - **Behavior:** Masked sensitive details, showing clearance warnings and safe refusal.
3. **Guest Role (`GUEST`)**
   - **Decision:** `REDACTED` / `SUMMARY`
   - **Behavior:** Fully restricted and blocked unauthorized chunks.
