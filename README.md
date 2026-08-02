# SoloNest — Room booking for solo travelers, students & workers

A Django MVP for budget room/guesthouse booking, built for solo travelers,
students, job-interview candidates, and workers — not full families or tourists.
(SoloNest is a placeholder name — rename anytime before launch.)

## What's included
- **Accounts**: owner & guest roles, signup/login, ID proof upload field, **Google login**
- **Listings**: title, photos, price/day & /month, room type, amenities, gender preference, stay type, map coordinates
- **Edit / delete listings**: owners can update details (including price) or remove a listing entirely
- **Search & filters**: city chips, dual price-range slider, room type, stay length, gender preference — sidebar styled after common booking sites
- **Calendar-based availability**: check-in/check-out date pickers; rooms already booked for those dates are excluded automatically
- **Map view**: live map with pins for every listing (OpenStreetMap + Leaflet, no API key required)
- **Booking flow**: request → owner approve/reject → mark completed, with a "Book Now" button on every card
- **Call button**: every listing card and detail page shows a tap-to-call button using the owner's phone number
- **In-app chat**: per-booking messaging between guest and owner
- **Reviews**: after a completed stay
- **Admin panel**: manage users, listings ("mark verified" bulk action), bookings

## Color theme
Blue / green / white — blue for header & structure, green for primary actions (Book Now, Search, Call), white/light-blue-gray for backgrounds.

## Run it locally
```bash
pip install django pillow django-allauth
python manage.py migrate
python manage.py runserver
```
Visit http://127.0.0.1:8000

### Demo accounts (seeded)
- Admin: `admin` / `admin12345` → /admin/
- Owner: `ravi_owner` / `owner12345` (has a phone number, so you'll see the Call button work)
- Guest: `priya_guest` / `guest12345`

(Re-run `python manage.py shell < seed.py` if you reset the database — note this clears existing listings first.)

## Setting up Google Login (required step — not automatic)
Google login won't work until you plug in your own credentials. This is a one-time setup:

1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth Client ID → Application type: **Web application**
3. Add this Authorized redirect URI (swap in your real domain when you deploy):
   `http://127.0.0.1:8000/accounts/google/login/callback/`
4. Copy the **Client ID** and **Client Secret** it gives you
5. Run the app, go to `http://127.0.0.1:8000/admin/`, log in as `admin`
6. Under **Sites**, edit the existing site → set domain to `127.0.0.1:8000` (or your real domain)
7. Under **Social applications**, add a new one:
   - Provider: Google
   - Client ID / Secret key: paste what Google gave you
   - Sites: move `127.0.0.1:8000` to "Chosen sites"
8. Save — "Continue with Google" on the login/signup page will now work

Until this is set up, the Google button will show a server error — that's expected, not a bug in the code.

New users signing in with Google are asked to pick a role (guest/owner) and add a phone number on their first login, since Google doesn't provide those.

## Project structure
```
soloNest/          Django project settings/urls
core/              Main app: models, views, forms, admin, urls
templates/core/    All page templates
static/css/        Design system (style.css)
media/             Uploaded listing photos (created at runtime)
```

## Suggested next steps
1. Rename the brand (SoloNest is a working name)
2. Deploy to a free tier (Render/Railway) with Postgres instead of SQLite
3. Recruit 10-15 real room owners in one city (e.g. Thanjavur) manually first
4. Add Razorpay/UPI once you have booking volume
5. Add a proper "drop a pin" map picker for owners instead of manual lat/lng entry (needs a Google Maps API key)

## New in this update

- **OTP phone verification** — real flow (send code → verify code), but no SMS gateway
  is connected yet. In dev mode the code is printed to the server console *and* shown
  on-screen so you can test it. To send real SMS, wire a provider (MSG91, Twilio) into
  `send_otp()` in `core/views.py`.
- **Razorpay/UPI payments** — real order-creation + signature-verification code using
  the official `razorpay` Python SDK. Needs your own free test-mode keys from
  https://dashboard.razorpay.com/app/keys — set them as environment variables
  `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` before running the server. Until then, the
  "Pay for this stay" button shows a clear "not connected yet" message instead of crashing.
- **Email notifications** — uses Django's console email backend by default (emails print
  to your terminal instead of sending). Switch `EMAIL_BACKEND` in `settings.py` to SMTP
  and add real credentials to send actual emails. Fires on: booking requested, approved,
  rejected, completed, and payment received.
- **In-app notifications** (practical stand-in for push) — a Notifications page shows
  the same events above inside the app. True OS-level push (phone lock-screen alerts)
  needs a Firebase Cloud Messaging project (Android) or Web Push VAPID keys (browser) —
  not included yet since that requires your own Firebase project; ask if you want this built.
- **Wishlist / Favorites** — heart icon on every card and the detail page; "Favorites"
  page in the nav.
- **Report listing** — "Report listing" link on every listing; reports show up in
  `/admin/` under Reports with moderation actions (mark reviewed / dismiss / deactivate listing).
- **Owner ID verification** — dedicated status (not submitted → pending → approved/rejected),
  a submit-ID page, and admin actions to approve/reject.
- **Booking overlap protection** — the app now blocks a guest from requesting dates that
  conflict with another request/approved booking for the same room.
- **Analytics** — `/analytics/` for owners (views, bookings breakdown, revenue estimate);
  `/admin-analytics/` for staff (platform-wide totals).
- **Admin moderation tools** — expanded Django admin: approve/reject ID verification,
  review/dismiss reports, deactivate listings, all as bulk actions.

### Setting environment variables for Razorpay (example)
```bash
export RAZORPAY_KEY_ID="rzp_test_xxxxxxxx"
export RAZORPAY_KEY_SECRET="your_secret_here"
python manage.py runserver
```
