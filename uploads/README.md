# Uploads

Written by the **Manage** page (`?admin=1`). Two separate stores:

| Folder | Committed to git? | Rendered on the site? |
|--------|-------------------|-----------------------|
| `public/` | **Yes — commit it** | Yes |
| `private/` | No (git-ignored) | **Never** |

`public/` holds your profile photo, résumé, certificates and project images.
Commit it so those files survive a redeploy — Streamlit Community Cloud wipes
the filesystem on every restart, so anything uploaded on the live site and not
committed is lost.

`private/` holds passports, IDs, transcripts and other originals. It is
git-ignored, so it never reaches GitHub or the deployed app, and no public page
can read it — the code that renders the site only ever opens `public/index.json`.

Each folder keeps its own `index.json` of file metadata. Stored filenames are
random; the original name is metadata only.
