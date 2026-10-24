# Build this app: Premier University — Entrance Exam Kiosk + Admin

A face-verified attendance system for a university entrance exam. Two surfaces:

1. **Kiosk** — a public, full-screen tablet app used by applicants (register, then time in on exam day).
2. **Admin** — a staff console (login, exam batches, attendance).

Style: calm, institutional, navy + off-white, serif display type for headings, Inter for UI text. Generous whitespace, 8px spacing scale, soft 8–16px radii, subtle card shadows.

---

## Fidelity rules (read first)

The attached screenshots are the source of truth. Reproduce them; do not redesign or embellish.

- **Copy exactly.** Use the strings, capitalisation and punctuation written below. Do not convert labels to sentence case or invent subtitles.
- **Add nothing.** No invented data, dates, avatars/initials, icons, counters, helper lines, extra buttons or extra panels. Only the elements listed per screen.
- **Headings are left-aligned.** No eyebrow/kicker line above them (“STEP 2 OF 4”, “MONDAY, OCTOBER 19” do not exist).
- **Navigation labels are fixed**: Dashboard · Manage Exam Schedule · View Attendance. Never rename them (no “Overview”, “Exam schedule”, “Attendance”).
- **Button labels and casing are fixed**: “Manage Exam Schedule”, “View Attendance”, “Create Batch”, “Export CSV”, “Log In”, “Done”, “Reserve My Seat”, “Continue to Batch Selection”, “I understand”.
- **Stat cards: exactly three**, number + label only — no icon in the corner, no “+12 this week”, no “67% attendance”, no “3 upcoming”.
- **No success tick** at the top of the confirmation screen; the heading is the first element.
- **Empty inputs look empty**: white fill, 1px `#E2E5EA` border. Do not show every field in a navy focused state.
- **Keep the form grid** exactly as described per screen (which fields share a row matters).
- **Consent is a full card**, not a one-line checkbox: paragraph + underlined link + checkbox + hint line.

---

## Design tokens

### Colour
| Token | Hex | Use |
|---|---|---|
| primary | `#1E2A4A` | navy: side panels, buttons, headings |
| primary light | `#2C3D66` | button hover |
| bg | `#F6F7F9` | page background |
| surface | `#FFFFFF` | cards, inputs, tables |
| text | `#1A1D24` | body text |
| text muted | `#5B6472` | secondary text |
| success | `#2E7D6B` | present badge, success flash |
| warning | `#C97A2B` | ongoing badge, focus ring on kiosk cards |
| danger | `#A13A3A` | errors, delete, absent |
| border | `#E2E5EA` | hairlines, input borders |

Tints: success bg `#E9F1EF`, warning bg `#FFF3E4`, danger bg `#FBEAEA`, neutral badge bg `#EDEEF0`, selected card `#EEF1F7`.

### Type
- Display: **Source Serif 4** (600) — page headings, kiosk headings, big numbers, reference codes.
- Body: **Inter** (400/500/600/700) — everything else.
- Kiosk heading 28px/1.2, panel heading up to 36px; admin page heading 24px/700; card title 15–22px; body 14–16px; small 12–13px.

### Shape & spacing
- Radii: 4px (kiosk buttons/inputs), 8px (admin controls), 12px (cards), 16px (modals, kiosk action cards), 99px (pills).
- Shadow card: `0 1px 2px rgba(30,42,74,.04), 0 4px 16px rgba(30,42,74,.04)`.
- Shadow modal: `0 24px 60px rgba(30,42,74,.28)`.
- Spacing scale: 4, 8, 12, 16, 24, 32, 40, 48, 64.

---

## 1. Kiosk home

Full-viewport **50/50 split**.

**Left half (navy #1E2A4A):**
- Top-left brand: “Premier University” (serif 25px, white) with “Entrance Exam Kiosk” beneath (Inter 13px, #AEB7CC).
- Centred circular face-scan illustration (concentric rings, white rounded brackets, simple smiling face, thin mint scan line).
- Bottom-left: “Welcome” (serif ~64px, white) and “Face-verified registration and time-in for the entrance exam.” (#C9D1E4).

**Right half (#F6F7F9), vertically centred, max 560px:**
- Heading “What would you like to do?” (serif ~36px, navy).
- Two large action cards, stacked, 16px gap:
  - **Register** — white card, 2px navy border, light navy tint `#EEF1F7`, circular navy icon (person +), title serif 30px, text “First time here. Register before exam day.”, arrow right.
  - **Time in** — white card, 2px grey border, outlined navy circular icon (face scan), title serif 30px, text “Already registered and it's exam day. Scan your face to time in.”, arrow right.
- No other text.

---

## 2. Shared kiosk layout (registration + time-in)

Left **280px sticky navy panel**:
- Brand (“Premier University” + “Entrance Exam Kiosk”).
- Vertical step list, 34px circles: completed = mint `#2E7D6B` with white tick; current = white circle, navy number, white label; upcoming = outlined, muted.
  - Registration flow: Face → Details → Batch → Confirmed.
  - Time-in flow: Scan → Timed in.
- Nothing at the bottom.

Right content area: max 640px, vertically centred; heading (serif clamp 28–36), subtext 16–18px muted, then content.

---

## 3. Face capture

- Heading “Face Capture”, subtext “Position your face in the frame. The Capture button turns on once your face is clear.”
- 4:3 live camera frame, 12px radius, **3px border that changes colour**: grey (starting) → amber (no face / multiple faces / bad light) → green (ready).
- Status line under it with a coloured dot: “Starting camera…”, “Face detected clearly - ready to capture.”
- Full-width navy **Capture** button (disabled grey until ready).
- Small centred helper: “Your face is converted to a numeric template. The photo itself is not stored.”

---

## 4. Registration details

- Heading “Applicant Registration”, subtext “Your face was captured. Now enter your details.”
- Field grid, exactly these rows:
  1. First Name | Middle Name (optional)
  2. Last Name (wider) | Suffix (optional)
  3. Contact Number (placeholder `09XXXXXXXXX`) | Email (placeholder `name@example.com`)
  4. Address (full width)
- **Biometric consent card** (light grey `#F6F7F9`, 8px radius) containing, in order:
  - paragraph “Biometric consent. We store a numeric template of your face - not your photo - to check for duplicate registrations and to record your attendance on exam day.”
  - underlined navy link “Read the full biometric consent notice”
  - checkbox row “I have read and accept the biometric consent notice.”
  - hint “Read the notice above to enable this box.”
- Full-width navy **Continue to Batch Selection**.
- **Consent modal** (620px, 16px radius, dark backdrop): title “Biometric Consent Notice”, lead “Before proceeding, please read and acknowledge how your biometric data will be used.”, then three sections with uppercase 14px headings:
  - Purpose of Collection — “This system captures your facial image to generate a facial embedding, a numerical representation of your facial features. This embedding will be used to assist in identity verification and attendance monitoring during the entrance examination.”
  - Data Storage and Privacy — “Your facial embedding will be processed and stored for the system's demonstration and attendance verification purposes. Access to the data should be restricted to authorized personnel, and the data should be protected against unauthorized access or misuse.”
  - Data Retention — “Biometric data will be retained only for the specified demonstration period or as otherwise explained in the system's privacy notice, after which it will be securely deleted, subject to applicable requirements.”
  - Right-aligned navy button “I understand”.

---

## 5. Batch selection

- Heading “Select Your Exam Batch”, subtext “Choose an open exam slot below.”
- List of selectable cards (14px radius, 2px border): custom 28px radio ring on the left, then “Batch 14” (serif 22px), date + time, “Building, Room”, a thin progress meter of seats reserved and “2 / 12 seats reserved”, and a right-aligned pill “N seats left” (mint; amber when ≤5 left).
- Selected card: navy border + `#EEF1F7` fill.
- Full-width **Reserve My Seat**.
- Empty state: circular icon, “No exam batches are open right now”, “Please check back later.”, outlined **Back to start**.

---

## 6. Confirmation

- Heading “Registration Confirmed” (no icon above it), text “Thank you, {name}. Your seat is reserved. Keep your registration number.”
- Dashed-border box: label “Registration Number”, large serif code `REG-2026-BD9BF0`.
- Details card, label left / value right, exactly six rows: Name, Batch ID (`14`), Date, Time, Building, Room (Building and Room are separate rows, not one “Location” line).
- Full-width navy **Done**.
- Steps panel: all four ticked.

---

## 7. Time-in result

- Success: navy heading “Time In Recorded”, “Welcome, {name}. Your attendance has been recorded.”
- Repeat scan: **red** heading “Already Timed In”, “{name}, you already timed in earlier. Nothing new was recorded.”
- Dashed box: “Reference Number” + `ATT-2026-AC82BE`.
- Details: Name, Batch ID, Building, Room, Time In (e.g. “Oct 24, 2026 09:36 PM”).
- Navy **Done**.
- Steps: Scan ✓, Timed in ✓.

There is **no “Late” status** anywhere: arriving after the start still shows “Time In Recorded”.

---

## 8. Admin login

50/50 split again.

**Left (navy):** brand “Premier University” + “Entrance Exam System”; white circular badge with a face-scan icon; headline “Manage Exams and Attendance” (serif 42px, two lines); five softly floating, slightly rotated rounded-square icon tiles (clipboard, shield, calendar, user, check) at different speeds.

**Right:** centred white card (380px, 12px radius, soft shadow): “Admin Login” (serif 30px), “Enter your staff credentials to continue.”, Username, Password, full-width navy **Log In**. Error banner above the fields: pale red, 13px.

---

## 9. Admin shell

240px sticky navy sidebar: “Entrance Exam Admin” brand (serif, two lines), nav (Dashboard, Manage Exam Schedule, View Attendance — active row = 12% white), user block near the bottom (name in white + “Administrator” underneath, no avatar circle), “Log Out” link.

Content: 40/48px padding, page header (heading + subtext left, actions right), then the page.

---

## 10. Dashboard

- “Dashboard”, “Welcome, {name}. Here is the overall picture.” (no date line above the heading).
- Right actions: “Manage Exam Schedule” (secondary) and “View Attendance” (primary).
- Exactly three stat cards, each just a big serif number + small muted label: **Registered applicants**, **Time-ins recorded**, **Exam batches**. No icons, no sub-lines.
- Two panels side by side (3fr / 2fr):
  - **Upcoming batches** — rows: “#14 Oct 24, 2026”, time + “wgwa, Room 212121” underneath, seats “2 / 23232” with a thin green fill bar, status pill (open green / ongoing amber / full grey), “Manage” link.
  - **Recent time-ins** — rows: name, “Batch #14 · ATT-2026-…” underneath, timestamp right.
- Empty panels: centred bold line + hint.

---

## 11. Manage Exam Schedule

- Header: heading + “Create Batch” primary button (with + icon).
- Toolbar: search box (“Search by Batch ID or Building...”), Status select, date picker.
- Table, each row a white rounded strip: Batch ID (`#5`, bold navy), Date, Window (12-hour), “Building / Room” stacked, Seats with fill bar, Status pill, Actions (“Edit”, “Delete” in red).
- Create Batch is a centred **modal** (“Create New Batch”): 2-column grid — Exam Date, Building, Start Time, Room, End Time, Capacity — then “Cancel” + “Save Batch”.
- Flash banners above content: green “Batch created.”, red validation errors.

---

## 12. View Attendance

- Header: “View Attendance”, “Every registered applicant and their time-in status.”, right “Export CSV” button.
- Toolbar: search (“Search by name or registration number...”), batch select (“Batch: All”), status select (All / Not yet timed in / Present / Absent), record counter right (“5 applicants”).
- Table strips: Full Name (bold), Registration No., Batch pill (“Batch 14”, mint), Time-In (“Oct 24, 2026 10:20 PM” or “—”), Reference No. (or “—”), Status pill:
  - **Present** — mint
  - **Absent** — pale red
  - **Not yet timed in** — grey
- Empty state: “No records”.

---

## Component states

- **Buttons**: primary navy → hover `#2C3D66`; secondary white/grey border → hover `#F6F7F9`; focus ring 2px navy, offset 2px. Kiosk buttons are full width, 16px text, 4px radius; admin buttons are inline, 14px, 8px.
- **Inputs**: 1px `#E2E5EA`, radius 8 (admin) / 1.5px, radius 4 (kiosk); focus = navy border + `0 0 0 3px rgba(30,42,74,.12)` (admin) or 2px navy outline offset 1 (kiosk).
- **Kiosk action cards**: hover = 2px black `#1A1D24` outline, offset 2.
- **Batch cards**: hover = navy border; selected = navy border + `#EEF1F7`.
- **Sidebar links**: hover/active = `rgba(255,255,255,.12)` background, white text.
- **Modals**: dark navy 45% backdrop, 0.18s fade/scale-in.

## Behaviour worth designing for

- Registration validates: required fields, contact must be `09XXXXXXXXX`, email format, and **both email and contact number must be unique** (a single message can name both).
- Consent checkbox is disabled until the notice modal is acknowledged.
- Time In window: opens 15 min before start, closes at end time. Outside it the kiosk shows an error.
- A second scan shows the red “Already Timed In” screen.
- Attendance status: Present (timed in), Not yet timed in (batch still open), Absent (batch closed, no time-in).

## Responsive

- Kiosk: below 860px the side panel becomes a top bar and the home split stacks vertically; step labels hide except the current one.
- Admin: below 960px dashboard panels stack; below 720px sidebar becomes a top bar and tables scroll horizontally.
