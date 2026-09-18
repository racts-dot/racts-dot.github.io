# -*- coding: utf-8 -*-
"""Puts the 18 Sep 2026 AFR into the Desk's news section.

Her ruling, 18 Sep 2026: the daily paper goes into the Desk rather than its own
artifact. This writes ONLY sections['news'] in the Desk feed and bumps rev, so
it never touches desk/index.html - another chat is editing that file tonight.

Grouped, not one card per story: the paper had 64 stories and the Desk digest
is for reading on a phone. Numbers are spelled out, matching the section's
existing house style.
"""
import io, json, time

FEED = 'desk/feed/09814a7934ef1d3e.json'

NEWS = {
    "date": "2026-09-18",
    "title": "AFR — Friday 18 September 2026",
    "caveat": "Five days missing before this one. The six a.m. job did not run at all on the "
              "fourteenth through the seventeenth, so nothing was collected on those days and "
              "those editions are gone. This one is the catch-up: sixty-four stories from the "
              "seventeenth and eighteenth, grouped below.",
    "stories": [
        {
            "h": "The one to read twice: the Reserve Bank has stopped protecting jobs and inflation at once",
            "p": "Three separate stories point the same way. A rate decision lands at the end of the month, "
                 "and the language changed this week.",
            "pts": [
                "The governor put households and the government on notice that beating inflation now comes "
                "first, even if unemployment rises.",
                "She said the risks the bank had warned would trigger another rise have actually happened.",
                "The US Federal Reserve is lifting rates too, so the two are moving in step and cheaper "
                "borrowing is a long way off.",
                "What it means for you: households cut small optional buys first, and weeks later rather than "
                "the same day. Expect quiet patches, and do not read one as the product failing."
            ]
        },
        {
            "h": "The government dropped its plan to let AI companies train on copyrighted work for free",
            "p": "This is the rule that decides whether work someone made can be fed into AI training without "
                 "payment. It moved this week toward the people who made the work.",
            "pts": [
                "Australia's media and creative industries met the Attorney-General's Department for ninety "
                "minutes on Tuesday about how AI companies should pay for content they have used.",
                "The proposal that would have given them free rein appears to have been abandoned.",
                "Separately, staff at the makers of Claude and ChatGPT are pushing back on their own bosses' "
                "plan to slow AI down, and on letting outsiders assess their work.",
                "What it means for you: worth following, because it sets what anyone selling creative work can "
                "expect to be asked, or paid."
            ]
        },
        {
            "h": "Fourteen per cent of property listings now use AI-touched photos, and buyers arrive disappointed",
            "p": "The practice is most common at the cheaper end, where first home buyers are looking. It is the "
                 "same trap as any picture that flatters what actually arrives.",
            "pts": [
                "One Melbourne buyers' agent says the homes are always a let-down in person after the photos.",
                "A Paddington mansion sold for twenty-three and a half million after a campaign built to spread; "
                "the agent said standing out matters more than ever while the market is cooling.",
                "What it means for you: an image that oversells buys one sale and a bad review. Every preview "
                "should show what the buyer actually receives, unimproved."
            ]
        },
        {
            "h": "A fifty billion dollar float will dominate the market for the next five weeks",
            "p": "Firmus rents out high-end chips for artificial intelligence and joins the share market at the "
                 "end of October. It is the biggest float in a generation.",
            "pts": [
                "Its deal with Nvidia would need more than ten times the power of every data centre currently "
                "being built across Australia and Asia.",
                "A columnist argues the risk cuts both ways: either AI does not live up to the promise, or it "
                "works so well it causes real damage.",
                "What it means for you: a supplier that size can move the price and availability of AI tools "
                "underneath everyone using them. Keep the important steps written down as steps, so one "
                "company's price rise is an annoyance rather than a stoppage."
            ]
        },
        {
            "h": "Record copper prices are handing shareholders about forty billion dollars",
            "p": "Two-thirds of listed companies lifted their dividends at the August results.",
            "pts": [
                "Roughly twenty-eight billion reaches owners during September, and another ten billion the "
                "month after.",
                "It ends a three-year run of shrinking payouts, and only two years on record have paid more.",
                "Money landing in household accounts is the one thing pulling the other way against rate rises."
            ]
        },
        {
            "h": "A doctor says nearly everyone should throw their supplements away",
            "p": "His argument is about evidence, not health fads, and it is the cleanest version of a lesson "
                 "worth borrowing.",
            "pts": [
                "Clinical trials show healthy adults taking vitamins and collagen are mostly wasting money.",
                "He says a worldwide wellness business worth six point eight trillion dollars runs on claims "
                "the evidence does not support.",
                "What it means for you: only print a number or a promise you could defend if a buyer asked "
                "where it came from. A whole industry got that big on claims nobody checked."
            ]
        },
        {
            "h": "A comedian's wine tasting show is now performed in a hundred countries",
            "p": "Six glasses in front of every person, and the whole tasting run as stand-up comedy.",
            "pts": [
                "It started as an Australian comedy-circuit act and became a global hit.",
                "What it means for you: a dry subject sold as a format people enjoy travels much further than "
                "the same information sold as instruction. That is a packaging decision, and it is available "
                "to anyone making learning material."
            ]
        },
        {
            "h": "Also in the paper",
            "p": "Shorter items worth knowing, without needing the detail.",
            "pts": [
                "One Nation wants seven hundred and fifty thousand fewer people here on temporary visas; "
                "Labor's plan is smaller and more technical.",
                "Macquarie froze two funds while it runs fresh checks, as regulators watch the two hundred "
                "billion dollar private credit market.",
                "Bendigo Bank is cutting up to a hundred and forty jobs and sending the work overseas.",
                "Building company failures hit a record in August after the Bathla collapse.",
                "A takeover fight over a tutoring company is still running, which says education products "
                "still attract real investor money."
            ]
        }
    ]
}


def main():
    doc = json.load(io.open(FEED, encoding='utf-8'))
    before = doc['sections'].get('news', {}).get('date')
    doc['sections']['news'] = NEWS
    doc['rev'] = int(time.time())
    doc['made'] = '2026-09-18'
    if 'news' not in doc.get('has', []):
        doc.setdefault('has', []).append('news')
    io.open(FEED, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(doc, ensure_ascii=False, separators=(',', ':')))
    print('news section: %s -> %s' % (before, NEWS['date']))
    print('rev bumped to %d, %d grouped stories' % (doc['rev'], len(NEWS['stories'])))


if __name__ == '__main__':
    main()
