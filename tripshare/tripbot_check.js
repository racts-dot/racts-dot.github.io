/* tripbot_check.js - the offline proof. Free to run, no API key, no network.
 *
 *   node tripbot_check.js
 *
 * WHAT IT PROVES. It loads the REAL AppsScript-TripBot.gs and the REAL normItem
 * out of index.html - never a retyped copy, because a retyped copy tests the
 * copy - and pushes two things through them:
 *
 *   1. tripbot_real_replies.json, which is what gpt-5.6-luna ACTUALLY replied
 *      on 11 Sep 2026 (two real calls, US$0.00149 for the pair). Both should
 *      come through clean, every date inside the trip.
 *   2. Seven deliberately broken replies. Each must fail in the stated way.
 *      A checker that cannot be made to fail is not a checker.
 *
 * Three of those seven found real defects on the day it was written:
 *   - a reply keyed "itinerary" instead of "items" produced ZERO suggestions,
 *     and an error message that blamed the traveller's wording;
 *   - an item dated a year outside the trip was silently re-dated onto day one,
 *     where it looked deliberate;
 *   - 150 items were silently cut to 40 with nothing said about it.
 * All three are fixed. This file is what keeps them fixed.
 */
const fs = require('fs'), os = require('os'), path = require('path'), vm = require('vm');
/* This file LIVES in the folder it reads, so __dirname is the answer and no
   guessing is needed. It used to be path.join(os.homedir(), 'Sales Tracker
   Website', 'tripshare'), which is true on the MacBook and FALSE on the Windows
   machine, where the folder now sits under Desktop/Desktop. The check therefore
   crashed on one of the two computers it exists to protect - and a check that
   cannot run is indistinguishable from a check that passed.
   Line 53 was already using __dirname for the replies file, so the file
   disagreed with itself. */
const base = __dirname;
const gs   = fs.readFileSync(path.join(base, 'AppsScript-TripBot.gs'), 'utf8');
const html = fs.readFileSync(path.join(base, 'index.html'), 'utf8');

const sandbox = {
  PropertiesService: { getScriptProperties: () => ({ getProperty: () => null, setProperties: () => {} }) },
  LockService: { getScriptLock: () => ({ waitLock(){}, releaseLock(){} }) },
  UrlFetchApp: {}, ContentService: { createTextOutput: () => ({ setMimeType: () => {} }), MimeType: {} },
  Utilities: { formatDate: () => '2026-01-01' }, Logger: { log: console.log }, console,
};
vm.createContext(sandbox);
vm.runInContext(gs, sandbox);

/* the page-side pair: uid/isoDate/knownKind/str/hhmm/normItem, lifted verbatim */
const grab = (name) => {
  const i = html.indexOf('function ' + name + '(');
  if (i < 0) throw new Error('missing ' + name);
  let d = 0, j = html.indexOf('{', i);
  for (let k = j; k < html.length; k++) {
    if (html[k] === '{') d++;
    else if (html[k] === '}') { d--; if (!d) return html.slice(i, k + 1); }
  }
};
const page = {};
vm.createContext(page);
vm.runInContext(fs.readFileSync(path.join(base,'index.html'),'utf8').match(/var KINDS = \[[\s\S]*?\];/)[0], page);
for (const f of ['uid','isoDate','knownKind','str','hhmm','safeUrl','normItem'])
  vm.runInContext(grab(f), page);

const replies = JSON.parse(fs.readFileSync(path.join(__dirname, 'tripbot_real_replies.json'), 'utf8'));

for (const [name, r] of Object.entries(replies)) {
  console.log('\n================ ' + name + ' ================');
  const got = sandbox.extractItems_(r.raw, r.start, r.end); const items = got.items;
  console.log('extractItems_ returned ' + items.length + ' items, dropped ' + got.dropped);
  let bad = 0;
  items.forEach((a, i) => {
    const problems = [];
    if (a.d < r.start || a.d > r.end) problems.push('DATE OUT OF RANGE');
    if (!a.t) problems.push('NO TITLE');
    if (!['flight','stay','transport','activity','food','note'].includes(a.k)) problems.push('BAD KIND ' + a.k);
    if (a.t.length > 90) problems.push('TITLE TOO LONG');
    if (a.s && !/^([01]\d|2[0-3]):[0-5]\d$/.test(a.s)) problems.push('BAD TIME');
    /* now the page half, which is what actually gets stored */
    const p = page.normItem(a, r.start);
    if (p.t !== a.t) problems.push('page normItem CHANGED the title');
    if (p.d !== a.d) problems.push('page normItem CHANGED the date ' + a.d + ' -> ' + p.d);
    if (p.k !== a.k) problems.push('page normItem CHANGED the kind ' + a.k + ' -> ' + p.k);
    if (p.n !== a.n) problems.push('page normItem CHANGED the note');
    if (problems.length) { bad++; console.log('  [' + i + '] ' + a.d + ' ' + a.k + ' "' + a.t.slice(0,50) + '" -> ' + problems.join('; ')); }
  });
  console.log(bad ? bad + ' item(s) with a problem' : 'all ' + items.length + ' items clean through BOTH validators');
  const days = {};
  items.forEach(a => days[a.d] = (days[a.d]||0)+1);
  console.log('dates:', JSON.stringify(days));
  console.log('invented times:', items.filter(a=>a.s).map(a=>a.t.slice(0,28)+'@'+a.s).join(' | ') || '(none)');
}

/* --- adversarial: what the far end does with a reply that is NOT the agreed shape --- */
console.log('\n================ adversarial shapes ================');
const nasty = [
  ['wrong root key',   '{"itinerary":[{"d":"2026-04-13","k":"food","t":"Lunch"}]}'],
  ['date outside trip','{"items":[{"d":"2027-01-01","k":"food","t":"Lunch far in the future"}]}'],
  ['no title',         '{"items":[{"d":"2026-04-13","k":"food","t":""}]}'],
  ['html in title',    '{"items":[{"d":"2026-04-13","k":"food","t":"<img src=x onerror=alert(1)>"}]}'],
  ['junk kind',        '{"items":[{"d":"2026-04-13","k":"nuclear","t":"Odd"}]}'],
  ['prose not json',   'Sure! Here is your plan for Kyoto...'],
  ['150 items',        JSON.stringify({items:Array.from({length:150},(_,i)=>({d:'2026-04-13',k:'food',t:'Item '+i}))})],
];
for (const [label, raw] of nasty) {
  const g2 = sandbox.extractItems_(raw, '2026-04-13', '2026-04-17'); const got = g2.items;
  console.log(label.padEnd(20) + ' -> ' + got.length + ' kept, ' + g2.dropped + ' dropped' +
    (got.length ? '  first: ' + JSON.stringify({d:got[0].d,k:got[0].k,t:got[0].t.slice(0,45)}) : ''));
}
