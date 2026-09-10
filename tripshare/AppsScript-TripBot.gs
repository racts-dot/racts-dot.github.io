/**
 * TripShare planning bot - the MIDDLEMAN.
 *
 * WHY THIS FILE EXISTS, in one sentence:
 * tripshare/index.html is served from a PUBLIC website, so anything written
 * into that page can be read by anyone; the AI key therefore lives here, in a
 * Google Apps Script that the page talks to but never sees inside.
 *
 * THE KEY IS NOT IN THIS FILE AND MUST NEVER BE PASTED INTO IT.
 * It goes in Script Properties. See TRIPBOT-DEPLOY.md, step 3.
 * This file is committed to a public GitHub repository. Treat every line of it
 * as readable by strangers, because it is.
 *
 * WHAT IT DOES
 *   in : { text: "5 days in Tokyo in March, we like food and temples" }
 *   out: { ok: true, items: [ {d,k,t,s,e,l,n}, ... ] }
 *
 * WHAT PROTECTS THE MONEY (all four, not one)
 *   1. DAILY_CALL_CAP    - a hard ceiling on calls per day. The spend cannot
 *                          exceed cap x cost-per-call, whatever anyone does.
 *   2. MAX_INPUT_CHARS   - a stranger cannot post a novel and be billed for it.
 *   3. MAX_OUTPUT_TOKENS - caps the expensive half of every single call.
 *   4. MIN_MS_BETWEEN    - slows a rapid loop without blocking a real person.
 *
 * HONEST LIMIT, stated rather than hidden: this endpoint is public, so a
 * determined abuser can still burn the daily cap. The cap is what protects the
 * account - it makes the worst case a KNOWN SMALL NUMBER per day, not zero.
 */

/* ---------- the settings you may want to change ---------- */

var MODEL = 'gpt-5.6-luna';
/* $0.20 in / $1.20 out per 1M tokens, read off OpenAI's live pricing page
   8 Sep 2026 and recorded in review_board/ask_openai_api.py as VERIFIED.
   A typical itinerary is ~1,000 tokens in and ~1,500 out, so about
   US$0.002 - a fifth of one US cent - per plan. */

var DAILY_CALL_CAP    = 100;   /* ~US$0.20/day worst case. THE SPEND CEILING. */
var MAX_INPUT_CHARS   = 1200;
var MAX_OUTPUT_TOKENS = 2000;
var MIN_MS_BETWEEN    = 1500;
var MAX_ITEMS         = 40;

/* ---------- nothing below here needs editing ---------- */

var PROP = PropertiesService.getScriptProperties();

var KINDS = ['flight', 'stay', 'transport', 'activity', 'food', 'note'];

var SYSTEM_PROMPT = [
  'You turn a traveller description of a trip into a structured itinerary.',
  '',
  'Reply with JSON ONLY. No prose, no markdown, no code fence. Shape:',
  '{"items":[{"d":"YYYY-MM-DD","k":"kind","t":"title","s":"HH:MM","e":"HH:MM","l":"place","n":"note"}]}',
  '',
  'Rules:',
  '- "k" must be exactly one of: flight, stay, transport, activity, food, note.',
  '- "d" is the date the item happens, in YYYY-MM-DD. Always include it.',
  '- "s" and "e" are 24-hour times. Use "" when a time is not implied. Never',
  '  invent a precise time the traveller did not give or clearly imply.',
  '- "t" is a short title, under 90 characters.',
  '- "l" is a place name, under 120 characters, or "".',
  '- "n" is a short practical note, under 500 characters, or "".',
  '- Prefer FEWER, better items. Three good entries beat ten padded ones.',
  '- Do not invent prices, booking references, flight numbers or opening hours.',
  '- If the description gives no dates at all, still return items and put them',
  '  on consecutive days starting from the trip start date you are given.'
].join('\n');

function doPost(e) {
  try {
    var body = {};
    try { body = JSON.parse(e.postData.contents); } catch (err) { body = {}; }

    var text = String(body.text == null ? '' : body.text).trim();
    if (!text) return respond({ ok: false, error: 'Nothing to plan from.' });
    if (text.length > MAX_INPUT_CHARS) {
      return respond({
        ok: false,
        error: 'That description is too long. Please keep it under ' +
               MAX_INPUT_CHARS + ' characters.'
      });
    }

    var startDate = isoOrToday_(body.start);
    var endDate   = isoOrToday_(body.end);
    if (endDate < startDate) endDate = startDate;

    var gate = spendGate_();
    if (!gate.ok) return respond({ ok: false, error: gate.error, capped: true });

    var key = PROP.getProperty('OPENAI_API_KEY');
    if (!key) {
      return respond({
        ok: false,
        error: 'The planner is not set up yet (no key configured).'
      });
    }

    var userMsg =
      'Trip start date: ' + startDate + '\n' +
      'Trip end date: '   + endDate   + '\n' +
      'Keep every item between those two dates inclusive.\n\n' +
      'The traveller wrote:\n' + text;

    var res = UrlFetchApp.fetch('https://api.openai.com/v1/chat/completions', {
      method: 'post',
      contentType: 'application/json',
      headers: { Authorization: 'Bearer ' + key },
      muteHttpExceptions: true,
      payload: JSON.stringify({
        model: MODEL,
        max_completion_tokens: MAX_OUTPUT_TOKENS,
        response_format: { type: 'json_object' },
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user',   content: userMsg }
        ]
      })
    });

    var code = res.getResponseCode();
    if (code !== 200) {
      /* Never pass the provider raw error back to a stranger browser: it can
         carry account and key detail. Log it for her, say something plain to
         them. */
      console.error('OpenAI HTTP ' + code + ': ' + res.getContentText().slice(0, 500));
      return respond({ ok: false, error: 'The planner could not be reached just now.' });
    }

    var parsed = JSON.parse(res.getContentText());
    var content = parsed &&
                  parsed.choices &&
                  parsed.choices[0] &&
                  parsed.choices[0].message &&
                  parsed.choices[0].message.content;

    if (!content) return respond({ ok: false, error: 'The planner returned nothing usable.' });

    var items = extractItems_(content, startDate, endDate);
    if (!items.length) {
      return respond({
        ok: false,
        error: 'The planner could not turn that into itinerary items. Try naming the days.'
      });
    }

    return respond({ ok: true, items: items });

  } catch (err) {
    console.error('doPost threw: ' + err);
    return respond({ ok: false, error: 'Something went wrong building that plan.' });
  }
}

/**
 * The spend ceiling and the rate limit, together.
 * A LockService lock is taken so two requests arriving at once cannot both read
 * "99 used" and both proceed - the exact read-modify-write race that made the
 * review-board counter unsafe before it moved to a real transaction.
 */
function spendGate_() {
  var lock = LockService.getScriptLock();
  try { lock.waitLock(5000); }
  catch (e) { return { ok: false, error: 'The planner is busy. Try again in a moment.' }; }

  try {
    var now = Date.now();
    var today = Utilities.formatDate(new Date(), 'Etc/UTC', 'yyyy-MM-dd');

    var last = Number(PROP.getProperty('lastCallMs') || 0);
    if (now - last < MIN_MS_BETWEEN) {
      return { ok: false, error: 'One at a time, please. Try again in a second.' };
    }

    var day = PROP.getProperty('countDay');
    var used = Number(PROP.getProperty('countUsed') || 0);
    if (day !== today) { day = today; used = 0; }

    if (used >= DAILY_CALL_CAP) {
      return {
        ok: false,
        error: 'The planner has reached its limit for today. It resets tomorrow.'
      };
    }

    /* Counted BEFORE the call, not after. A call that is made and then fails
       still cost money, so it must still count against the ceiling. */
    PROP.setProperties({
      countDay: day,
      countUsed: String(used + 1),
      lastCallMs: String(now)
    });
    return { ok: true };
  } finally {
    lock.releaseLock();
  }
}

/* Pull the items out and force every field into the shape TripShare stores.
   The model is an untrusted source like any other: nothing it returns is
   written through without being checked here first. */
function extractItems_(raw, startDate, endDate) {
  var obj;
  try {
    obj = JSON.parse(raw);
  } catch (e) {
    var m = raw.match(/\{[\s\S]*\}/);
    if (!m) return [];
    try { obj = JSON.parse(m[0]); } catch (e2) { return []; }
  }

  var list = (obj && Array.isArray(obj.items)) ? obj.items : [];
  var out = [];
  for (var i = 0; i < list.length && out.length < MAX_ITEMS; i++) {
    var a = list[i] || {};
    var d = isoDate_(a.d);
    if (!d || d < startDate || d > endDate) d = startDate;
    var title = str_(a.t, 90);
    if (!title) continue;
    out.push({
      d: d,
      k: knownKind_(a.k),
      t: title,
      s: hhmm_(a.s),
      e: hhmm_(a.e),
      l: str_(a.l, 120),
      n: str_(a.n, 500)
    });
  }
  return out;
}

function knownKind_(v) {
  for (var i = 0; i < KINDS.length; i++) if (KINDS[i] === v) return v;
  return 'note';
}

function str_(v, max) {
  if (typeof v !== 'string') return '';
  var s = v.replace(/\s+/g, ' ').trim();
  return s.length > max ? s.slice(0, max) : s;
}

function isoDate_(v) {
  if (typeof v !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(v)) return '';
  var p = v.split('-'), y = +p[0], m = +p[1], da = +p[2];
  var dt = new Date(Date.UTC(y, m - 1, da));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== da) return '';
  return v;
}

function isoOrToday_(v) {
  return isoDate_(String(v || '')) ||
         Utilities.formatDate(new Date(), 'Etc/UTC', 'yyyy-MM-dd');
}

function hhmm_(v) {
  return (typeof v === 'string' && /^([01]\d|2[0-3]):[0-5]\d$/.test(v)) ? v : '';
}

function respond(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/** Run this from the editor to see today's usage without touching the site. */
function checkUsage() {
  var today = Utilities.formatDate(new Date(), 'Etc/UTC', 'yyyy-MM-dd');
  var day   = PROP.getProperty('countDay');
  var used  = Number(PROP.getProperty('countUsed') || 0);
  if (day !== today) used = 0;
  var costPerCall = 0.002;
  Logger.log('Today (' + today + '): ' + used + ' of ' + DAILY_CALL_CAP + ' calls used.');
  Logger.log('Estimated spend today: about US$' + (used * costPerCall).toFixed(3));
  Logger.log('Worst case if the cap is hit: about US$' +
             (DAILY_CALL_CAP * costPerCall).toFixed(2) + ' per day.');
}
