# Hackathon Live Demonstration Script (5–10 Minutes)

Follow this step-by-step walkthrough to showcase the full end-to-end capabilities of the **AI-Powered Evidence Collection Bot**.

---

### Step 1: Sign in as Reviewer (0:00 – 1:00)
1. Open the frontend at `http://localhost:5173/login`.
2. Click the **Reviewer** 1-Click Demo Login button (populates `reviewer@example.com` / `Password123!`).
3. Click **Sign In**.
4. **Key Talking Point**: Highlight the executive dashboard showing LOD2 metrics: Total Controls, Active Assignments, Complete, Pending, Incomplete, and Overdue requests.

---

### Step 2: Showcase Reusable Controls & Evidence Requirements (1:00 – 2:00)
1. Click **Controls** in the sidebar.
2. Select **C001 — Periodic User Access Review**.
3. **Key Talking Point**: Explain that controls are reusable across any department or system. Show the 4 mandatory requirements defined for C001:
   - *Access Review Report*
   - *Reviewer Confirmation*
   - *Approval Evidence*
   - *Exception Report*

---

### Step 3: Showcase Dynamic Scopes (2:00 – 2:45)
1. Click **Scopes** in the sidebar.
2. **Key Talking Point**: Evidence requests are not limited to generic teams. Show how the system resolves recipients dynamically:
   - `IT Operations Team` (`TEAM`)
   - `Finance Team` (`TEAM`)
   - `John Smith` (`PERSON`)
   - `Payments Application` (`APPLICATION`)
   Each scope has a designated owner email and an independent escalation email.

---

### Step 4: Initiate a New Review & Generate Request (2:45 – 4:00)
1. Click **Reviews** in the sidebar.
2. Click **+ Initiate New Review**.
3. Select `C001 → IT Operations Team`, set review period dates and due date, and click **Initiate Review**.
4. The system automatically creates a new Evidence Request (e.g., `REQ-2026-0005`) and sends an initial email notification containing a secure, personalized submission link.

---

### Step 5: Recipient Experience — Upload Incomplete Evidence (4:00 – 6:00)
1. Open the Evidence Request details or click the public submit link:
   `http://localhost:5173/submit/demo-token-itops-2026-0001`
2. **Key Talking Point**: The business user does not need to learn complex audit software; they receive a dedicated submission portal.
3. Choose the sample file: `sample_evidence/Incomplete_User_Roster.xlsx`.
4. Click **Upload & Verify**.
5. Watch the real-time Gemini AI audit analysis appear:
   - Status changes to **INCOMPLETE**.
   - The AI identifies that the account list was uploaded, but flags missing *Exception Report* and *Approval Evidence*.
   - The backend automatically logs a `MISSING_EVIDENCE` email notification back to the user detailing exactly what items are missing.

---

### Step 6: Recipient Uploads Complete Evidence (6:00 – 7:30)
1. Now choose the comprehensive sample file: `sample_evidence/Complete_Access_Review_Q3_2026.pdf`.
2. Click **Upload & Verify**.
3. The Gemini AI engine extracts the text and verifies:
   - Status transitions to **COMPLETE**.
   - Model confidence displays at **94%+**.
   - Positive audit findings confirm all 4 requirements are verified.
   - The backend transitions the request to **COMPLETE** and sends an acceptance email.

---

### Step 7: Central Dashboard & Communication Timeline (7:30 – 8:30)
1. Return to the Reviewer interface at `http://localhost:5173/dashboard`.
2. Show the updated metrics: The request is now counted under **Complete**.
3. Open the request detail page to view the **Communication & Verification Timeline**:
   - Initial Request → Reminder #1 → Upload → Incomplete Notice → Supplementary Upload → Accepted.
4. Open the **Audit Logs** tab to show that every single action, file hash (SHA-256), and AI judgment is permanently auditable.

---

### Step 8: Autonomous Reminders & Escalations Demo (8:30 – 9:30)
1. Return to the Dashboard.
2. Highlight the **Overdue Alert Banner** showing overdue requests from the Finance Team.
3. Click the **Trigger Reminders & Escalations** button.
4. **Key Talking Point**: Explain that **APScheduler** runs this autonomously in the background inside the FastAPI process on a configurable interval (no Redis, no Celery needed!).
5. The engine queries the database, checks the past communication records to ensure idempotency, issues escalation notices for overdue items, and updates the reminder count.
