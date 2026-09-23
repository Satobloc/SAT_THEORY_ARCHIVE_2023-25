// flc / floating liars' club — reference consumer for the live backend tunnel.
// Framework-agnostic on purpose: Sites can inline/adapt these functions.

export const FLC_LATEST_URL =
  'https://raw.githubusercontent.com/Satobloc/SAT_THEORY_ARCHIVE_2023-25/main/flc/_SITE_FEED/latest.json';

async function getJson(url, { fresh = false } = {}) {
  const target = new URL(url);
  if (fresh) target.searchParams.set('_flc', Date.now().toString());
  const response = await fetch(target.toString(), {
    cache: fresh ? 'no-store' : 'default',
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`flc backend ${response.status}: ${target}`);
  }
  return response.json();
}

export async function loadFlcBackend() {
  const latest = await getJson(FLC_LATEST_URL, { fresh: true });
  const index = await getJson(latest.story_index_url, { fresh: true });
  const stories = index.issues.flatMap((issue) =>
    issue.stories.map((story) => ({ ...story, issue }))
  );
  return {
    latest,
    index,
    stories,
    bySlug: new Map(stories.map((story) => [story.slug, story])),
  };
}

export async function loadStory(slug, backend = null) {
  const state = backend || (await loadFlcBackend());
  const story = state.bySlug.get(slug);
  if (!story) throw new Error(`Unknown flc story slug: ${slug}`);
  if (!story.text_url) {
    return { story, record: null, textAvailable: false };
  }
  const record = await getJson(story.text_url, { fresh: true });
  return { story, record, textAvailable: Boolean(record.display_text) };
}

export function backendStatus(backend) {
  return {
    connected: true,
    builtUtc: backend.latest.built_utc,
    tunnelStatus: backend.latest.tunnel_status,
    storyCount: backend.latest.summary.story_count,
    storiesWithMachineText: backend.latest.summary.stories_with_machine_text,
    issuesWithTextSource: backend.latest.summary.issues_with_text_source,
    latestUrl: FLC_LATEST_URL,
    storyIndexUrl: backend.latest.story_index_url,
  };
}

// Suggested routing behavior:
// - Contents card/title: if story.text_url, link to story.route.
// - /stories/:slug/: loadStory(slug), render record.display_text, and keep
//   story.facsimile_route visible as the source view.
// - /reconstruction-status/: show backendStatus(). If loadFlcBackend() throws,
//   show the packaged-snapshot fallback and the actual error rather than silently
//   pretending the live tunnel is current.
