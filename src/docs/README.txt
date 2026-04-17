Financial AI - README

Menu:

Create New Profile
View Profile
Local AI
Edit Profile
Exit

What each option means now:

1. Create New Profile
This is the full guided creation flow from scratch.
It supports both personal and business profiles.
If a profile already exists, it asks for overwrite confirmation.

2. View Profile
This becomes the reporting surface.
It should include the profile summary plus the visual/report outputs you want, instead of scattering them across separate top-level menu options.
This is where tables and pie charts belong for now.

3. Local AI
This remains deterministic-first with LLM fallback.
If no profile exists, it should not hard-fail silently. It should return a deterministic message like:
No profile found. Create a new profile first with option 1.
So yes, it can suggest creating a profile instead of a hard stop.

4. Edit Profile
This stays separate from profile viewing.
It should not be a rebuild wizard.
It should be a targeted editor.


