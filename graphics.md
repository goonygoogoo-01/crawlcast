# CRAWLCAST graphics upgrade

Plan for replacing CRAWLCAST's procedural graphics with ComfyUI images and, where the scene is 3D, Blender meshes. The inventory below was taken from the Godot 4.7.2 export in the v1.0.0 Linux build (`CRAWLCAST.x86_64`, PCK format 4, 104 packed files).

## What the game draws today

The shipped build contains one piece of authored art: `icon.svg`, a 128×128 plum tile with a flat isometric cube, a magenta gem, and a red on-air bar. Godot imported it as `CompressedTexture2D`. Everything else is built in code.

| System | Script in the export | What it draws |
| --- | --- | --- |
| Actor and prop meshes | `scripts/view/figures.gd` | Primitive meshes named `Body`, tinted with hex colors, keyed by a `shape` string |
| Floor and wall materials | `scripts/view/materials.gd` | Flat `floor_a` / `floor_b` / `wall_a` / `wall_b` colors per depth, plus room kinds `safe`, `boss`, `treasure`, `shrine`, `start` |
| Scene assembly, lights, combat FX | `scripts/view/world_view.gd` | `MeshInstance3D` figures, a door `Hinge`, spotlights, elite auras, floating text, projectiles |
| Inventory and skill icons | `scripts/ui/icons.gd` | Procedural `IconTextures` keyed by icon id and skill glyph |
| Icon widget | `scripts/ui/icon_view.gd` | Displays those textures |
| Panels, buttons, type | `scripts/ui/ui_kit.gd` | Dark plum `StyleBox` colors. Fonts: Inter, Noto Sans, DejaVu Sans |
| HUD, title, intake, ending, menus | `scripts/ui/hud.gd`, `title_screen.gd`, `create_screen.gd`, `end_screen.gd`, `menu_panel.gd` | Live bug, bars, hotbar, hall of fame, stamps |
| Screenshot contact sheet | `tools/shots.gd` | Renders the current icon set to `user://shots` |

The camera is a zoomable isometric 3D view (Godot Y-up, mouse wheel zoom, `[` / `]` brightness). Forward+ is the default renderer. Low graphics drops glow, anti-aliasing, and the torch shadow, and renders the 3D view at 75% resolution. New materials should keep a readable silhouette when glow is off.

Gameplay data that the art has to match lives in `data/enemies.json`, `data/items.json`, `data/skills.json`, `data/floors.json`, `data/meta.json`, `data/zonebosses.json`, and `data/announcer.json`. Those files name every creature, item, skill, background, companion, mutation, rival, and sponsor. They do not contain image paths. Colors and `shape` / `icon` / `glyph` fields are the hooks.

Three floors, one tint each:

| Depth | Name | Theme | Tint | Boss |
| --- | --- | --- | --- | --- |
| 1 | Sublevel One | The Dead Mall | `#000000` | Brunhold Oxgrind, Sector Warden |
| 2 | Sublevel Two | The Studio Backlot | `#3a2a10` | Grukka Rivetjaw, Demolition Foreman |
| 3 | Sublevel Three | The Penthouse Pit | `#2a1040` | Vexa Glitterqueen, Ratings Diva |

Room set pieces the generator already places: Contestant Intake (start), The Green Room (safe), Prize Vault and Sponsor Storage (treasure), Chapel of Maybe (shrine), boss lairs, plus the named rooms in `floors.json`.

## How to generate

Paste the **Global style prompt**, a blank line, then the asset's **Prompt** into ComfyUI's positive prompt. Use the **Negative prompt** on the negative node.

This repo's ComfyUI connection is an SSE bridge (`.cursor/mcp.json`). It queues a workflow JSON. Put the combined prompt in that workflow's positive text node. Checkpoint choice is local: Flux or SDXL for icons and key art, a tiling-capable SDXL pass for floors and walls, a character-sheet pass for actors.

Generate in this order so later sheets can use the contestant as a scale reference:

1. App icon, wordmark, title key art.
2. Contestant base sheet, then the nine backgrounds.
3. Enemy and boss sheets, props, then Blender meshes.
4. Icons, skill glyphs, unique items, zone-boss drops.
5. Floor and wall PBR sets.
6. VFX flipbooks and UI chrome.

After each batch, shrink a copy to 64×64 and check that the silhouette still reads. CRAWLCAST is played zoomed out.

## Global style prompt

```
Late-night intergalactic reality show filmed inside a condemned shopping mall. Practical objects with cheap sci-fi bolted on: fluorescent grime, scuffed plastic, stained carpet, gaffer tape, sponsor stickers, studio makeup, duct-taped props. Palette anchors are plum shadow #140c1e, hot magenta #ff4fd8, sponsor gold #ffd23f, camera cyan #5ce1e6, and danger red #ff3b3b. Satirical, worn, and readable at a glance. Even product lighting, full subject in frame, no motion blur, no watermark, no border, no caption.
```

## Negative prompt

```
gore, viscera, celebrity face, real-world brand logos, watermark, signature, blurry, extra limbs, extra fingers, chibi, pixar, anime, high-fantasy castle, pure white cyclorama, muddy low contrast, cropped subject, unreadable silhouette
```

Icons and UI add: `isometric environment, scenery, multiple objects`. Actor sheets add: `text, name label`. Tileables add: `seam, unique hero object in the center, text`.

## Shared output specs

**Icon.** 1024×1024 generation, export 256×256 PNG with straight alpha. One object, three-quarter view as if the camera sits up and to the south-east, subject filling about 80% of the frame. Flat enough to read on a hotbar.

**UI chrome.** 9-slice friendly. Generate at 1024, export the slice named in the entry. Keep the center empty of detail so text can sit on it.

**PBR tile.** 1024×1024 seamless. Three files: `_albedo.png` (sRGB), `_normal.png` (OpenGL, linear), `_roughness.png` (linear, white = rough). Average color should stay close to the hex listed, because the game still tints room types.

**Actor sheet (ComfyUI, before Blender).** One image, neutral mid-gray background, full body, front and three-quarter views side by side, even lighting, feet on a shared ground line, no cast shadow blob. Humanoids about the same height as the contestant sheet. The in-game `size` value is a scale on that base, applied by code, so the mesh itself is authored at size 1.

**VFX.** 8-frame horizontal strip, 256×256 per frame, straight alpha, loopable unless the entry says one-shot.

## Blender specs

Use Blender only for assets marked **Actor**, **Prop**, or **Pickup**. Icons, tileables, UI, portraits, and flipbooks stop at ComfyUI.

**Actor**

- Units: meters. One dungeon tile is 1 meter. Godot is Y-up; the mesh faces −Z.
- Origin on the floor, centered on the tile. Apply scale and rotation.
- Root node named `Body`, matching the node `figures.gd` already looks up.
- Triangle budget: ordinary creatures 1,500–4,000, bosses and the contestant 6,000, small vermin under 2,000.
- Textures packed in the file: 1024 albedo for bosses and the contestant, 512 for everyone else. Albedo sRGB. One material.
- glTF binary (`.glb`). No cameras or lights in the file.
- Idle animation is optional. If present, name it `idle`, 24 fps, one second, looping. The current game does not require a skeleton.
- The gameplay color stays available as a tint. Paint the real materials, and keep a clearly visible area in the entity's hex so elites and backgrounds still read.

**Prop.** Same export rules. Triangle budget 800–2,500. Pivot where the entry says. If the entry names a child node (`Hinge`, `Water`, `Crystal`, `Hole`, `Light`), create that empty or mesh.

**Pickup.** A small prop, under 1 meter tall, origin on the floor, same `Body` root. Model it from the matching icon image pinned in Blender as a reference.

## File layout the game will load

```
res://art/icon/crawlcast_icon.png
res://art/ui/...
res://art/icons/<icon_id>.png
res://art/skills/<glyph>.png
res://art/portraits/<id>.png
res://art/textures/<set>_albedo.png
res://art/textures/<set>_normal.png
res://art/textures/<set>_roughness.png
res://art/decals/<id>.png
res://art/vfx/<id>.png
res://art/models/actors/<shape>.glb
res://art/models/props/<id>.glb
res://art/models/pickups/<id>.glb
res://art/manifest.json
```

`manifest.json` is a flat list of `{ "id", "kind", "path" }` for every file this document names. The activation prompt at the end loads art through that list and falls back to today's procedural draw when a file is absent.

---

## 1. Brand and screens

### `icon` — application icon

- **Replaces:** `icon.svg`
- **Files:** `res://art/icon/crawlcast_icon.png` (1024 and a 128 export)
- **Blender:** none

**Prompt**

```
App icon, 1024 square, of an isometric dungeon tile seen from the game camera. A worn plum cube, faces in #3a3148, #241d30, and #2e263c, sitting on a #140c1e rounded-square field. A faceted hot-magenta gem hovers above the cube. A small red on-air lamp bar caps the cube. Thick shapes, no tiny detail, still readable at 32 pixels. Upgrade of a flat vector icon, with chipped edges and a fluorescent specular on the gem.
```

### `title_key` — title-screen illustration

- **Replaces:** the flat title panel behind the wordmark in `title_screen.gd`
- **Files:** `res://art/ui/title_key.png` (1920×1080)
- **Blender:** none

**Prompt**

```
Wide key art of a fluorescent dead-mall atrium converted into a dungeon set. Escalator to nowhere, wet tile, a single camera drone with a cyan lens, a velvet rope, a cracked fountain, and a distant ON AIR practical light in hot magenta. Tiny contestant in a gray jumpsuit at the bottom center, back to camera, holding a crowbar. Empty of logos and letters. Room for a title across the upper third.
```

### `wordmark` — CRAWLCAST logo

- **Replaces:** the outlined "CRAWLCAST" label on the title screen
- **Files:** `res://art/ui/wordmark.png`
- **Blender:** none

**Prompt**

```
Game logo spelling CRAWLCAST in one line. Custom block letters built from mall signage and studio marquee bulbs. Fill #fff1f6, outline #ff2d6f, a hard drop shadow. Transparent background. Letters only, no tagline, no box.
```

### `on_air` — live bug

- **Replaces:** the HUD "LIVE" chip
- **Files:** `res://art/ui/on_air.png`
- **Blender:** none

**Prompt**

```
Small broadcast bug, transparent background. A red lamp dot and the word LIVE in condensed white letters on a plum bar. Reads at 32 pixels tall.
```

### `panel` — window chrome

- **Replaces:** `PanelContainer` style in `ui_kit.gd` (`#1c1630` family)
- **Files:** `res://art/ui/panel.png` (nine-slice, corners 48 px)
- **Blender:** none

**Prompt**

```
Square UI panel texture, dark plum #1c1630 fill, inner edge lit by a thin magenta-to-gold hairline, outer edge scuffed like a production monitor bezel. Center 60% is flat color with no ornament so body text stays readable. Transparent outside the bezel.
```

### `button` — button face

- **Replaces:** button normal `#1c1630`, hover `#2a2148`, pressed `#3a2c66`
- **Files:** `res://art/ui/button_normal.png`, `button_hover.png`, `button_pressed.png`
- **Blender:** none

**Prompt**

```
Three stacked button faces on one sheet, identical rounded rectangle, transparent outside. Top: plum plastic #1c1630. Middle: same button lifted, rim #7a64c8. Bottom: same button pushed in, fill #3a2c66. No text.
```

### `hotbar_slot` — hotbar cell

- **Replaces:** HUD slots (`slot_`, colors `#15202a` / `#3f7fa0`)
- **Files:** `res://art/ui/hotbar_slot.png`, `res://art/ui/hotbar_slot_selected.png`
- **Blender:** none

**Prompt**

```
Two empty square slots, transparent outside. First is a dark recessed well #15202a with a cyan plastic rim. Second is the same well with a gold #ffd23f selection ring. No numerals.
```

### `bars` — health, focus, experience

- **Replaces:** HUD fill colors for health, focus, and xp
- **Files:** `res://art/ui/bar_hp.png`, `bar_focus.png`, `bar_xp.png`, `bar_track.png`
- **Blender:** none

**Prompt**

```
Four thin horizontal meter textures, transparent outside. A dark track. A health fill running from #c0282d to #ff6b5b. A focus fill in #3b8bff. An experience fill in #ffd23f. Each fill is a simple glossy strip with a 1-pixel highlight, seamless on the X axis.
```

### `end_stamps` — outcome stamps

- **Replaces:** the end-screen words OFF SCRIPT, RENEWED FOR ANOTHER SEASON, CANCELLED
- **Files:** `res://art/ui/stamp_offscript.png`, `stamp_renewed.png`, `stamp_cancelled.png`
- **Blender:** none

**Prompt**

```
Three rubber-stamp graphics, separate files, transparent background, slightly uneven ink. One reads OFF SCRIPT in magenta. One reads RENEWED in gold. One reads CANCELLED in red. Each is rotated a few degrees, as if slammed onto a call sheet.
```

### `rarity_frames` — item rarity

- **Replaces:** rarity colors common `#c9c9c9`, uncommon `#5fd35f`, rare `#4da3ff`, epic `#c05bff`, legendary `#ff9b2f`
- **Files:** `res://art/ui/frame_common.png`, `frame_uncommon.png`, `frame_rare.png`, `frame_epic.png`, `frame_legendary.png`
- **Blender:** none

**Prompt**

```
Five square item frames, one file each, transparent center so the icon shows through. Common is scuffed gray plastic. Uncommon is mall-green. Rare is camera-cyan glass. Epic is magenta stage gel. Legendary is trophy gold with a chipped laurel. Same outer size on every frame.
```

### `tooltip` — item tooltip

- **Replaces:** `TooltipPanel` in `ui_kit.gd`
- **Files:** `res://art/ui/tooltip.png`
- **Blender:** none

**Prompt**

```
Small dark tooltip card, #120e20, thin gold corner screws, transparent outside the card. Center is empty flat color.
```

### `map_pins` — HUD location chips

- **Replaces:** the colored words safe, boss, shaft, chest, shrine, fountain on the HUD
- **Files:** `res://art/ui/pin_safe.png`, `pin_boss.png`, `pin_shaft.png`, `pin_chest.png`, `pin_shrine.png`, `pin_fountain.png`
- **Blender:** none

**Prompt**

```
Six tiny map pins, one file each, transparent background, readable at 24 pixels. Safe: green room door. Boss: red skull-shaped stamp. Shaft: purple hole. Chest: brass box. Shrine: violet crystal. Fountain: cyan water drop. No text.
```

### `portraits_host` — EMCEE-9

- **Replaces:** the announcer name printed as text. The host is EMCEE-9, "your host, your judge and your legally binding narrator."
- **Files:** `res://art/portraits/emcee9.png` (bust, 512 square)
- **Blender:** none

**Prompt**

```
Bust portrait of EMCEE-9, a game-show robot host with a cracked porcelain smile, a magenta bow tie, a dead mall earpiece, and one cyan camera eye. Plum background. Friendly and slightly legally threatening. No text.
```

### `sponsor_logos` — sponsor bugs

Sponsors are named in `announcer.json` and stapled onto memorial plaques. Each logo is a square mark with the sponsor name, used at 64 pixels.

- **Files:** `res://art/ui/sponsor_<id>.png`
- **Blender:** none

| id | Name | Prompt |
| --- | --- | --- |
| `blorbco` | Blorbco Snack Paste | Square sticker logo reading BLORBCO. A squeeze-pouch mascot shaped like a beige blob. Mustard and plum inks, cheap flexographic print. |
| `cryokale` | Cryo-Kale Energy Slurry | Square sticker logo reading CRYO-KALE. An ice-crusted kale leaf inside a can. Cyan and sickly green. |
| `hexagon` | Hexagon Tactical Mattresses | Square stencil logo reading HEXAGON. A mattress shown as a hex bolt. Olive drab. |
| `vorm` | Uncle Vorm's Discount Litigation | Square logo reading UNCLE VORM. A smiling briefcase with a price tag. Navy and gold. |
| `prism` | Prism Deodorant (For Species With Glands) | Square logo reading PRISM. A crystal deodorant stick spraying a rainbow mist. White and magenta. |
| `nebula` | The Glimmering Nebula Timeshare Collective | Square logo reading NEBULA. A tiny moon with a SOLD sign. Purple and gold. |
| `ninemouth` | Nine-Mouth Dental Solutions | Square logo reading NINE-MOUTH. A tooth with too many smiles around it. Clinical teal. |
| `spacevest` | SpaceVest Retirement Pods | Square logo reading SPACEVEST. A coffin-like pod with a smiling sun sticker. Warm gray and gold. |
| `zzt` | Grandma Zzt's Lab-Grown Cookies | Square logo reading GRANDMA ZZT. A cookie growing in a petri dish, tied with a gingham bow. |

---

## 2. Floors, walls, and decals

Depth selects the set: 1 Dead Mall, 2 Studio Backlot, 3 Penthouse Pit. Room kind multiplies a decal on top (`safe`, `boss`, `treasure`, `shrine`, `start`). Blender is not required for these; they are sampled by `materials.gd` as `StandardMaterial3D` albedo, normal, and roughness.

### `floor_mall` / `wall_mall` — Sublevel One, The Dead Mall

- **Match colors:** floor `#4a433c` / `#a09483`, wall `#35303a` / `#857b8e`, ambient `#141019`
- **Files:** `res://art/textures/floor_mall_*`, `wall_mall_*`

**Prompt — floor**

```
Seamless tileable texture of a dead-mall corridor floor, stained terrazzo and crushed food-court carpet, gum, coupon scraps, one repeating fluorescent reflection. Average color near #4a433c. No single hero object, no text, no horizon.
```

**Prompt — wall**

```
Seamless tileable mall wall, off-white panels gone #35303a with water stains, a repeating chair-rail, unplugged sconce holes, and a band of dead directory slats. No readable store names.
```

### `floor_backlot` / `wall_backlot` / `wood_backlot` — Sublevel Two, The Studio Backlot

- **Match colors:** `#4a4236` / `#ab9a78`, wood `#3b2412` / `#8a5a2e`

**Prompt — floor**

```
Seamless tileable studio floor, scuffed plywood and gaffer-tape spikes, sawdust, a repeating faded spike-tape X. Average color near #4a4236. No text.
```

**Prompt — wall**

```
Seamless tileable soundstage flat, canvas on timber, paint chipped to bare wood #3b2412, a repeating brace. Average color near #3d3024.
```

**Prompt — wood trim**

```
Seamless tileable plank strip of set-construction lumber, #3b2412 to #8a5a2e, nail holes, chalk marks that are not letters.
```

### `floor_penthouse` / `wall_penthouse` — Sublevel Three, The Penthouse Pit

- **Match colors:** `#3f2d4a` / `#9a78a8`, shadow `#170d22`

**Prompt — floor**

```
Seamless tileable black marble floor with gold vein, champagne stains, a repeating scuff from dress shoes. Average color near #2e2138. No text.
```

**Prompt — wall**

```
Seamless tileable penthouse wall, tufted plum velvet panels and a thin gold picture rail, one repeating burned-out sconce. Average color near #3f2d4a.
```

### Room decals

Projected on the floor. 512×512 PNG, soft edges, transparent outside the motif.

| id | Use | Prompt |
| --- | --- | --- |
| `decal_safe` | Green Room, tint `#7dffb0` | Circular floor decal, soft green wash #7dffb0, a painted ring of gaffer tape, faint "quiet set" hush marks that are not letters. |
| `decal_boss` | Boss rooms, tint `#ff4a3b` | Circular floor decal, danger red #ff4a3b, worn spotlight ellipse and four tape corners. |
| `decal_treasure` | Prize Vault | Circular floor decal, gold dust and a faint laurel worn into the tile. |
| `decal_shrine` | Chapel of Maybe, crystal `#c77dff` | Circular floor decal, violet #c77dff candle-soot ring and a chipped circle. |
| `decal_start` | Contestant Intake | Circular floor decal, white tape rectangle where a contestant is told to stand, scuffed. |
| `decal_charge` | Attack telegraph, `#ffb347` | Square tile decal, pulsing orange hazard wash #ffb347, readable as "do not stand here" with no words. |
| `decal_graffiti` | Stagehand tag, `#5ce1e6` | Wall decal of hurried cyan paint tags. Strokes only, no letters, because the game draws the sentence in a label. |

---

## 3. Contestant

The player is one `player` shape, recolored by background. Upgrade it to a shared body plus an outfit mesh per background, a mutation body per species twist, and a class accessory. Code scales the whole figure by 1.0. Starting clothes are the Complimentary Contestant Jumpsuit ("one size fits nobody") plus a Trusty copy of the background weapon.

### `player_base` — contestant body

- **Files:** `res://art/models/actors/player_base.glb` and sheet `res://art/sheets/player_base.png`
- **Blender:** Actor. Body under the jumpsuit. Neutral standing pose, feet shoulder-width, hands empty so weapons can attach later.

**Prompt**

```
Character design sheet of an ordinary human contestant in a gray one-size-fits-nobody jumpsuit, scuffed sneakers, a studio wristband, and a dead-mall earpiece. Front and three-quarter, full body, mid-gray background, even light, no weapon, no text. Average build, readable silhouette, practical costume a camera can see at thirty yards.
```

### Background outfits

Each outfit is a separate mesh worn on `player_base`. Generate a sheet, then Blender: Actor, export `res://art/models/actors/player_<id>.glb`, same skeleton or same vertex order as the base if you skin it; otherwise a rigid outfit shell parented to `Body`.

| id | Who | Color | Weapon in hand on the sheet | Prompt |
| --- | --- | --- | --- | --- |
| `guard` | Night-Shift Security Guard. Twelve years in an empty parking garage. | `#3a6ea5` | Mall-cop truncheon | Contestant outfit sheet. Navy rent-a-cop windbreaker #3a6ea5 over the gray jumpsuit, plastic badge, heavy flashlight, tired posture, truncheon in the right hand. Front and three-quarter, full body, mid-gray background. |
| `cook` | Line Cook. Fast hands, burn scars, zero fear. | `#e9e4d4` | Cast-iron skillet | Contestant outfit sheet. Stained cook's whites #e9e4d4, hairnet, burn-scar makeup on the forearms, skillet held like a shield. Front and three-quarter, full body, mid-gray background. |
| `teacher` | Substitute Teacher. Survived thirty eighth-grade classrooms. | `#c05b8a` | Pointer staff | Contestant outfit sheet. Cardigan #c05b8a, lanyard full of keys, comfortable shoes, a pointer staff. Kind and exhausted. Front and three-quarter, full body, mid-gray background. |
| `librarian` | Retired Librarian. Asked to stop practicing fire magic indoors. | `#6b4f9a` | Staff | Contestant outfit sheet. Plum cardigan #6b4f9a, reading glasses on a chain, soot on the cuffs, a staff topped with a brass bookend. Front and three-quarter, full body, mid-gray background. |
| `lifter` | Amateur Powerlifter. Never skips leg day. | `#c0392b` | Crowbar | Contestant outfit sheet. Red singlet #c0392b over the jumpsuit, chalked hands, lifting belt, crowbar across the shoulders. Broad silhouette. Front and three-quarter, full body, mid-gray background. |
| `crypto` | Former Crypto Evangelist. Believes the dungeon is bullish. | `#f39c12` | Shiv | Contestant outfit sheet. Wrinkled gold-toned blazer #f39c12 over the jumpsuit, laminated conference badge, a cheap shiv. Hopeful and slightly haunted. Front and three-quarter, full body, mid-gray background. |
| `magician` | Birthday-Party Magician. Banned from Chuckle Barn. | `#5b2c83` | Staff | Contestant outfit sheet. Purple tailcoat #5b2c83, frayed cuffs with frost on them, a wand-staff, no rabbit. Front and three-quarter, full body, mid-gray background. |
| `stuntman` | Retired Stunt Double. Every bone broken exactly once. | `#e67e22` | Crowbar | Contestant outfit sheet. Orange stunt pads #e67e22, dented helmet under one arm, knee braces, crowbar. Front and three-quarter, full body, mid-gray background. |
| `vettech` | Night-Shift Vet Tech. Forgave every bite. | `#2a9d8f` | Shiv | Contestant outfit sheet. Teal scrubs #2a9d8f, tape on the wrists, a stethoscope, a small shiv that reads as a scalpel handle. Calm. Front and three-quarter, full body, mid-gray background. The dog is a separate model. |

### Mutations

Optional species twist chosen at level-up. Each replaces the body mesh and keeps the outfit. Blender: Actor, export `res://art/models/actors/mut_<id>.glb`.

| id | Name | Prompt |
| --- | --- | --- |
| `gremlin` | Mall Gremlin | Same contestant jumpsuit on a shorter, quick body with oversized ears, long fingers, and pockets stuffed with shiny junk. Front and three-quarter sheet, mid-gray background. |
| `animatronic` | Animatronic Convert | Same jumpsuit pulled over a body of exposed servo panels and a metal jaw. Paint chipped to steel. Front and three-quarter sheet, mid-gray background. |
| `wraith` | Influencer Wraith | Same jumpsuit on a half-translucent body, ring-light catchlights in the eyes, hems dissolving into static. Front and three-quarter sheet, mid-gray background. |
| `golem` | Bargain-Bin Golem | Same jumpsuit strained over a bulky body of trophy plastic, cardboard, and foam. Slow, wide silhouette. Front and three-quarter sheet, mid-gray background. |
| `sommelier` | Sewer Sommelier | Same jumpsuit with a tarnished tastevin on the chest and a greenish drip stain. Front and three-quarter sheet, mid-gray background. |
| `specter` | Laugh-Track Specter | Same jumpsuit ghosted to half opacity, a small canned-laughter speaker bolted to the back. Front and three-quarter sheet, mid-gray background. |
| `vending` | Vending Revenant | Same jumpsuit with a snack-machine door set into the torso and scorch marks around the coin slot. Front and three-quarter sheet, mid-gray background. |

### Class accessories

Equipped at level 3. Blender: Prop, parented to `Body`, export `res://art/models/actors/class_<id>.glb`.

| id | Class | Color | Prompt |
| --- | --- | --- | --- |
| `brawler` | Knuckle Celebrity | `#ff3b3b` | Accessory sheet: red tape hand-wraps and a tiny autograph marker tucked in the wrap. Isolated on mid-gray. |
| `pyro` | Discount Pyromancer | `#ff5a1f` | Accessory sheet: a scorched correspondence-course sash and a laser-pointer lanyard. Isolated on mid-gray. |
| `knight` | Hedge Knight | `#9fb4c7` | Accessory sheet: a scrap-metal pauldron and a riot-shield strap, hedge-green cloth tied at the shoulder. Isolated on mid-gray. |
| `cutpurse` | Cutpurse Tactician | `#7a5cff` | Accessory sheet: a dark hood and a slim wallet chain. Isolated on mid-gray. |
| `saint` | Sponsored Saint | `#fff38a` | Accessory sheet: a gold snack-paste sponsor sash and a cheap plastic halo on a headband. Isolated on mid-gray. |
| `demo` | Demolitions Hobbyist | `#ff9f1c` | Accessory sheet: a bandolier of cartoon-round firebombs and a bandaged hand. Isolated on mid-gray. |
| `evangelist` | Bare-Knuckle Evangelist | `#e9c46a` | Accessory sheet: gold knuckle caps and a folded paper tract. Isolated on mid-gray. |
| `pyrotechnician` | Licensed Pyrotechnician | `#ff6b35` | Accessory sheet: a forged license in a plastic sleeve and a daisy-chain of small charges. Isolated on mid-gray. |

---

## 4. Companions, rivals, and Green Room people

Companions currently share the ally tint `#c4a574` on a generic figure. Rivals share `#e85d4c`. Give each a real mesh. Blender: Actor.

| id | Who | File | Prompt |
| --- | --- | --- | --- |
| `possum` | Biscuit, uplifted possum. Digs up snacks. Plays dead with commitment. Color `#b8b0a8`. | `actors/possum.glb` | Small uplifted possum in a tiny studio wristband, standing on hind legs, snack in one paw. Front and three-quarter, mid-gray background. About half a contestant's height. |
| `mascot_ally` | Rally, mascot suit. Cheers and soaks a hit. Color `#c05b8a`. | `actors/mascot_ally.glb` | Person inside a worn pink sports-mascot suit, dead smile, one paw raised in a cheer. Distinct from the hostile discontinued cereal mascot. Front and three-quarter, mid-gray background. |
| `mannequin` | Dolores, mannequin. Draws the eye and occasionally the claws. Color `#f4e1c1`. | `actors/mannequin.glb` | Department-store mannequin with a cracked cheek, a sale tag still tied to the wrist, posed mid-stride. Front and three-quarter, mid-gray background. |
| `dog` | Tripod, three-legged dog. Color `#c4a574`. | `actors/dog.glb` | Tough tan dog with three legs, a vet-clinic bandana, alert and kind. Front and three-quarter, mid-gray background. Low to the floor. |
| `gorsh` | Gorsh the Vend-Beast. Merchant. Hauls crates out of a vent and taps a price sign. | `actors/merchant.glb` | Vend-beast merchant: a squat creature with a vending-machine belly, a price placard for a hand, and a friendly used-car posture. Front and three-quarter, mid-gray background. The placard has no readable prices. |
| `zibble` | Producer Zibble, segment producer. Jobs, clipboard, coffee. | `actors/producer.glb` | Tired alien segment producer in a thrift-store blazer, headset, coffee, and the lucky clipboard. A small gold check-mark pin. Front and three-quarter, mid-gray background. No readable writing. |
| `rival_nix` | Nix Calder | `actors/rival_nix.glb` | Rival contestant. Cropped silver broadcast jacket, magenta streak in the hair, earpiece, gray jumpsuit underneath. Front and three-quarter, mid-gray background. |
| `rival_pia` | Pia Voss | `actors/rival_pia.glb` | Rival contestant. Olive field coat over the jumpsuit, a slim notebook, calm stance. Front and three-quarter, mid-gray background. |
| `rival_jonah` | Jonah Peck | `actors/rival_jonah.glb` | Rival contestant. Loud yellow windbreaker, sunglasses, a foam finger sawed down into a club. Front and three-quarter, mid-gray background. |
| `rival_marisol` | Marisol Quill | `actors/rival_marisol.glb` | Rival contestant. Ink-stained cardigan, glasses on a chain, a pen held like a dagger. Front and three-quarter, mid-gray background. |
| `rival_intern` | The Intern Who Stayed | `actors/rival_intern.glb` | Rival contestant. Faded intern polo under the jumpsuit, too many blank lanyards, a coffee cup taped to the wrist. Front and three-quarter, mid-gray background. |
| `rival_bran` | Bran Holt | `actors/rival_bran.glb` | Rival contestant. Stunt pads, dented helmet, duct-taped knee, crowbar. Front and three-quarter, mid-gray background. Distinct shoulder shape from the stuntman background. |

Rival look is proposed. The game only stores the six names and the shared tint `#e85d4c`.

---

## 5. Enemies

Each row is one enemy `shape` from `data/enemies.json`. ComfyUI makes the sheet. Blender builds the Actor mesh at `res://art/models/actors/<shape>.glb`. In-game scale is the `size` column; author the mesh at human-reference scale and let the game scale it. Family matters for the crafting drop (vermin and beasts drop fangs, oozes and demons drop goo, constructs drop circuitry, fans drop glitter, undead drop bone meal, goblins drop ID badges).

`figures.gd` already builds a custom primitive for most of these shapes, and the mesh it creates is named `Body`. These shapes are data-only today and fall through to that default humanoid, tinted by the enemy color: `goblin`, `steward`, `fan`, `critic`, `walker`, `understudy`, `extra`. `steward` is also a color key on NPCs in `world_view.gd`. They still get their own mesh in this pack. Goblin-family actors should include a child mesh named `Badge`, matching a node name already present in `figures.gd`.

| shape | Creature | Family | Size | Color | Prompt |
| --- | --- | --- | --- | --- | --- |
| `rat` | Gutter Rat | vermin | 0.55 | `#8a7b6b` | Low quadruped rat the color of wet cardboard #8a7b6b, municipal ear tag, too confident. Front and three-quarter, mid-gray background. |
| `roach` | Chittering Roach | vermin | 0.45 | `#6b4226` | Giant cockroach #6b4226 wearing a tiny "most likely to outlast" ribbon. Low, wide, six legs readable in silhouette. Front and three-quarter, mid-gray background. |
| `goblin` | Goblin Intern | goblin | 0.75 | `#6fa84a` | Short green intern #6fa84a in a stained polo and a blank lanyard, holding a stapler like a weapon. Front and three-quarter, mid-gray background. |
| `hexer` | Goblin Hex-Temp | goblin | 0.75 | `#8d5fd3` | Goblin temp in a purple contractor vest #8d5fd3, glowing sticky-note curses stuck to its arms. Front and three-quarter, mid-gray background. |
| `mold` | Mold Shambler | ooze | 0.85 | `#7fae3a` | Shambling mound of break-room fridge mold #7fae3a, a yogurt lid for a face, slow and damp. Front and three-quarter, mid-gray background. |
| `skeleton` | Bone Clerk | undead | 0.80 | `#e6dfc8` | Skeleton clerk #e6dfc8 in a melted name-tag lanyard, rubber stamp raised. Front and three-quarter, mid-gray background. |
| `imp` | Sprinkler Imp | demon | 0.60 | `#e0482f` | Small red imp #e0482f built around a ceiling sprinkler head, spraying a warning mist. Front and three-quarter, mid-gray background. |
| `mascot` | Discontinued Mascot | construct | 1.10 | `#f2b233` | Huge foam cereal-mascot suit #f2b233, dead eyes, cereal-box paunch, fists like mittens. Hostile, distinct from the ally mascot Rally. Front and three-quarter, mid-gray background. |
| `steward` | Union Shop Steward | goblin | 0.80 | `#c9a227` | Goblin in a gold union vest #c9a227, clipboard shield, whistle. Front and three-quarter, mid-gray background. |
| `slime` | Gelatinous Temp and the smaller Temp Fragment | ooze | 0.80 and 0.45 | `#4fc3a1` | Translucent office-slime cube #4fc3a1 with a swallowed swivel chair inside. One sheet showing the full temp and a smaller angry fragment. Mid-gray background. One mesh; the fragment is the same file scaled. |
| `shark` | Carpet Shark | beast | 0.80 | `#7b8fa6` | Shark #7b8fa6 swimming through a torn flap of industrial carpet worn like water. Low dorsal fin silhouette. Front and three-quarter, mid-gray background. |
| `drone` | Rogue Camera Drone | construct | 0.55 | `#5ce1e6` | Flying camera drone, cyan lens #5ce1e6, taped wires, a tally light. Hovering, no legs. Front and three-quarter, mid-gray background. |
| `bouncer` | Velvet Rope Bouncer | brute | 1.05 | `#2b2b35` | Massive bouncer #2b2b35 in a too-small tuxedo jacket, velvet rope wrapped around one fist. Front and three-quarter, mid-gray background. |
| `fan` | Obsessive Superfan | fan | 0.70 | `#ff7eb6` | Human fan #ff7eb6 in homemade merch, poster tube, frantic lean. Front and three-quarter, mid-gray background. |
| `critic` | Scathing Critic | undead | 0.80 | `#a0a4c8` | Gaunt critic #a0a4c8 in a moth-eaten turtleneck, pen like a stiletto, one-star pin. Front and three-quarter, mid-gray background. |
| `bomber` | Pyro-Technician | goblin | 0.75 | `#ff9f1c` | Goblin in an orange burns suit #ff9f1c, goggles, a round cartoon bomb hugged to the chest. Front and three-quarter, mid-gray background. |
| `pigeon` | Food Court Pigeon | vermin | 0.50 | `#8e9aa8` | Overfed pigeon #8e9aa8 with a french-fry spear in its beak and mall-tile eyes. Front and three-quarter, mid-gray background. |
| `walker` | Undead Mall-Walker | undead | 0.80 | `#8fa38a` | Shambling mall walker #8fa38a in a tracksuit and visor, fanny pack, knitting needles. Front and three-quarter, mid-gray background. |
| `thief` | Kiosk Pickpocket | goblin | 0.70 | `#3d5a80` | Skinny goblin in a kiosk polo #3d5a80, sample tray that hides a blade. Front and three-quarter, mid-gray background. |
| `puffball` | Spore Puffball | ooze | 0.60 | `#c9b458` | Round spore sac #c9b458 on a thin stalk, ready to pop, soft and readable. Front and three-quarter, mid-gray background. |
| `understudy` | Understudy Doppelganger | demon | 0.80 | `#6c5ce7` | Featureless understudy #6c5ce7 wearing a copy of the contestant jumpsuit, face a smooth mirror. Front and three-quarter, mid-gray background. |
| `boom` | Boom Mic Operator | goblin | 0.80 | `#4a6fa5` | Goblin with a nine-foot boom pole and a fuzzy microphone, vest #4a6fa5. The pole is the silhouette. Front and three-quarter, mid-gray background. |
| `animatronic` | Malfunctioning Animatronic | construct | 1.00 | `#b5651d` | Birthday animatronic bear #b5651d with the jaw unhinged and gears showing, party hat askew. Front and three-quarter, mid-gray background. |
| `director` | Casting Director | demon | 0.80 | `#e07a5f` | Horned casting director #e07a5f in a turtleneck and scarf, riding a director's chair it carries with it, megaphone. Front and three-quarter, mid-gray background. |
| `extra` | Nameless Extra | goblin | 0.65 | `#b8b8b8` | Gray goblin extra #b8b8b8 in an unmarked costume smock, number card with no digits. Front and three-quarter, mid-gray background. |
| `paparazzo` | Feral Paparazzo | fan | 0.75 | `#2d3142` | Crouched photographer #2d3142, huge telephoto lens, flash unit, coat of pockets. Front and three-quarter, mid-gray background. |
| `champagne` | Champagne Elemental | demon | 0.75 | `#f3e5ab` | Living champagne splash #f3e5ab corkscrewed into a torso, foil collar, pressurized and furious. Front and three-quarter, mid-gray background. |
| `golem` | Gilded Golem | construct | 1.15 | `#d4af37` | Golem #d4af37 built from melted trophies, sharp award-cup elbows, heavy. Front and three-quarter, mid-gray background. |
| `lawyer` | Entertainment Lawyer | undead | 0.80 | `#1d3557` | Skeletal lawyer in a navy suit #1d3557, briefcase spilling cease-and-desist scrolls. Front and three-quarter, mid-gray background. |
| `paralegal` | Overworked Paralegal | goblin | 0.70 | `#a8dadc` | Exhausted goblin paralegal, shirt #a8dadc, stapler extended, dark circles. Front and three-quarter, mid-gray background. |
| `mimic` | Hungry Crate | construct | 0.80 | `#9a6a36` | Wooden crate #9a6a36 with a tongue of packing paper and teeth along the lid. Reads as a crate until the mouth opens. Front and three-quarter, plus a closed-lid view. Mid-gray background. |
| `ogre` | Brunhold Oxgrind, Sector Warden | boss | 1.60 | `#7c8a93` | Huge middle-manager ogre #7c8a93 in a torn dress shirt and lanyard, a DENIED stamp in one hand and a sledge in the other. Front and three-quarter, mid-gray background. Boss scale. |
| `foreman` | Grukka Rivetjaw, Demolition Foreman | boss | 1.60 | `#e8b923` | Massive foreman #e8b923 in a yellow hard hat and a jaw of rivets, jackhammer slung like a spear. Front and three-quarter, mid-gray background. Boss scale. |
| `diva` | Vexa Glitterqueen, Ratings Diva | boss | 1.40 | `#ff4fd8` | Towering diva in a magenta gown #ff4fd8 made of rating-chart foil, microphone scepter, spotlight catching every edge. Front and three-quarter, mid-gray background. Boss scale. |

### Zone-boss variants

These reuse a base shape with a gold or colored aura (`#ffd23f` unless noted). Blender: start from the base Actor and add the silhouette pieces. Export `res://art/models/actors/<id>.glb`. ComfyUI prompt is the extra pieces on a sheet, mid-gray background.

| id | Name | Base | Aura | Add |
| --- | --- | --- | --- | --- |
| `z_nibbles` | Queen Nibbles, Monarch of the Drains | `rat` | `#ffd23f` | A crown of gnawed pennies and a drain-grate cape. |
| `z_squeaks` | Mister Squeaks, The Mascot Who Snapped | `mascot` | `#ff4fd8` | Popped balloons, a snapped smile, an oversized foam finger. |
| `z_gristle` | Supervisor Gristle | `steward` | `#9fb4c7` | A bigger clipboard, a termination stamp, middle-management shoulder pads. |
| `z_rhonda` | Big Rhonda, Head of Door Policy | `bouncer` | `#e63946` | Steel loafers, a velvet rope worn as a sash, list clipboard with no names. |
| `z_voss` | Sparky Voss | `bomber` | `#ff9f1c` | Extra charges, a detonator glove, soot crown. |
| `z_unit7` | Unit 7, Decommissioned Security Bot | `golem` | `#5ce1e6` | Security-bot chassis plates, a flashing visor, trophy-gold replaced by scrap steel. |
| `z_glimmer` | Lady Glimmer, Tabloid Queen | `paparazzo` | `#fff38a` | A larger telephoto, a foil gown over the coat, flashbulbs. |
| `z_critic` | The Critic Supreme | `critic` | `#a0a4c8` | A balcony railing he carries, a zero-star medal, a long quill. |
| `z_vex` | Director Vex, Auteur of Suffering | `director` | `#c77dff` | A bigger megaphone, film-strip scarf, cutting-room shears. |

### Elite rings

One soft ring texture, tinted in engine by the affix color. Blender: none.

- **File:** `res://art/vfx/elite_ring.png`

**Prompt**

```
Circular ground aura, transparent outside a soft ring, white so the game can tint it. Colors used at runtime: juiced #ff4d6d, armored #9fb4c7, swift #5ce1e6, vampiric #b3001b, volatile #ff9f1c, venomous #8ac926.
```

---

## 6. Props

Blender: Prop, unless noted. Export `res://art/models/props/<id>.glb`. Generate a turnaround on mid-gray first.

| id | In the game | Prompt | Blender note |
| --- | --- | --- | --- |
| `chest` | Chest. Bump to open. | Brass-bound mall locker chest, slightly smiling hardware, closed. Three-quarter product turnaround. | Hinged lid node named `Lid`. Closed is the default pose. |
| `chest_welcome` | Welcome chest at intake. A starter kit and a note. | The same chest, lid ajar, tissue paper and a gray jumpsuit sleeve visible. | Variant of `chest`. |
| `chest_showcase` | Showcase chest. Opens to a drumroll. | The same chest on a tiny scuffed turntable with a gold gel light. | Variant of `chest`. Child node `Light`. |
| `crate` | Crate. Smash it. Also the mimic's disguise, so keep this one toothless. | Plain wooden shipping crate, stenciled block marks that are not letters, smashable. | Rigid. |
| `pillar` | Pillar. | Square mall pillar with a dead directory frame and a scuff band at shoulder height. | Rigid. Occluder, keep the footprint under 0.8 m. |
| `shaft` | Descent Shaft. Sealed until the boss dies, then open. | Vertical service shaft mouth, plum inner void #1a0033, metal collar #3a3f47, hazard ticks with no words. | Child empty `Hole` at the opening. A slow `idle` spin on warning lights is optional. |
| `shrine` | Shrine of Questionable Blessings. | A chapel plinth made from a customer-service podium, violet crystal #c77dff, unlit tea candles. | Child mesh `Crystal`. |
| `fountain` | Healing fountain. One drink, then dry. Tastes faintly of pennies. | Dead-mall fountain, cyan water #4dc9ff, penny-colored basin, one cherub replaced by a security camera. | Child mesh `Water` and `Light`. |
| `couch` | Recovery Couch. Sponsored nap. | Overstuffed purple couch #7b2d8b with a clear plastic cover and a sponsor tag. | Rigid. |
| `banner` | CRAWLCAST promotional banner. | Vertical vinyl banner, plum field, the word CRAWLCAST in the wordmark style, standing on a tripod base. This is one of the few assets that should contain that word. | Rigid. |
| `workbench` | Contestant Workbench. Craft and salvage. | Folding table #777d85, pegboard, glue gun, a vise, scrap metal in a coffee can. | Rigid. |
| `bones` | Remains of a previous contestant. | A small respectful pile of bones in a torn gray jumpsuit, name tag blank. Somber, not gory. | Rigid. |
| `memorial` | Memorial. Bump to pay respects. Plaque text is runtime. | Standing plaque #e0c3fc, empty name plate, one sponsor staple, a tea light. | Rigid. Leave the plate blank. |
| `cooler` | Water cooler. A drink on a timer. | Office water cooler, half full, a paper-cup stack, a tiny contract tag. | Rigid. |
| `mirror` | Makeup mirror. Ring light. Camera Ready. | Vanity mirror on a stick, round ring light, a few dead bulbs. | Child node `Light`. |
| `beacon` | Homing beacon. Points at the Green Room. Gorsh swears it is not a bomb. | A device that is trying very hard not to look like a bomb: antenna, blinking cyan lamp, too many "not a bomb" stickers with no readable words. | Child node `Light`. |
| `camera` | Smashable camera drone parked on a tile. Distinct from the flying enemy. | Tripod security camera, red tally #ff2020, cyan status LED, a lens you can break. | Rigid. |
| `welcome` | Contestant Intake lectern. Color `#9aa3ad`. | A gray intake lectern with a blank waiver clipboard and a worn "stand here" tape square at its base. | Rigid. |
| `door` | Dungeon door. Tracked in the doors stat. `world_view.gd` has a `Hinge`. | Mall service door, push bar, scuffed paint, a small reinforced window. Closed. | Pivot empty named `Hinge` on the left edge. Open pose is +90 degrees yaw. |
| `weapon_rack` | Ground loot marker for gear, used with tints. | A small floating weapon stand holding a generic crowbar, for scale reference only. | See pickups instead. This sheet is the modeling reference. |

### Traps

Hidden until sprung, then they play a mesh. Blender: Prop. Keep the footprint inside one tile.

| id | Trigger | Color | Prompt |
| --- | --- | --- | --- |
| `spike` | Spikes erupt. | `#d9d9d9` | A floor plate of retractable steel spikes, shown extended, one tile wide. |
| `gas` | A hiss of green gas. | `#8ac926` | A cracked floor vent coughing a green gas puff #8ac926. The puff is a separate flipbook; the mesh is the vent. |
| `fire` | Flame from a vent. | `#ff8a3c` | A scorched floor nozzle, flame modeled only as a short emissive cone so the flipbook can sit on it. |
| `alarm` | Everything nearby hears you. | `#c0c7d1` | A wall-mounted alarm horn #c0c7d1 with a red glass bulb. |
| `snare` | The player's own snare, and the snare-kit trap. | `#2b2b2b` | A low black snare of wire and a tin can, obvious once seen, flat enough to read as floor clutter. |

---

## 7. Icons

ComfyUI only. Blender none, except the pickup note at the end of this section. 256×256 RGBA, three-quarter product view, transparent background. Gameplay tint is listed so the object stays recognizable after the UI tints rarity.

### Weapons and armor

| icon | Used by | Prompt |
| --- | --- | --- |
| `crowbar` | Crowbar | A scuffed steel crowbar, three-quarter, transparent background, reads at 32 pixels. |
| `pan` | Cast-Iron Skillet | A black cast-iron skillet, grease shine, three-quarter, transparent background. The current icon drawer has no `pan` picture; this adds one. |
| `dagger` | Shiv | A short shiv made from a snapped mall-directory letter, three-quarter, transparent background. |
| `mace` | Mall-Cop Truncheon, Sledgehammer | A black police truncheon with a wrist loop, three-quarter, transparent background. |
| `axe` | Hatchet, Fire Axe | A red fire axe, three-quarter, transparent background. The current drawer has no `axe` picture; this adds one. |
| `sword` | Shortsword, Longsword | A short practical sword with a duct-tape grip, three-quarter, transparent background. |
| `staff` | Pointer Staff, Laser Pointer Wand | A teacher pointer with a dead laser tip glowing faint red, three-quarter, transparent background. |
| `spear` | Rebar Spear | A length of rebar sharpened and wrapped in tape, three-quarter, transparent background. |
| `helm` | Hard Hat, Bucket Helm, Riot Visor | A yellow hard hat with a cracked brim, three-quarter, transparent background. |
| `chest` | Hoodie, vest, jerkin, hauberk, plate | A gray contestant hoodie on an invisible torso, three-quarter, transparent background. Icon id is `chest`, distinct from the prop chest. |
| `legs` | Reinforced Jeans, Shin Guards | Reinforced jeans with sewn-in shin guards, three-quarter, transparent background. |
| `boots` | Sneakers, Steel-Toe Boots | Scuffed steel-toe boots, three-quarter, transparent background. |
| `shield` | Trash Can Lid, Buckler, Riot Shield | A trash-can lid used as a shield, dents, three-quarter, transparent background. |
| `tome` | Self-Help Tome | A thick self-help paperback, bookmark ribbon, three-quarter, transparent background. No readable title. |
| `ring` | Ring | A mood ring, stone an uncertain color, three-quarter, transparent background. |
| `amulet` | Amulet | A laminated all-access lanyard badge coiled into an amulet, three-quarter, transparent background. Blank badge. |

### Consumables, pods, materials

| icon | Name | Prompt |
| --- | --- | --- |
| `potion_red` | Health Tonic | A cherry-red tonic bottle, cheap pharmacy glass, three-quarter, transparent background. |
| `potion_blue` | Focus Fizz | A blue soda-canister vial, fizzing, three-quarter, transparent background. |
| `potion_green` | Antidote Chew | A green chew in a blister pack, three-quarter, transparent background. |
| `elixir` | Elixir of Minor Ascension | A small gold-capped vial with a rising bubble, three-quarter, transparent background. |
| `bomb` | Firebomb | A round homemade firebomb with an orange rag #ff7b00, three-quarter, transparent background. |
| `bomb_nail` | Nail Bomb | The same bomb wrapped in a bristling nail belt, three-quarter, transparent background. |
| `bomb_goo` | Sticky Goo Bomb | The same bomb slimed in green goo, three-quarter, transparent background. |
| `grenade_glitter` | Glitter Grenade | A pink grenade #ff4fd8 leaking glitter, three-quarter, transparent background. |
| `scroll` | Scroll of Relocation | A curled call sheet tied with red string, three-quarter, transparent background. No readable words. |
| `scroll_map` | Scroll of Cartography | An unrolled floorplan scroll, cyan ink lines, three-quarter, transparent background. No readable words. |
| `clipboard` | Producer's Lucky Clipboard | A coffee-ringed clipboard, names crossed out as abstract marks, three-quarter, transparent background. |
| `gold` | Gold | A stack of prop coins and a crumpled sponsor bill, three-quarter, transparent background. |
| `snare` | Snare Kit | A coiled wire snare and a tin trigger, three-quarter, transparent background. |
| `compass` | Green Room Compass | A brass compass whose needle is a tiny camera lens, three-quarter, transparent background. |
| `pod_bronze` | Bronze Prize Pod | An egg-shaped prize pod, bronze #cd7f32, a seam like a product package, three-quarter, transparent background. |
| `pod_silver` | Silver Prize Pod | The same pod in silver #d8dde3. |
| `pod_gold` | Gold Prize Pod | The same pod in gold #ffd23f. |
| `pod_legendary` | Legendary Prize Pod | The same pod in hot trophy orange #ff7b00 with a cracked-laurel seam. |
| `mat_scrap` | Scrap Metal | A coffee can of bent brackets and screws, three-quarter, transparent background. |
| `mat_goo` | Monster Goo | A jar of judgmental green slime, three-quarter, transparent background. |
| `mat_fang` | Fangs & Claws | A paper tray of cleaned fangs and claws, three-quarter, transparent background. |
| `mat_circuit` | Salvaged Circuitry | A humming circuit board with a tiny intact jingle-light, three-quarter, transparent background. |
| `mat_glitter` | Weaponized Glitter | A vial of magenta glitter #ff4fd8, a few grains escaped, three-quarter, transparent background. |
| `mat_bone` | Bone Meal | A kraft sack of pale bone meal, three-quarter, transparent background. No label text. |
| `mat_badge` | Goblin ID Badge | A blank green ID badge on a torn lanyard, three-quarter, transparent background. |

### Unique gear icons

These currently inherit the base icon. Give each its own file at `res://art/icons/<id>.png` so the tooltip can prefer it and fall back to the base icon.

| id | Name | Base icon | Prompt |
| --- | --- | --- | --- |
| `u_stapler` | The Unkillable Stapler | `mace` | A heroic office stapler, scorched, still smiling, three-quarter, transparent background. |
| `u_spatula` | Spatula of the Final Shift | `pan` | A broad spatula nicked like a sword, grease halo, three-quarter, transparent background. |
| `u_crown` | Crown of Viral Moments | `helm` | A crown made from a traffic cone and phone-shaped jewels, three-quarter, transparent background. |
| `u_bathrobe` | Bathrobe of Unearned Confidence | `chest` | A plush bathrobe that reads as armor, monogram blurred, three-quarter, transparent background. |
| `u_ring` | Mood Ring of Poor Decisions | `ring` | A mood ring stuck on a single reckless color, three-quarter, transparent background. |
| `u_lanyard` | All-Access Lanyard | `amulet` | A backstage lanyard with too many blank passes, three-quarter, transparent background. |
| `u_detonator` | Grandpa's Detonator | `amulet` | A 1970s detonator plunger the size of a pendant, big red button, three-quarter, transparent background. |
| `u_hottake` | The Hot Take | `dagger` | A dagger with a comment-section glow along the edge, three-quarter, transparent background. |
| `u_momentum` | Championship Ring of Momentum | `ring` | A chunky sports championship ring, three-quarter, transparent background. |
| `u_parka` | Porcupine Parka | `chest` | A parka bristling with short quills, three-quarter, transparent background. |
| `u_mic` | Echo Chamber Mic | `tome` | A handheld microphone that echoes itself as a second faint mic, three-quarter, transparent background. |
| `u_knuckles` | Golden Knuckles | `mace` | Solid gold brass knuckles, tasteless and heavy, three-quarter, transparent background. |
| `u_locket` | Lodestone Locket | `amulet` | A locket cracked open on a tiny photo of a couch, three-quarter, transparent background. |

### Zone-boss drops

| id | Name | Prompt |
| --- | --- | --- |
| `drop_nibbles` | Crown of Gnawed Pennies | A small crown of pennies, every coin chewed, three-quarter, transparent background. |
| `drop_squeaks` | Oversized Foam Hand | A foam finger numbered 1, pointing, three-quarter, transparent background. |
| `drop_gristle` | Supervisor's Lanyard | A supervisor lanyard and blank badge, three-quarter, transparent background. |
| `drop_rhonda` | Bouncer's Steel Loafers | Polished steel dress shoes, scuffed, three-quarter, transparent background. |
| `drop_voss` | Voss's Lucky Detonator Glove | A four-finger glove with a detonator stud, three-quarter, transparent background. |
| `drop_unit7` | Unit 7's Chassis Plate | A curved robot chest plate with a dark visor slit, three-quarter, transparent background. |
| `drop_glimmer` | Glimmer's Telephoto Lens | A long camera lens, gold ring, three-quarter, transparent background. |
| `drop_critic` | One-Star Quill | A sharp quill with a single star charm, three-quarter, transparent background. |
| `drop_vex` | Megaphone of Final Cuts | A director megaphone with a cutting-room blade along the rim, three-quarter, transparent background. |

### Skill glyphs

Hotbar pictures. File `res://art/skills/<glyph>.png`. Several skills share a glyph; one picture serves all of them. The current procedural drawer only special-cases some glyphs (`fist`, `dash`, `flame`, `knife`, `cross`, `snow`, `heart`, `coin`, `meteor`, `halo`). The others still need real pictures.

| glyph | Skills | Color | Prompt |
| --- | --- | --- | --- |
| `fist` | Power Strike, Haymaker, Sermon on the Mount | `#ff7849` | A taped fist mid-punch, transparent background, hotbar icon. |
| `arc` | Cleave | `#ffb347` | A wide orange swing arc, transparent background, hotbar icon. |
| `dash` | Lunge, Shadowstep | `#ffd166` | A motion dash chevron, transparent background, hotbar icon. |
| `flame` | Firebolt | `#ff5a1f` | A compact firebolt, transparent background, hotbar icon. |
| `knife` | Throwing Knife, Backstab | `#c0c7d1` | A thrown knife in profile, transparent background, hotbar icon. |
| `cross` | Mend | `#5fd35f` | A green field-medic cross on a bandage patch, transparent background, hotbar icon. |
| `star` | Showboat | `#ff4fd8` | A magenta showbiz star, transparent background, hotbar icon. |
| `snow` | Freezer Burn | `#7fdbff` | A burst of freezer-burn frost, transparent background, hotbar icon. |
| `heart` | Toughness, Sic 'Em | `#e05252` | A sturdy heart, transparent background, hotbar icon. |
| `shield` | Iron Skin, Shield Wall | `#9fb4c7` | A raised scrap shield, transparent background, hotbar icon. |
| `eye` | Keen Eye | `#ffd23f` | A gold keen eye, transparent background, hotbar icon. |
| `orb` | Meditation | `#6c8cff` | A calm blue focus orb, transparent background, hotbar icon. |
| `coin` | Scavenger | `#f4c542` | A gold coin with a camera-aperture hole, transparent background, hotbar icon. |
| `mic` | Crowd Pleaser, Objection! | `#ff4fd8` | A handheld mic, transparent background, hotbar icon. |
| `compass` | Wayfinder | `#5ce1e6` | A small compass rose, transparent background, hotbar icon. Distinct from the item compass by being flatter and more symbolic. |
| `meteor` | Discount Meteor | `#ff2e00` | A slightly used meteor with a price-sticker scar, transparent background, hotbar icon. |
| `halo` | Divine Sponsorship, Rally Cry | `#fff38a` | A cheap plastic halo, transparent background, hotbar icon. |
| `bomb` | Cluster Bomb, Daisy Chain | `#ff9f1c` | A cluster of three tiny bombs, transparent background, hotbar icon. |

### Status chips

HUD currently prints these as words. Replace the chip with an icon plus the existing word if it still fits. `res://art/ui/status_<id>.png`.

| id | Label | Prompt |
| --- | --- | --- |
| `poison` | Poisoned | Tiny status icon, green dripping drop, transparent background. |
| `burn` | Burning | Tiny status icon, small flame, transparent background. |
| `bleed` | Bleeding | Tiny status icon, a red thread, transparent background. |
| `stun` | Stunned | Tiny status icon, circling stars, transparent background. |
| `slow` | Slowed | Tiny status icon, a boot in molasses, transparent background. |
| `weaken` | Weakened | Tiny status icon, a bent sword, transparent background. |
| `shield` | Shielded | Tiny status icon, a gray barrier arc, transparent background. |
| `rage` | Enraged | Tiny status icon, a red jagged pulse, transparent background. |
| `regen` | Regenerating | Tiny status icon, a green plus, transparent background. |
| `blessed` | Blessed | Tiny status icon, a soft gold spark, transparent background. |
| `cursed` | Cursed | Tiny status icon, a violet crack, transparent background. |
| `marked` | Marked | Tiny status icon, a targeting reticle, transparent background. |
| `compass` | Compass | Tiny status icon, a cyan needle, transparent background. |
| `momentum` | Momentum | Tiny status icon, three speed lines, transparent background. |
| `glam` | Camera Ready | Tiny status icon, a ring light, transparent background. |

### Ground pickups

Blender: Pickup. One small mesh per icon id above that can lie on a tile (`weapon`, `armor`, `jewelry`, `pod`, and each consumable the figures script already builds: `hp_potion`, `mp_potion`, `antidote`, `firebomb`, `nail_bomb`, `goo_bomb`, `glitter_grenade`, `elixir`, `tome_skill`, plus `gold` and `clipboard`). Pin the matching PNG in Blender as the reference and export `res://art/models/pickups/<icon>.glb`. No new ComfyUI prompt; the icon prompt is the design.

---

## 8. Combat VFX

Eight-frame strips unless noted. Blender is listed only where a mesh sells the gag better than a card. The game already spawns these by name from `world_view.gd` and `game.gd`: `attack`, `burst`, `projectile`, `death`, `teleport`, `heal`, `crit`, `bomb`, `debris`, `charge`, plus skill colors for fire, frost, and glitter.

| id | Reads as | Blender | Prompt |
| --- | --- | --- | --- |
| `vfx_attack` | Melee swipe | none | Eight-frame slash arc, white-to-gold, transparent background, loopable. |
| `vfx_burst` | AoE pop, cleave, frost edge | none | Eight-frame ground burst ring, one-shot, transparent background. |
| `vfx_bolt` | Firebolt projectile `#ff5a1f` | none | Eight-frame firebolt flying rightward, loopable, transparent background. |
| `vfx_knife` | Throwing knife `#e0e6ee` | none | Eight-frame spinning knife, loopable, transparent background. |
| `vfx_heal` | Mend and fountain `#5fd35f` | none | Eight-frame rising green motes, loopable, transparent background. |
| `vfx_crit` | Critical hit | none | Eight-frame gold spark burst, one-shot, transparent background. |
| `vfx_death` | Enemy death puff | none | Eight-frame dust-and-confetti puff, one-shot, transparent background. Keep it comic. |
| `vfx_teleport` | Shadowstep, scroll `#b9a8ff` | none | Eight-frame violet static tear, one-shot, transparent background. |
| `vfx_bomb` | Explosions `#ff9f1c` | none | Eight-frame orange blast with a smoke ring, one-shot, transparent background. |
| `vfx_debris` | Rubble `#b0a08a` | none | Eight-frame chips of mall tile flying out and falling, one-shot, transparent background. |
| `vfx_frost` | Freezer Burn `#7fdbff` | none | Eight-frame frost nova ring, one-shot, transparent background. |
| `vfx_meteor` | Discount Meteor | A 200-triangle rock mesh `props/meteor.glb` plus this strip | Eight-frame fiery trail, loopable, transparent background. The rock is a used meteor with a scorch scar. |
| `vfx_glitter` | Glitter grenade `#ff4fd8` | none | Eight-frame magenta glitter pop, one-shot, transparent background. |
| `vfx_gas` | Gas trap `#8ac926` | none | Eight-frame green gas puff, loopable, transparent background. |
| `vfx_spotlight` | Showboat and the diva | none | A vertical light shaft texture, white-to-gold, soft edges, single frame, transparent background. The engine tints it `#fff38a`. |

---

## Global prompt to activate them in game

Paste this to a coding agent that has the Godot 4.7 CRAWLCAST source. The public `crawlcast` repo ships the desktop build, not the project. The script names below are the ones inside the v1.0.0 PCK. Keep every gameplay number in the JSON data. Swap only the view.

```
You are wiring a finished CRAWLCAST art pack into the Godot 4.7 project. The pack follows res://art/ as listed in graphics.md, with res://art/manifest.json naming every file. Gameplay JSON stays as it is. Combat, dungeon generation, saves, and UI text stay as they are. When a file is missing, keep today's procedural draw for that one id so a partial pack still runs.

1. Project icon. Replace icon.svg with res://art/icon/crawlcast_icon.png and point the application icon at it.

2. Actors. In scripts/view/figures.gd, before building primitives for a shape, instance res://art/models/actors/<shape>.glb if it exists. Name the glTF root Body, the same node name the procedural builder uses. Apply the existing color as a modulate on top of the textured material, and apply the existing size scale. Load every enemy shape from data/enemies.json, including the ones that currently fall through to the default humanoid: goblin, steward, fan, critic, walker, understudy, and extra. Also load rat, roach, hexer, mold, skeleton, imp, mascot, slime, shark, drone, bouncer, bomber, pigeon, thief, puffball, boom, animatronic, director, paparazzo, champagne, golem, lawyer, paralegal, mimic, ogre, foreman, diva, and player.

3. Player slots. Build the player from player_base.glb, then attach player_<background_id>.glb as the outfit, mut_<id>.glb when a mutation is chosen, and class_<id>.glb when a class is chosen. Background ids: guard, cook, teacher, librarian, lifter, crypto, magician, stuntman, vettech. Mutation ids: gremlin, animatronic, wraith, golem, sommelier, specter, vending. Class ids: brawler, pyro, knight, cutpurse, saint, demo, evangelist, pyrotechnician.

4. Named characters. Companions possum, mascot_ally, mannequin, and dog replace the generic ally figure, tinted with their meta.json colors. Rivals nix, pia, jonah, marisol, intern, and bran use rival_<id>.glb and the rival tint #e85d4c. Gorsh uses merchant.glb. Producer Zibble uses producer.glb. Zone bosses use z_<id>.glb when that file exists, otherwise the base shape plus the existing aura.

5. Props and traps. In the same figures path, instance res://art/models/props/<id>.glb for chest, chest_welcome, chest_showcase, crate, pillar, shaft, shrine, fountain, couch, banner, workbench, bones, memorial, cooler, mirror, beacon, camera, welcome, door, spike, gas, fire, alarm, and snare. Honor child nodes Hinge, Lid, Water, Crystal, Hole, and Light. The door swings on Hinge. Shaft, shrine crystal, fountain water, mirror light, and beacon light may use their existing spin or light_energy tweens.

6. Floors and walls. In scripts/view/materials.gd, depth 1 loads floor_mall and wall_mall, depth 2 loads floor_backlot, wall_backlot, and wood_backlot, depth 3 loads floor_penthouse and wall_penthouse. Each set has _albedo, _normal, and _roughness. Room kinds safe, boss, treasure, shrine, and start project the matching decal. The charge telegraph uses decal_charge. Graffiti uses decal_graffiti under the existing label, because the sentence is still drawn as text.

7. Icons. In scripts/ui/icons.gd, IconTextures loads res://art/icons/<id>.png and res://art/skills/<glyph>.png before generating a texture. Unique ids and zone-boss drop ids win over the base icon. Status chips on the HUD load res://art/ui/status_<id>.png. Rarity frames, hotbar slots, bars, panel, buttons, tooltip, map pins, end stamps, the on-air bug, the wordmark, and the title key art replace the matching StyleBoxes and Labels in ui_kit.gd, hud.gd, title_screen.gd, and end_screen.gd. Sponsor bugs use res://art/ui/sponsor_<id>.png next to sponsor names from announcer.json. EMCEE-9's portrait sits beside announcer lines.

8. Pickups and VFX. Ground items instance res://art/models/pickups/<icon>.glb. Combat effects play the matching strip in res://art/vfx/ as an animated transparent quad: attack, burst, bolt, knife, heal, crit, death, teleport, bomb, debris, frost, meteor, glitter, gas, spotlight. Elite monsters use vfx/elite_ring.png tinted by the affix color already in enemies.json.

9. Import. Albedo and UI are sRGB. Normals and roughness are linear, no mipmaps on UI, mipmaps on world textures. glTF materials stay as imported. Add the art folder to the export include list.

10. Check. Run tools/shots.gd and confirm the icon contact sheet shows the new pictures, including pan and axe. Start a run as the guard, the librarian, and the vet tech. Walk a Dead Mall floor, a Backlot floor, and a Penthouse floor. Open a chest, a shrine, a fountain, and the Green Room. Trigger one melee hit, one firebolt, one bomb, and one elite. Finish or abandon a run and look at the end stamp. Missing files must fall back to the old procedural art rather than erroring.
```
