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

## Direct Care Staff (View-Only for Meds)

### Certified Nursing Assistant (CNA)
- **Username:** `cna.maria`
- **Name:** Maria Garcia
- **Access:** Patient care activities, vital signs, ADLs (cannot administer medications)

### Home Health Aide (HHA)
- **Username:** `hha.david`
- **Name:** David Martinez
- **Access:** Basic patient care, ADLs, observation (cannot administer medications)

---

## Role Capabilities Summary

| Feature | RN/LPN | Pharmacist | Admin | CNA/HHA |
|---------|--------|------------|-------|---------|
| View Patients | ✅ | ✅ | ✅ | ✅ |
| View Medications | ✅ | ✅ | ✅ | ✅ |
| Administer Meds | ✅ | ❌ | ✅ | ❌ |
| Add/Modify Meds | ✅ | ✅ | ✅ | ❌ |
| Hold/Discontinue | ✅ | ✅ | ✅ | ❌ |
| ADR Alerts | ✅ | ✅ | ✅ | View Only |
| Document Visits | ✅ | ❌ | ✅ | Limited |
| Billing/Reports | ❌ | ❌ | ✅ | ❌ |

---

**Philosophy:** Minimize clicks, maximize face-to-face patient time. Each role sees only what they need to do their job efficiently.
