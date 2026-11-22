# Task: censor nudity in an image

**Goal:** a safe-for-work copy of an image: nudity found by NudeNet is pixelated, blurred or blacked out. Workflow: `nudenet-censor`. No prompt.

## Ask if unsure
- Pixel, blur or black? Default: pixel.
- Which parts? Default: genitals and breasts on, buttocks off.

## Inputs
| Node | Set |
|---|---|
| `Picture` | the image |
| `Censor` | `style` (`pixel`, `blur`, `black`), `genitals`, `breasts`, `buttocks` (true/false), `confidence` (default 0.25), `padding` (default 0.15) |

## Run
```bash
$RUN nudenet-censor --set "Picture.image=@in.png" --set "Censor.style=blur"
```
Output: `output/nudenet-censor/sfw`.

## Check
- **Every exposed part is covered,** including small ones; lower `confidence` if something is missed.
- **Nothing else is touched.**
