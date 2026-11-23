# Qwen3-TTS: how to prompt it

Used by: `speech-text-to-speech`. The workflow has three modes as groups: **Voice Clone** (on by default), **Custom Voice** and **Design Voice**.

- **Voice Clone:** speaks `target_text` in the voice of a reference recording (`Load Audio`).
  - `language`: the language of the text.
  - `x_vector_only = true`: no transcript of the reference is needed. Set it false and fill `ref_text` with the reference's exact words for a closer match.
  - Use a clean reference of 10–20 s: one speaker, no music.
- **Custom Voice:** a preset `speaker` (Aiden, Dylan, Eric, Serena, …) plus an optional `instruct` for the tone ("calm, slow, warm").
- **Design Voice:** no reference. `instruct` describes the voice in plain words: sex and age, pitch, pace, energy, emotion, accent ("a young woman, light and bright voice, fast and playful, slight Italian accent").

**Writing `target_text`:**
- Write what is said, exactly as it should sound.
- Punctuation sets the pauses: commas for short ones, full stops for longer ones.
- Write numbers and abbreviations the way they're read ("twenty twenty-six", not "2026").
- One language per run, matching `language`.
