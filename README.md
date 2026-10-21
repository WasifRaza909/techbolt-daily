# Instagram AI Tech News

Every run: Google News + tech RSS -> Gemini picks the best story and writes the post -> Pillow draws a 3-slide branded carousel (no AI images) -> Instagram Graph API publishes it. Runs 3x/day on GitHub Actions. All free.

## Setup

1. **Instagram**: switch to a Business/Creator account and link it to a Facebook Page.
2. **Meta app**: create an app at developers.facebook.com, add Instagram Graph API, and generate a long-lived token with `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`. Note your Instagram Business account ID. The token expires in ~60 days, so refresh it then.
3. **Gemini**: get a free key at aistudio.google.com.
4. **GitHub**: push this folder to a **public** repo (Instagram fetches images from raw.githubusercontent.com). Then under Settings > Secrets and variables > Actions:
   - Secrets: `GEMINI_API_KEY`, `IG_USER_ID`, `IG_ACCESS_TOKEN`
   - Variables: `BRAND_HANDLE` (`@techbolt.daily`), `DRY_RUN` = `true`
5. Run the workflow manually (Actions > post-tech-news > Run workflow). In dry-run mode it only builds the post; download the `preview` artifact to check the slides and caption.
6. When you like the output, set `DRY_RUN` to `false`.

## Branding

Slides use bundled open-licence fonts (Anton, Barlow in `assets/fonts`) and an electric-blue accent on near-black. Optional settings, as environment variables locally or repo variables on GitHub:

- `BRAND_NAME`: wordmark next to the logo (defaults to `TECHBOLT`)
- `BRAND_ACCENT`: accent colour as hex, e.g. `C8FF2E` (default `2E90FF`)
- Logo files live in `assets/` (`logo.png`, `logo_ink.png`, `profile.png`). Regenerate them after changing the name or colour with `python tools/make_logo.py`, or replace them with your own transparent PNGs

## Local preview

```
pip install -r requirements.txt
set GEMINI_API_KEY=your_key
python -m src.main generate
```
Images land in `posts/`, caption is printed.

## Legal and safety measures built in

- **No third-party images.** Every slide is drawn in code. Fonts are open-licence (see `assets/fonts/LICENSES.md`) and the logo is our own.
- **Original wording.** Gemini must rewrite headlines and never copy sentences or use direct quotes from the source.
- **Attribution on every post.** Cover and takeaways slides name the publisher, and the caption credits it as an original-reporting summary.
- **Careful claims.** Reports, rumours and allegations are attributed to the source, never stated as fact. No investment, medical or legal claims. Finance stories get "Not financial advice."
- **Sensitive topics skipped.** Violence, abuse, sexual content, self-harm and deaths are filtered out in code before the AI sees them (`SENSITIVE` in `src/news.py`), and the prompt also tells Gemini to avoid crimes, lawsuits against individuals, tragedies and minors.
- Not legal advice. Good extra steps: put a short disclaimer in your Instagram bio, respond quickly to any takedown request from a publisher, and spot-check posts regularly.

## Notes

- Post times are UTC cron entries in `.github/workflows/post.yml`. GitHub can delay scheduled runs by several minutes.
- `posted.json` prevents repeating a story. Old images in `posts/` are pruned after 2 days.
- Gemini only sees the headline and RSS snippet, not the full article, so the prompt forbids inventing facts. Skim early posts before going fully hands-off.
- Posts credit the source in the caption. Don't reuse publishers' photos; the cover art is AI-generated.
