# Krea 2: how to prompt it

Used by: `image-text-to-image`, `image-clone-vibe`. Our workflows run Krea 2 **Turbo** (int8) at 8 steps, CFG 1.

## What works (sources at the end)
- **Natural sentences, in this order:** subject → what they do → setting → light → camera and lens → look and finish. Krea's examples open with the subject, then add material, framing and lighting (fal). Comma lists also work, but sentences read cleaner for a photo.
- **Detail narrows the output.** "The more detail you give — style, medium, lighting, composition — the tighter the model's output range becomes" (Krea). A short prompt explores, a detailed one locks a look. For a set of matching images, be detailed.
- **Photography words steer the camera:** shot type (close-up, medium shot, full body, low angle, wide angle), the device ("amateur iPhone photo", "35 mm film"), the light ("on-camera flash", "golden hour sunlight", "soft window light"), the finish (film grain, motion blur, slight overexposure).
- **No negative prompt.** At CFG 1 a negative does nothing, and NAG doesn't fire on Krea 2 either (measured, 2026-11-07). Say what you want instead.
- **The character comes from her LoRA plus one identity line:** the LoRA trigger and "She is a 21-year-old woman with …" are added by the workflow's Final prompt node. Your scene text never describes her face.

## Examples (general patterns; swap in your own subject and place)
1. `An amateur iPhone flash photograph of a young woman leaning against the front fender of a white sports car at a gas station late at night, harsh on-camera flash, dark sky, wet asphalt reflecting neon signs, slightly overexposed, candid.`
2. `A candid full-body photo of a young woman walking across a sunlit city crosswalk at midday, low angle from a phone held at waist height, hard shadows, people blurred in the background, natural colours.`
3. `A close-up portrait of a young woman by a rain-streaked café window, soft grey window light from the left, shallow depth of field, warm interior bokeh, shot on 35 mm film with fine grain.`
4. `A mirror selfie of a young woman in a small bedroom, morning light through thin curtains, phone covering part of her face, unmade bed and clothes on a chair behind her, slightly tilted framing.`

## Sources
- Krea, "Explorative prompting with Krea 2": https://www.krea.ai/blog/explorative-prompting-krea-2
- fal, "Krea 2 prompting guide": https://fal.ai/learn/tools/krea-2-prompting-guide
- Our measurement: NAG is a no-op on Krea 2 (2026-11-07).
