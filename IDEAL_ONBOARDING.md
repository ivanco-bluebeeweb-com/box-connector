# Ideal Onboarding — Box Connector

## First-launch experience (before any connection)
Left sidebar shows a single connect form (no card decoration), stretched
to the sidebar's full width, with a secondary "Как подключить?" button
above it that opens an `overlay` help panel. The help panel walks through
creating a Box Custom App with Server Authentication (CCG):
1. Go to Box Developer Console (https://app.box.com/developers/console) ->
   Create New App -> "Custom App" -> Authentication method: "Server
   Authentication (Client Credentials Grant)".
2. In the app's Configuration tab, copy the **Client ID** and
   **Client Secret**.
3. Note your **Enterprise ID** (visible on the app's Configuration tab,
   or Admin Console -> Account & Billing).
4. In the app's Authorization tab, submit the app for admin
   authorization if it isn't auto-authorized, then have a Box admin
   approve it in the Admin Console -> Apps -> Custom Apps Manager.
5. Paste Client ID / Client Secret / Enterprise ID into the form and
   connect.

## Connect form fields (all labeled, contextual placeholders)
- Label (optional): placeholder "e.g. Acme Corp Box"
- Client ID: placeholder "from Box Developer Console > Configuration"
- Client Secret: placeholder "from Box Developer Console > Configuration"
- Enterprise ID: placeholder "from Box Developer Console or Admin Console"

## Post-connect experience
On successful connect, sidebar switches to: connection summary (label +
enterprise id), a compact set of quick links to Sites/Folders/Audit
center panels, and the "App settings" button pinned at the bottom for
disconnect. No connect-flow instructions are duplicated in the sidebar
once connected — the help modal remains the single source of setup
instructions.

## Errors surfaced to the user
- Invalid credentials -> box_client raises BoxError with Box's own error
  message (never a raw stack trace).
- 401 on first connect-time validation call (`GET /users/me`) -> clear
  "Could not verify these credentials with Box" message before saving.
- Enterprise ID mismatch -> Box returns a clear invalid_grant error,
  surfaced as-is (Box's error text is already user-actionable).
