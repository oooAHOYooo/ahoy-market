"""
One-time seed script for the poems table on Render.
Run from the repo root after `alembic upgrade head`:

    python scripts/seed_poems.py

Safe to re-run — skips any poem_id that already exists.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db import get_session
from models import Poem
from datetime import datetime

POEMS = [
    {
        "poem_id": "the-apple-tree",
        "title": "The Apple Tree",
        "poet_name": "Craig Martin",
        "poet_slug": "craig-martin",
        "note": "(The Apple of My Mother's Eye)",
        "is_published": True,
        "position": 0,
        "published_at": datetime(2026, 5, 29),
        "body_text": """\
The orphan of a Victorian orchard,
her sister died when I was a boy.
Gnarled trunk, cloaked with ivy—
a slow shadow creeping higher.

Most of the apples fall
spoiled before they hit the ground.
Crow waits in the branches,
watching for worm or fruit.

This year,
there are two—
blushed and smooth,
resting in my hand.

When I was young,
I would hurl unripe sheddings at the neighbor,
then climb to box the best
for harvest festival.

Her treasures were sweet.
I stood on a chair, fork in my mouth,
piercing the bobbing fruit
in a steel pail below.

Now, she is tired,
cankered, and yet she stands,
roots deep enough—
hair thinner but proud.

She blossoms each year,
but fruits every two.
This year,
two apples were passed to me,
as I left her to return home.""",
    },
    {
        "poem_id": "the-words-in-my-head",
        "title": "The words in my head",
        "poet_name": "Kyle Middleton",
        "poet_slug": "kyle-middleton",
        "note": "Read at Poets & Friends #9",
        "is_published": True,
        "position": 1,
        "published_at": datetime(2026, 3, 26),
        "body_text": """\
The words in my head
often they're never said
often they're forgotten
the light goes out before it's even acknowledged

but when one goes out another sparks
brightening my mind for good and for bad
sometimes there's thoughts I wish I never had
other times I'm excited when they come

a single thought can change despair into hope
doubt into belief
it can your change whole outlook on life
It can change the direction you go in

I choose to think positively
I choose to have hope
Inevitably negative thoughts come back
It's my job to say nope

For the longer I dwell in dread
The longer I am succumb by the words never said""",
    },
    {
        "poem_id": "where-do-your-best-thoughts-come-from",
        "title": "Where do your best thoughts come from",
        "poet_name": "Kyle Middleton",
        "poet_slug": "kyle-middleton",
        "note": "Read at Poets & Friends #10",
        "is_published": True,
        "position": 2,
        "published_at": datetime(2026, 4, 30),
        "body_text": """\
Where do your best thoughts come from

What constitutes a thought as a best thought?

How many of these thoughts do we have?

Is there a limit to how many thoughts considered a best thought we can have?

These are just some of the thoughts I currently have

It's fun to ponder about these random ideas sometimes

When small talk is the norm, such as "how's the weather" to questions about traffic and pop culture...

I'll think, sometimes the best conversations I have are the ones within myself

It's funny how a simple walk can spark some of your best thoughts of your day

It's funny when you're on your phone too much it can cloud those thoughts making them gray

It's interesting that limiting your information will give you ideas you'll want to relay

When taking in too much information will spin those ideas into disarray""",
    },
    {
        "poem_id": "cellulose-ether",
        "title": "Cellulose Ether",
        "poet_name": "Claire Cooper",
        "poet_slug": "claire-cooper",
        "note": "",
        "is_published": True,
        "position": 3,
        "published_at": datetime(2026, 6, 4),
        "body_text": """\
When my grandmother sneezes, bits of her cloud
out like spores. I find her silver mind lining
nests, watch as strands of her unwind
leaving behind bone, sharp, like dark
tea steeped too long. She screams

when my mother takes her car keys,
raging against her disintegration
like the robotic art installation
that endlessly mops its own hydraulic fluid.

My parents sign a letter, promising,
in old age, to be better at releasing control.
I read the pain and hope mixed
into their signatures' ink.

The pain: when their minds dissolve, will this
promise be part of what stays?
The hope: that they will find strength
to hold the dust of their own broken bodies up
in cupped hands, singing as they scatter.""",
    },
    {
        "poem_id": "seance-in-the-corner-stall",
        "title": "Seance in the Corner Stall",
        "poet_name": "Claire Cooper",
        "poet_slug": "claire-cooper",
        "note": "",
        "is_published": True,
        "position": 4,
        "published_at": datetime(2026, 6, 4),
        "body_text": """\
Jamie was here crawls
over cracked tile. It's nothing
bleach can't rinse. I've been picking
at the wall, at my dark-mooned nails,
at anything but my own thoughts. If I could pierce
each one, if I could knot them in a line
and sink their shapes without wincing, my head
would ring clear, a glass bell. Instead,

I bury my ghosts in grout,
but they always come back. Their tell
is the tolling. Maybe Kylie and Samuel
can keep my vigils and the illegible
sharpie scrawl can track in gold
runes across the dust-velveted cinderblock.
Maybe I can lay my shame to rest
with a lullaby of call me, Sarah
and ignore the mold packing each inhale.

I track the rust dripping down
the wall, then stand, then pick
the grout clean, then pick
the cleanest sink. The janitor brings
rubbing alcohol. "Damn those
teens," he says. "I clean the stall
each week. The ink always
comes back.\"""",
    },
    {
        "poem_id": "spaghetti-with-syrup",
        "title": "Spaghetti with Syrup",
        "poet_name": "Claire Cooper",
        "poet_slug": "claire-cooper",
        "note": "",
        "is_published": True,
        "position": 5,
        "published_at": datetime(2026, 6, 4),
        "body_text": """\
We toss our marbled memories in a game of catch,
knocking off their edges, swirling their patterns like tops,
licking their sauce off our fingers.

I remember the time we ate spaghetti with syrup
like Buddy the Elf. It was a little nauseating
and a little too sweet, but still lovely. I wanted it to last.

Once, I found "RIP" written on a sticky note,
left by a dead cockroach in a stairwell.
I don't know who wrote it, but I felt like they left
it for me to find.

I want my dental hygienist to be proud of me,
but she says I don't floss enough. I think a lot
of people can relate, and I think we all would be friends.

What I'm trying to say is that if I fill you with my stories,
I will know I exist. If you fill me with yours, I promise to narrate
aloud. Our echoes carve furrows in the air—
a little nauseating, a little too sweet, but still lovely.""",
    },
    {
        "poem_id": "on-the-subway-contemplating-death",
        "title": "On the Subway, Contemplating Death",
        "poet_name": "Claire Cooper",
        "poet_slug": "claire-cooper",
        "note": "",
        "is_published": True,
        "position": 6,
        "published_at": datetime(2026, 6, 4),
        "body_text": """\
Some people want to taste eternity.
They brace their bones with iron to withstand
time's music box. There is no rewind key,
and years erode from falling hourglass sand.

Some people look no further than the day
ahead. They're young; why should they fear their death?
It surely doesn't wait for them with clay-
orange grave dust clinging to its cloying breath.

But I can tell my sinews will unwind
like puppet strings cut loose from their supports.
So, let my words be bold and underlined
as long as my pulse beats. I swear to force
my muscles to obey my fading mind
until the mushrooms take root in my corpse.""",
    },
    {
        "poem_id": "the-train-of-time",
        "title": "The train of time",
        "poet_name": "Samuel Chen",
        "poet_slug": "samuel-chen",
        "note": "",
        "is_published": True,
        "position": 7,
        "published_at": datetime(2026, 6, 5),
        "body_text": """\
We are all on a train called time, we depart from our first cry.
the train of time takes us around our life.

How often do you also felt the same that this train goes abit too fast. When we are satisfied, when there are laughter and warmth and friends.
when we are doing just fine.

But also, how often do we felt that the train almost stopped. When we are in pain, in fire, when we are waiting in darkness, waiting for sunrise.
 we wish we can just cut in line,

The train of time, you bring us new memories, to new loved ones. You also bring us to new pain, new feelings, new despair, new hope. You keep moving, on this journey there is no stop sign.

Sometimes we ask, can you just slow down a bit. When you pass by those places called joy, or laughter. When there are food and wine and bright sun shine.
No, you never. Though we kept looking through your back window, just like a child looking at a passing wind. Those moments say farewell to us, and some come back to us again, in other forms. like the rise and fall of the ocean tide.

Sometimes we wonder, can you just speed up a bit, just a bit. on those days of sorrow, sickness, in painful suffering when we lie and our tears run dry. No, you never speed up. Till some of us can wait no longer, many wish they had better die. Some left us, but some of us are still painfully hanging in there. we ask why?
Why? Train of time, that the pace is you to decide. We wonder, is the next stop gonna be nice? But come on, you've seen so far, on this train we don't really have a say right?
I don't know how to conclude this poem, but some how it's nice to know that we are on this one train together, side by side. and that there is hope that we'd make sense of all this, in this life. by Poet Samuel Chen""",
    },
]


def main():
    with get_session() as session:
        for data in POEMS:
            existing = session.query(Poem).filter_by(poem_id=data["poem_id"]).first()
            if existing:
                print(f"  skip  {data['poem_id']} (already exists)")
                continue
            p = Poem(
                poem_id=data["poem_id"],
                title=data["title"],
                poet_name=data["poet_name"],
                poet_slug=data.get("poet_slug"),
                body_text=data["body_text"],
                handwriting_image_url=data.get("handwriting_image_url"),
                note=data.get("note"),
                is_published=data.get("is_published", False),
                position=data.get("position", 0),
                published_at=data.get("published_at"),
            )
            session.add(p)
            print(f"  insert {data['poem_id']} — {data['title']} by {data['poet_name']}")
    print("Done.")


if __name__ == "__main__":
    main()
