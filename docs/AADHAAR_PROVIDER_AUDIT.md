# Aadhaar & KYC Provider Audit for SAKHI

## 1. Executive Recommendation
For the SAKHI hackathon prototype, we have a strict **₹0 cost** requirement. Based on the current ecosystem of Indian KYC gateways, **Setu's Aadhaar eKYC Sandbox** is the unequivocally recommended path. It provides a free, fully simulated API environment that requires no business KYC to access, offers dummy Aadhaar numbers, and perfectly demonstrates a production-grade architecture to judges. 

If third-party API registration proves too tedious during the hackathon time crunch, building a **Mock Verification Service** directly into our FastAPI backend is the industry-standard backup.

## 2. Provider Comparison Table

| Provider | Legitimate? | Free Sandbox? | Setup Required | Demo Usability | Hackathon Rank |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Setu eKYC** | Yes | Yes (₹0) | Developer Signup | High (Dummy OTPs) | **#1** |
| **Custom Mock API** | Yes (Simulated) | Yes (₹0) | None | High | **#2 (Backup)** |
| **Offline XML e-KYC** | Yes | Yes (₹0) | None | Low (Bad UX) | #3 |
| **Cashfree/Razorpay** | Yes | Yes (₹0) | Full Business KYC | Low | #4 |
| **Direct UIDAI API** | No (Restricted) | N/A | AUA/KUA License | Impossible | #5 |

## 3. Zero-Cost Feasibility
It is **100% feasible** to demonstrate Aadhaar verification at zero cost. We will achieve this by strictly utilizing a sandbox environment that does not touch the live UIDAI production database.

## 4. Exact Current Pricing Evidence
*   **Setu Sandbox:** Access to `dg-sandbox.setu.co` is completely free for developers. Production pricing is a flat ₹5 per successful verification, but we will not enter production.
*   **Direct UIDAI:** Not publicly priced for independent developers; restricted to licensed entities.
*   **Cashfree:** Free sandbox, but requires completing their merchant onboarding process, which mandates PAN and GST details.

## 5. Exact Sandbox Limitations (Setu)
*   You **cannot** use your real Aadhaar number.
*   You must use their provided dummy values (e.g., Aadhaar `999999990019`).
*   OTP is always simulated (e.g., entering `123456` always yields success, `123457` yields failure).
*   No SMS is actually sent to the user's phone.

## 6. UIDAI Official Option (Direct API)
*   **Feasibility:** Impossible for a hackathon.
*   **Reason:** UIDAI strictly restricts API access to authorized Authentication User Agencies (AUAs) and KYC User Agencies (KUAs). Independent developers cannot obtain these credentials without massive regulatory compliance and financial deposits.

## 7. Offline e-KYC Option (XML Upload)
*   **Feasibility:** Possible and free.
*   **Flow:** The user leaves the SAKHI app, visits the UIDAI website, downloads a password-protected XML zip file of their identity, returns to SAKHI, and uploads it.
*   **Verdict:** Rejected. The UX is terrible for a mobile safety app and fails to demonstrate seamless API integration to the judges.

## 8. Recommended Option for SAKHI: Setu Aadhaar Sandbox
**Setu** is the optimal choice. It allows us to build the exact frontend UI and backend architecture of a production app, while safely routing requests to a free sandbox that always responds predictably.

## 9. Backup Option: Mocked FastAPI Service
If registering for Setu fails, we will implement a mock `/api/v1/auth/kyc` endpoint directly in our FastAPI backend. It will artificially wait 2 seconds, accept any 12-digit number, accept `123456` as the OTP, and return a success payload. This is a highly respected approach in hackathons when dealing with restricted government APIs.

## 10. Required Account / Setup Steps (For Setu)
1. Go to [Setu's Developer Portal](https://bridge.setu.co).
2. Sign up using a standard email address.
3. Create a new "App" in the Sandbox environment.
4. Obtain the **Client ID** and **Client Secret**.
5. Add these to `backend/.env` (DO NOT commit them).

## 11. Security & Privacy Design
**Strict Policy:** SAKHI will not store sensitive data.
*   **DO NOT STORE:** The raw 12-digit Aadhaar number, the OTP, the user's address, or the raw XML payload.
*   **DO STORE (Minimum Metadata):**
    *   `identity_status`: `"VERIFIED"`
    *   `identity_provider`: `"setu_sandbox"`
    *   `identity_verified_at`: `timestamp`
*   **Our existing `User` model in `backend/app/models/user.py` already contains these exact fields and requires zero modification.**

## 12. Exact Implementation Architecture
1. **Frontend (Mobile):** User taps "Verify", enters 12 dummy digits, taps "Get OTP", enters `123456`.
2. **Backend (FastAPI):** Exposes `/kyc/init` and `/kyc/verify`.
3. **Backend Logic:** FastAPI securely holds the Setu API keys. It relays the dummy Aadhaar to Setu, receives a transaction ID, relays the dummy OTP, and receives the success response.
4. **Database (Supabase):** FastAPI updates the user's `identity_status` to `"VERIFIED"`.

## 13. Risks and Blockers
*   **Blocker:** We currently have no Setu API keys. Development cannot proceed until you register for a Setu developer account and provide the Sandbox Client ID and Secret to the `.env` file.
