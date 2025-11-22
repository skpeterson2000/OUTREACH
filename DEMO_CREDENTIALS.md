# Demo User Credentials

All demo users use the password: **password123**

## Licensed Clinical Staff (Full Access)

### Registered Nurse (RN)
- **Username:** `nurse.jane`
- **Name:** Jane Smith
- **Access:** Full medication administration, patient care documentation, all clinical features

### Licensed Practical Nurse (LPN)
- **Username:** `nurse.bob`
- **Name:** Bob Johnson
- **Access:** Medication administration, basic patient care, most clinical features

### Pharmacist
- **Username:** `pharm.sarah`
- **Name:** Sarah Williams
- **Access:** Medication review, ADR monitoring, clinical consultations (cannot administer meds)

## Administrative Staff

### Administrator
- **Username:** `admin.mike`
- **Name:** Mike Davis
- **Access:** Full system access, user management, reports, billing

## Delegated Medication Staff

### Trained Medication Assistant (TMA)
- **Username:** `tma.lisa`
- **Name:** Lisa Chen
- **Access:** Administer medications under RN delegation, patient care activities, vital signs (cannot hold/modify med orders)
- **Note:** TMAs are CNAs with additional training who can administer medications under RN supervision. Scope varies by state.

## Direct Care Staff (Support Only)

### Certified Nursing Assistant (CNA)
- **Username:** `cna.maria`
- **Name:** Maria Garcia
- **Access:** Patient care activities, vital signs, ADLs, can request med reorders (cannot administer medications without TMA training)

### Home Health Aide (HHA)
- **Username:** `hha.david`
- **Name:** David Martinez
- **Access:** Basic patient care, ADLs, observation, can report concerns (cannot administer medications)

---

## Role Capabilities Summary

| Feature | RN/LPN | Pharmacist | Admin | TMA | CNA/HHA |
|---------|--------|------------|-------|-----|---------|
| View Patients | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Medications | ✅ | ✅ | ✅ | ✅ | ✅ |
| Administer Meds | ✅ | ❌ | ✅ | ✅ (Delegated) | ❌ |
| Add/Modify Meds | ✅ | ✅ | ✅ | ❌ | ❌ |
| Hold/Discontinue | ✅ | ✅ | ✅ | ❌ | ❌ |
| Request Reorders | ✅ | ✅ | ✅ | ✅ | ✅ |
| Report Concerns | ✅ | ✅ | ✅ | ✅ | ✅ |
| ADR Alerts | ✅ | ✅ | ✅ | ✅ | View Only |
| Document Visits | ✅ | ❌ | ✅ | Limited | Limited |
| Billing/Reports | ❌ | ❌ | ✅ | ❌ | ❌ |

---

**Philosophy:** Minimize clicks, maximize face-to-face patient time. Each role sees only what they need to do their job efficiently.
