# mpos-badgehub-publish

Reusable composite GitHub Action that publishes a MicroPythonOS app to
[BadgeHub.eu](https://badgehub.eu) via its draft-upload-then-publish API
(`https://badgehub.eu/api-docs/swagger.json`). Any repo with a standard
MicroPythonOS app layout (a folder with `MANIFEST.JSON`, an entrypoint
`.py`, and an icon) can reuse this without modification.

## One-time setup (per project, done by a human on badgehub.eu)

1. Log into badgehub.eu and use "Create Project" to register your app,
   selecting `mpos_api_0` under "Badge".
2. Generate the project's API token (`POST /api/v3/projects/{slug}/token`
   while logged in -- there's a button for this on the project page).
3. Add that token as a repo secret, e.g. `BADGEHUB_API_TOKEN`.

## Usage

```yaml
- name: Publish to BadgeHub
  uses: tjorim/mpos-badgehub-publish@v1
  with:
    slug: your-project-slug
    api-token: ${{ secrets.BADGEHUB_API_TOKEN }}
    app-dir: path/to/your_app
    categories: Game
```

`name`, `description`, `long_description`, `author`, `version`, and the
entrypoint are all read from `app-dir/MANIFEST.JSON` automatically -- there
is exactly one place those live. Only BadgeHub-specific fields that have no
`MANIFEST.JSON` equivalent are action inputs; see `action.yml` for the full
list (`categories`, `badges`, `license-type`, `git-url`, `icon`, `api-base`).

Set `dry-run: true` to log the planned uploads/metadata/publish calls
without making any network requests -- useful for verifying the file list
and metadata before pointing it at a real project.

## Verification, not just a 204

A successful HTTP status from `publish` doesn't by itself prove the new
content is live, so the script also uses BadgeHub's public (unauthenticated)
`GET /project-latest-revisions/{slug}` endpoint: once before uploading, as a
reachability check alongside `GET /ping`, and once after publishing, to
confirm the revision number actually advanced. The action fails loudly if it
didn't, rather than reporting success on a publish call that silently no-opped.

## Stale-file cleanup

BadgeHub's draft carries forward the file set from the previous published
revision rather than starting empty -- deleting a file locally doesn't
un-publish it on its own. Before setting metadata, this action diffs the
current draft's file listing (`GET /projects/{slug}/draft`) against the
local app folder and `DELETE`s anything no longer present, so a removed
module doesn't linger in BadgeHub forever.

## Field name for file uploads

The published swagger spec doesn't document the multipart field name for
`POST /draft/files/{filePath}` -- it's wired via `multer.single("file")`
directly in BadgeHub's Express router, outside their typed `ts-rest`
contract, so their OpenAPI generator has nothing to describe it from (filed
as [BadgeHubCrew/badgehub-app#7](https://github.com/BadgeHubCrew/badgehub-app/issues/7)).
`publish.py` sends it as `file`, confirmed directly against BadgeHub's own
frontend (`formData.append("file", file)`) and backend
(`upload.single("file")`) source -- not a guess. The upload code path
itself hasn't been exercised against a live project end-to-end yet, though;
if it ever rejects an upload, this is still the first thing to check.
