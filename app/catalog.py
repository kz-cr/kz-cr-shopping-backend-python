"""The gallery catalogue.

This module is the single source of truth for the 30 pieces the demo ships
with. Both the database seeder (``app.seed``) and the image vendoring script
(``scripts/fetch_images.py``) read from ``CATALOG``.

Photographs come from the public https://github.com/yavuzceliker/sample-images
repository (``docs/image-<n>.jpg``); ``source_image`` records which one. Titles,
descriptions, artist names, years and media are written for this demo and are
fictional.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# Prices are drawn once from this seed so that every rebuild of the database
# produces the same catalogue.
PRICE_SEED = 20240501
PRICE_MIN_CENTS = 100_00
PRICE_MAX_CENTS = 500_00
PRICE_STEP_CENTS = 50


@dataclass(frozen=True)
class CatalogEntry:
    """One piece of art, before it reaches the database."""

    slug: str
    title: str
    description: str
    artist: str
    year: int
    medium: str
    category: str
    source_image: int
    alt_text: str


CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        slug="blue-sedan-wrapped",
        title="Blue Sedan, Wrapped",
        description=(
            "A die-cast sedan parked on the ribbon of a red gift box while the "
            "tree lights behind it dissolve into gold. The piece plays the "
            "sharpness of the little car against a field of pure bokeh, and it "
            "is that contrast, rather than the season, that carries the image."
        ),
        artist="Marta Vreeland",
        year=2019,
        medium="Archival pigment print",
        category="Still Life",
        source_image=1,
        alt_text="A small blue toy car on a red gift box in front of warm Christmas bokeh",
    ),
    CatalogEntry(
        slug="citrus-in-a-wire-basket",
        title="Citrus in a Wire Basket",
        description=(
            "Oranges, limes and a halved lemon crowd a chrome fryer basket set "
            "on green gingham. The cut lemon is the only broken surface in the "
            "frame, and the photographer lets it hold every bit of the light "
            "the matte peels refuse to return."
        ),
        artist="Iris Oyelaran",
        year=2021,
        medium="Archival pigment print",
        category="Still Life",
        source_image=34,
        alt_text="Oranges, limes and a cut lemon in a wire basket on a green checked cloth",
    ),
    CatalogEntry(
        slug="ginger-root-study",
        title="Ginger Root Study",
        description=(
            "Knuckled ginger and two peppercorns on a scarred worktable, warmed "
            "to a single amber key. Stripped of colour the root reads as "
            "something closer to driftwood, all joint and gesture, and the "
            "shallow focus keeps only its nearest arm truly legible."
        ),
        artist="Halvard Enns",
        year=2018,
        medium="Toned gelatin silver print",
        category="Still Life",
        source_image=67,
        alt_text="Sepia-toned close-up of ginger root and peppercorns on a wooden board",
    ),
    CatalogEntry(
        slug="lone-grazer",
        title="Lone Grazer",
        description=(
            "A pale horse grazes at the low edge of a ploughed field while a "
            "dark treeline presses down from above. In monochrome the field "
            "becomes a set of long grey bands, and the horse is the single "
            "bright interruption in all of them."
        ),
        artist="Signe Aalto",
        year=2017,
        medium="Gelatin silver print",
        category="Landscape",
        source_image=100,
        alt_text="Black and white photograph of a pale horse grazing alone in a large field",
    ),
    CatalogEntry(
        slug="billy-buttons",
        title="Billy Buttons",
        description=(
            "A stand of craspedia photographed tight enough that the stems "
            "vanish and only the drumstick heads remain, each one a textured "
            "yellow sphere floating against near-black. Repetition does the "
            "work here; no single bloom is allowed to become the subject."
        ),
        artist="Prisha Nandakumar",
        year=2022,
        medium="Archival pigment print",
        category="Botanical",
        source_image=133,
        alt_text="Cluster of round yellow craspedia flower heads against a dark background",
    ),
    CatalogEntry(
        slug="pullout-above-the-valley",
        title="Pullout Above the Valley",
        description=(
            "A traveller sits on the roof of a parked estate car looking across "
            "a valley of turning birch toward a snow-topped ridge. The figure "
            "is small and off-centre and entirely still, which is what lets the "
            "autumn hillside read as the larger event."
        ),
        artist="Emre Dalkıran",
        year=2020,
        medium="Archival pigment print",
        category="Landscape",
        source_image=166,
        alt_text="A person sitting on a car roof overlooking an autumn valley and snowy peaks",
    ),
    CatalogEntry(
        slug="the-massif-and-the-shore",
        title="The Massif and the Shore",
        description=(
            "A grey massif rises straight out of a shoreline where walkers have "
            "been reduced to marks a few pixels tall. Printed in warm sepia, the "
            "rock and the water are pulled into the same tonal family, so scale "
            "has to be inferred from the figures alone."
        ),
        artist="Johanna Bretz",
        year=2016,
        medium="Toned gelatin silver print",
        category="Landscape",
        source_image=199,
        alt_text="Sepia photograph of a steep mountain massif above a lake shore with tiny walkers",
    ),
    CatalogEntry(
        slug="still-water-bare-trees",
        title="Still Water, Bare Trees",
        description=(
            "A flooded margin of winter woodland, so windless that the bare "
            "canopy and its reflection meet in an almost unbroken seam. The "
            "sepia toning flattens the two halves toward each other until the "
            "waterline is the only thing telling you which way is up."
        ),
        artist="Johanna Bretz",
        year=2016,
        medium="Toned gelatin silver print",
        category="Landscape",
        source_image=232,
        alt_text="Sepia photograph of bare winter trees mirrored in still water",
    ),
    CatalogEntry(
        slug="swan-warm-light",
        title="Swan, Warm Light",
        description=(
            "A mute swan turned three-quarters away, wings half-raised, on water "
            "rendered as a single warm sheet. The toning removes every cue that "
            "would date the picture, leaving a study of one curve repeated in "
            "the neck, the wing and the reflection."
        ),
        artist="Colm Ferriter",
        year=2015,
        medium="Toned gelatin silver print",
        category="Wildlife",
        source_image=265,
        alt_text="Sepia-toned mute swan on calm water with raised wings",
    ),
    CatalogEntry(
        slug="swan-through-willow",
        title="Swan Through Willow",
        description=(
            "Shot from the bank through a screen of yellowing willow, so the "
            "leaves fall out of focus into gold ribbons across the foreground. "
            "The swan sits in the one clear gap in that screen, small, lit, and "
            "entirely unaware of being framed."
        ),
        artist="Colm Ferriter",
        year=2019,
        medium="Archival pigment print",
        category="Wildlife",
        source_image=298,
        alt_text="A white swan on dark water seen through blurred golden willow leaves",
    ),
    CatalogEntry(
        slug="elephant-crossing-the-scrub",
        title="Elephant Crossing the Scrub",
        description=(
            "An elephant walks pale dust through low thorn scrub, ears out, "
            "tusks catching the only hard light in the frame. Warm toning "
            "collapses animal and ground into a single palette, which makes the "
            "silhouette rather than the detail do the carrying."
        ),
        artist="Naledi Mothibi",
        year=2018,
        medium="Toned gelatin silver print",
        category="Wildlife",
        source_image=331,
        alt_text="Sepia photograph of an elephant walking through dry scrubland",
    ),
    CatalogEntry(
        slug="alpine-lake-mirror",
        title="Alpine Lake Mirror",
        description=(
            "A high lake holds an unbroken reflection of the snow ridge above "
            "it, with a stone path entering from the lower left to give the eye "
            "somewhere to start. The blues are left cold and unwarmed, and the "
            "picture is better for the restraint."
        ),
        artist="Lorenz Habegger",
        year=2021,
        medium="Archival pigment print",
        category="Landscape",
        source_image=364,
        alt_text="Snow-capped peaks reflected in a still blue alpine lake",
    ),
    CatalogEntry(
        slug="reclining-in-the-dry-grass",
        title="Reclining in the Dry Grass",
        description=(
            "A woman lies back in a field of bleached grass, one arm shading her "
            "eyes, knitted cap pushed high. Everything in the frame — hair, "
            "cardigan, stubble, ground — has been tuned to the same straw tone, "
            "so the pose is all that separates her from the field."
        ),
        artist="Tove Lindqvist",
        year=2020,
        medium="Archival pigment print",
        category="Portrait",
        source_image=397,
        alt_text="A woman reclining in a field of dry golden grass, shading her eyes",
    ),
    CatalogEntry(
        slug="white-kitchen-morning",
        title="White Kitchen, Morning",
        description=(
            "An interior held almost entirely in white: shaker cabinets, an "
            "apron sink, open walnut shelving, and a herringbone floor that "
            "supplies the room's only pattern. Brass fittings and the green "
            "outside the window are the sole permitted colour."
        ),
        artist="Delphine Aubert",
        year=2022,
        medium="Archival pigment print",
        category="Architecture",
        source_image=430,
        alt_text="A bright white kitchen with brass fixtures, open shelving and a patterned tile floor",
    ),
    CatalogEntry(
        slug="frost-road",
        title="Frost Road",
        description=(
            "A farm track runs dead centre into a snowfield, with frosted trees "
            "and a bank of fog closing off the far end. It is a picture about "
            "one line and three greys, and it does not ask for anything else."
        ),
        artist="Signe Aalto",
        year=2017,
        medium="Gelatin silver print",
        category="Landscape",
        source_image=463,
        alt_text="Black and white snowy field with a track leading toward frosted trees and fog",
    ),
    CatalogEntry(
        slug="peacock-in-full-display",
        title="Peacock in Full Display",
        description=(
            "The train fills the frame edge to edge, every ocellus a ring of "
            "bronze and green, with the bird's cobalt neck and crest set hard "
            "against it. Printed at scale the eyespots stop reading as feathers "
            "and start reading as pattern."
        ),
        artist="Prisha Nandakumar",
        year=2019,
        medium="Archival pigment print",
        category="Wildlife",
        source_image=496,
        alt_text="A peacock with its iridescent tail fanned fully open",
    ),
    CatalogEntry(
        slug="tulips-in-monochrome",
        title="Tulips in Monochrome",
        description=(
            "Backlit tulips photographed in black and white, which strips them "
            "of the one thing tulips are usually bought for. What is left is "
            "the translucency of the petals and the hard dark blades of the "
            "leaves beneath them."
        ),
        artist="Wies van Dooren",
        year=2018,
        medium="Gelatin silver print",
        category="Botanical",
        source_image=529,
        alt_text="Black and white photograph of backlit tulip blooms",
    ),
    CatalogEntry(
        slug="goslings",
        title="Goslings",
        description=(
            "Two goslings a few days old sit in cropped grass while an adult "
            "passes behind them, out of focus and cut by the frame. Shot from "
            "ground level with a long lens, so the grass in front is as soft as "
            "the parent behind."
        ),
        artist="Wies van Dooren",
        year=2021,
        medium="Gelatin silver print",
        category="Wildlife",
        source_image=562,
        alt_text="Black and white photograph of two young goslings sitting in grass",
    ),
    CatalogEntry(
        slug="bengal-at-rest",
        title="Bengal at Rest",
        description=(
            "A bengal cat sits folded and alert while a second sprawls behind "
            "it, rosettes running together where the two coats meet. The warm "
            "single-tone print turns the markings into something closer to "
            "watermarked paper than fur."
        ),
        artist="Halvard Enns",
        year=2020,
        medium="Toned gelatin silver print",
        category="Wildlife",
        source_image=595,
        alt_text="Sepia-toned photograph of a spotted bengal cat sitting with another behind it",
    ),
    CatalogEntry(
        slug="limestone-stacks-at-low-tide",
        title="Limestone Stacks at Low Tide",
        description=(
            "Two limestone stacks stand off a wide ochre beach under a flat "
            "bank of cloud. A handful of walkers near the waterline are the only "
            "scale given, and they are given deliberately late — the eye finds "
            "the rock first and the people second."
        ),
        artist="Bridget Callow",
        year=2019,
        medium="Archival pigment print",
        category="Landscape",
        source_image=628,
        alt_text="Coastal limestone stacks on a wide sandy beach with small figures near the water",
    ),
    CatalogEntry(
        slug="hare-among-thistles",
        title="Hare Among Thistles",
        description=(
            "A brown hare sits upright in low evening sun beside a stand of "
            "thistle, ears raised, caught mid-assessment. The meadow behind is "
            "thrown to a uniform green, which leaves the backlit rim of the "
            "animal as the sharpest edge in the picture."
        ),
        artist="Bridget Callow",
        year=2022,
        medium="Archival pigment print",
        category="Wildlife",
        source_image=661,
        alt_text="A brown hare sitting upright in green grass beside thistle plants",
    ),
    CatalogEntry(
        slug="spires-above-the-treeline",
        title="Spires Above the Treeline",
        description=(
            "A volcanic plug breaks out of a forested ridge in a run of broken "
            "spires. Warm toning and a hazy sky pull the whole range toward one "
            "value, so the summit registers as texture against smoke rather "
            "than rock against air."
        ),
        artist="Lorenz Habegger",
        year=2016,
        medium="Toned gelatin silver print",
        category="Landscape",
        source_image=694,
        alt_text="Sepia photograph of a jagged rocky peak rising above forested ridges",
    ),
    CatalogEntry(
        slug="fog-in-the-valley",
        title="Fog in the Valley",
        description=(
            "Cloud sits in a valley at the exact height of the spruce tops, so "
            "the forest appears to be standing in surf. Beyond it the far ridges "
            "step back into progressively paler greys until they give out "
            "altogether."
        ),
        artist="Lorenz Habegger",
        year=2018,
        medium="Gelatin silver print",
        category="Landscape",
        source_image=727,
        alt_text="Black and white photograph of fog filling a valley among conifer forest",
    ),
    CatalogEntry(
        slug="ridgelines-at-dusk",
        title="Ridgelines at Dusk",
        description=(
            "Five or six ridges recede into haze beneath a sky graded from "
            "orange to deep blue, with a single planet already out above the "
            "horizon. No foreground detail is offered at all; the picture is "
            "built entirely from stacked silhouettes."
        ),
        artist="Seo-yeon Baek",
        year=2021,
        medium="Archival pigment print",
        category="Landscape",
        source_image=760,
        alt_text="Layered mountain ridges silhouetted against an orange and blue dusk sky",
    ),
    CatalogEntry(
        slug="under-the-umbrella",
        title="Under the Umbrella",
        description=(
            "A couple stand in tall pampas grass sharing a clear umbrella, "
            "mid-conversation rather than posed. Black and white removes the "
            "obvious warmth of the setting and leaves the exchange between them "
            "as the only thing the frame is actually about."
        ),
        artist="Seo-yeon Baek",
        year=2020,
        medium="Gelatin silver print",
        category="Portrait",
        source_image=793,
        alt_text="Black and white photograph of a couple under a clear umbrella in tall pampas grass",
    ),
    CatalogEntry(
        slug="daisy-close",
        title="Daisy, Close",
        description=(
            "A daisy photographed close enough that the disc florets become a "
            "granular dome and the petals leave the plane of focus within "
            "millimetres. The warm single tone keeps it from reading as a "
            "botanical record and pushes it toward pure form."
        ),
        artist="Wies van Dooren",
        year=2017,
        medium="Toned gelatin silver print",
        category="Botanical",
        source_image=826,
        alt_text="Sepia-toned macro photograph of the centre of a daisy",
    ),
    CatalogEntry(
        slug="raspberry-smoothie-with-mint",
        title="Raspberry Smoothie with Mint",
        description=(
            "A cut-glass tumbler of raspberry smoothie, topped with a sprig of "
            "mint, on a crumpled rose linen cloth with loose berries scattered "
            "behind. The mint is the only cool note allowed into an otherwise "
            "entirely pink frame."
        ),
        artist="Iris Oyelaran",
        year=2022,
        medium="Archival pigment print",
        category="Still Life",
        source_image=859,
        alt_text="A glass of pink raspberry smoothie garnished with mint on a pink cloth",
    ),
    CatalogEntry(
        slug="alloy-in-low-key",
        title="Alloy in Low Key",
        description=(
            "A single lit wheel and the arch above it, with the rest of the car "
            "and the rest of the room surrendered to black. What survives is a "
            "five-spoke star and one long highlight along the wing — an abstract "
            "assembled out of the parts the light agreed to keep."
        ),
        artist="Marta Vreeland",
        year=2018,
        medium="Gelatin silver print",
        category="Abstract",
        source_image=892,
        alt_text="Low-key black and white photograph of a car's alloy wheel and wheel arch",
    ),
    CatalogEntry(
        slug="scarlet-beetle",
        title="Scarlet Beetle",
        description=(
            "A lily beetle grips the edge of a blade of grass, red lacquer "
            "against a field of nothing but green. The background is blurred "
            "past the point of description, which is what allows an insect a "
            "centimetre long to hold an entire frame."
        ),
        artist="Prisha Nandakumar",
        year=2021,
        medium="Archival pigment print",
        category="Wildlife",
        source_image=925,
        alt_text="Macro photograph of a red lily beetle on a green blade of grass",
    ),
    CatalogEntry(
        slug="glass-facade-fractured-sky",
        title="Glass Facade, Fractured Sky",
        description=(
            "An angled glass curtain wall shot from the pavement, each faceted "
            "panel returning a different piece of the sky above it. Converted "
            "to black and white, the building stops behaving like a building "
            "and becomes a lattice of broken reflections."
        ),
        artist="Delphine Aubert",
        year=2019,
        medium="Gelatin silver print",
        category="Architecture",
        source_image=958,
        alt_text="Black and white photograph of an angular glass building facade reflecting the sky",
    ),
)

CATEGORIES: tuple[str, ...] = tuple(sorted({entry.category for entry in CATALOG}))


def assign_prices() -> dict[str, int]:
    """Deterministically price every entry between $100 and $500.

    Returns a mapping of ``slug`` to price in cents. Seeding the generator
    keeps the catalogue stable across rebuilds, so a client that hard-codes a
    price in a test does not break the next time the database is dropped.
    """
    rng = random.Random(PRICE_SEED)
    return {
        entry.slug: rng.randrange(
            PRICE_MIN_CENTS, PRICE_MAX_CENTS + 1, PRICE_STEP_CENTS
        )
        for entry in CATALOG
    }


def source_url(source_image: int) -> str:
    """Upstream URL for one of the sample photographs."""
    return (
        "https://raw.githubusercontent.com/yavuzceliker/sample-images/main/"
        f"docs/image-{source_image}.jpg"
    )
