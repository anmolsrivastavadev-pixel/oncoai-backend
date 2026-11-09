# OncoAI Privacy Policy

> **OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.**

*Draft for legal review. Publish at a public, non-editable HTML URL (not a PDF), for example
`[https://oncoai.app/privacy]`, link it from the Play Console and from inside the app (sign-up
screen and Settings).*

**Effective date:** [DATE]
**Last updated:** [DATE]

---

## 1. Who we are

OncoAI ("OncoAI", "we", "us") is provided by **[LEGAL ENTITY NAME]**, [REGISTERED ADDRESS]
("the controller"). You can contact us about privacy at **[privacy@oncoai.app]**.
[If required: our Data Protection Officer / EU or UK representative is [NAME, CONTACT].]

This policy explains what information the OncoAI Android app, web app and backend services
(together, "the Service") collect, why we collect it, who we share it with, and the choices and
rights you have, including how to delete your account.

**OncoAI is an educational tool, not a medical service.** It is not a medical device. It does not
diagnose, treat, cure or prevent any medical condition, and it does not replace a doctor or
dermatologist. If you are worried about a spot on your skin, talk to a healthcare professional.

## 2. Information we collect

### 2.1 Account information
- **Email address, full name and password.** Used to create and secure your account. We store your
  password only as a salted one-way hash (bcrypt). We never store it in readable form.
- **Role** (user, moderator or admin). Used to control access to moderation tools.

### 2.2 Optional profile information
You can choose to add the following. You can leave any of it blank and edit or remove it at any time:
- Date of birth
- Skin type (Fitzpatrick type I–VI)
- Location (free text, for example a city)
- Bio

### 2.3 Skin photos (sensitive)
When you add a photo of a spot on your skin, using the camera or your gallery:
- The photo is uploaded to our servers over an encrypted (HTTPS) connection.
- Before the photo is uploaded, the app removes embedded metadata [CONFIRM once on-device EXIF
  stripping ships, see the Data Safety form note 1]. Our servers remove it again before storing:
  we **remove all embedded metadata**, including EXIF data, GPS location,
  camera details and comments. We keep only the image pixels.
- We store the photo and a small thumbnail in private storage linked to your account, **encrypted
  at rest**. [CONFIRM: production sets `IMAGE_ENCRYPTION_KEY`.] Photos are never published and can
  only be retrieved through your own signed-in account.
- An automated image-analysis model runs on our own servers. It describes visual features of the
  photo, such as symmetry, border, colour variation and relative size, to support self-tracking and
  education. It does not produce a diagnosis.

### 2.4 Skin tracking and health-related information (sensitive)
Information you enter or that the Service generates for you:
- **Tracked spots:** the name you give each spot, its body location and your notes.
- **Symptoms you log:** for example itching, bleeding, pain, or changes in size, colour or shape,
  plus any notes.
- **Scan results:** the visual-feature measurements, photo-quality checks and educational messages
  produced for each photo, plus the time each scan was taken.
- **Appointments and reminders:** the dermatologist or clinic listing you chose, the date and time,
  the reason you entered, any scan you attached, and your reminders.

We treat all of the above as **health data**, a special category of personal data. We only process
it to provide the features you use, and only with your explicit consent (see section 4).

### 2.5 Community content
If you use the community area: your posts, comments, reactions and any reports you submit. You can
post **anonymously**. Other users then see no name, but we still keep the link to your account
internally so we can moderate content and honour deletion requests. Our systems block posts and
comments that contain phone numbers or email addresses, to protect your privacy. Please don't share
health details in the community that you would not want other people to read.

### 2.6 Assistant conversations
If you use the educational assistant, we process the messages you send and the replies. When the
assistant is powered by an AI provider (see section 5), your most recent messages (up to 12) are sent
to that provider to generate the reply. If you choose to attach a photo entry, a text summary of its
visual measurements is sent too. Your photo, name and email address are never sent.
**We don't store assistant conversations on our servers.** They are processed only to produce
the reply, and the app keeps the conversation on screen.

### 2.7 Technical information
- **IP address**, held briefly in memory for security and rate limiting (for example, limiting login
  attempts). It is not written to our logs or database.
- **Server logs**: request times, request IDs, the address requested and error details, used to keep
  the Service secure and working. Logs don't include your IP address, password or photos.
  [CONFIRM: retention period, e.g. 30 days.]
- **On your device**, the app stores your sign-in tokens in the app's private storage (Android
  SharedPreferences) so you stay signed in. It also schedules reminder notifications locally.

### 2.8 What we do *not* collect
- We do not use advertising IDs and we do not show ads.
- We do not collect your precise device location.
- We do not read your contacts, and we do not access photos you have not chosen to upload.
- We do not use third-party analytics, advertising or crash-reporting SDKs. (Checked against the
  Android build at `55d1bac`. Update this section if any are added.)

## 3. Device permissions

| Permission | Why | When |
|---|---|---|
| Camera | To take a photo of a spot you want to track | Only when you tap to take a photo |
| None: Android system photo picker | To pick an existing photo. The picker gives OncoAI only the photo you select, never the rest of your library | Only when you choose "from gallery" |
| Notifications | To show reminders you set (re-checks, appointments) | Asked when you first create a reminder |

You can withdraw any permission at any time in Android Settings. The rest of the app keeps working.

## 4. Why we use your information (and legal bases)

| Purpose | Data | Legal basis (EU/UK GDPR) |
|---|---|---|
| Create and secure your account | Account information, technical information | Performance of a contract |
| Store, analyse and compare your skin photos; show your history and dashboard | Skin photos, tracking and health data | **Explicit consent** (Art. 9(2)(a)), given when you start using scan features |
| Reminders and appointment requests | Appointments, reminders | Explicit consent / contract |
| Community features and moderation | Community content, account information | Contract; legitimate interest in keeping the community safe |
| Educational assistant | Assistant messages, optionally attached scan results | Explicit consent |
| Security, fraud and abuse prevention, rate limiting | Technical information | Legitimate interests |
| Legal obligations | As required | Legal obligation |

**We do not sell your personal data. We do not use your health data for advertising.**
**We do not use your photos or health data to train or improve AI models** [CONFIRM. If this changes,
it will be opt-in only and this policy will be updated before that happens].

You can withdraw consent at any time by deleting the relevant photos or data, or your whole account.
Withdrawing consent does not affect processing that already took place.

## 5. Who we share information with

We share personal data only with service providers that process it on our behalf, under contracts
that require them to protect it and to use it only to provide their service to us:

| Provider | Purpose | Data |
|---|---|---|
| [HOSTING PROVIDER, REGION] | Servers, database and encrypted photo storage | All Service data |
| Anthropic PBC (Claude API), *if the AI assistant is enabled* | Generating assistant replies | Assistant messages, and scan results you choose to attach |
| [EMAIL PROVIDER, if used] | Account emails | Email address |

Dermatologist and clinic listings are shown for information only. Appointments you record in OncoAI
are stored only in your OncoAI account and are **not sent to any clinic**. You still need to book
with the clinic directly. [If a real booking integration is added later, name it here as sharing,
describe what is sent, and get consent at booking.]

We may also disclose information if the law requires it, to protect someone's safety, or as part of
a merger or acquisition. In that case, the new owner must follow this policy.

## 6. International transfers

[If data leaves the EEA/UK: describe the transfer and the safeguard, for example the EU Standard
Contractual Clauses or the UK IDTA, including transfers to the AI assistant provider in the United
States.]

## 7. How long we keep information

| Data | Retention |
|---|---|
| Account, profile, photos, tracking, appointments, reminders | Until you delete them or delete your account |
| Community posts and comments | Until you or a moderator delete them, or you delete your account |
| Assistant conversations | Not stored on our servers. The AI provider's retention follows its API terms: [CONFIRM, e.g. "deleted within 30 days and not used for training"] |
| Server logs and security records | [30] days |
| Encrypted backups | Overwritten within [30] days of deletion |

## 8. Deleting your data and your account

**In the app:** go to **Profile → Delete account**. This permanently deletes your account,
profile, all skin photos and thumbnails, tracked spots, scans, symptom logs, appointments, reminders,
community posts, comments and reactions. You can also delete individual photos, scans, spots and
reminders at any time.

**Without the app:** request deletion at **[https://oncoai.app/delete-account]**, or email
**[privacy@oncoai.app]** from your account email address with the subject "Delete my OncoAI account".
We will verify that the request comes from the account holder, complete it within **[30] days**, and
confirm by email.

**What happens:** data is removed from our live systems straight away. Copies in encrypted backups are
overwritten within [30] days. We ask our service providers to delete any copies they hold. We may keep
a minimal record that a deletion request was handled, and any information we are legally required to
keep. We will tell you if that applies.

## 9. Security

We use HTTPS for all traffic, bcrypt password hashing, short-lived access tokens, encryption at rest
for photos, owner-only access checks on every photo request, removal of photo metadata, and rate
limiting. No system is perfectly secure. If a breach affects your data, we will notify you and the
regulators as the law requires.

## 10. Your rights

Depending on where you live (for example under the EU/UK GDPR, the California CCPA/CPRA, or
Washington's My Health My Data Act), you may have the right to: access your data; correct it; delete
it; receive a copy in a portable format; restrict or object to processing; withdraw consent; and
complain to your data protection authority. To exercise these rights, email **[privacy@oncoai.app]**.
We will not treat you differently for using your rights.
[CONFIRM: whether an in-app data export exists. If not, say that exports are provided on request.]

## 11. Children

OncoAI is not intended for people under **[18]** and we do not knowingly collect their data. If you
believe a child has created an account, contact us and we will delete it.

## 12. Changes to this policy

If we make a material change, we will tell you in the app before it takes effect and update the
"Last updated" date. If a change would expand how we use your health data, we will ask for your
consent again.

## 13. Contact

[LEGAL ENTITY NAME], [ADDRESS] — **[privacy@oncoai.app]**

---

*OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or
treatment advice.*
