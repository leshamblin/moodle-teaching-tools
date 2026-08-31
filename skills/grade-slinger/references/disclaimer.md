# Required Disclaimer

Every Configuration Report must include this disclaimer at the top of the document, immediately after the header and before the first section. Render it as a yellow warning-style box with `#fff3cd` background.

## Wording (substitute the contact email from user config)

> **Important:** Gradebooks are dynamic documents that change throughout the semester as assignments are added, modified, or removed. I have configured your gradebook with settings designed to maximize transparency for students, but it remains your responsibility as the instructor to verify your grade totals at the end of the semester before submitting final grades.
>
> If you would like me to perform another gradebook review during the semester or before final grades are due, please contact **[email from user config]**.

## HTML snippet (drop in immediately after `.header`)

```html
<div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px 20px; margin: 20px 0;">
  <p style="margin-bottom: 10px;"><strong>Important:</strong> Gradebooks are dynamic documents that change throughout the semester as assignments are added, modified, or removed. I have configured your gradebook with settings designed to maximize transparency for students, but it remains your responsibility as the instructor to verify your grade totals at the end of the semester before submitting final grades.</p>
  <p>If you would like me to perform another gradebook review during the semester or before final grades are due, please contact <strong>{CONTACT_EMAIL}</strong>.</p>
</div>
```

Replace `{CONTACT_EMAIL}` with the `email` value from `~/Documents/Claude/Gradebooks/.gradebook-config.json`.
