# Task: speech from text

**Goal:** a spoken line in a chosen voice: a cloned voice (default), a preset speaker, or a voice described in words. Model: `models/qwen3-tts.md`. Workflow: `qwen3-text-to-speech` (Qwen3-TTS 1.7B).

## Ask if unsure
- What exactly is said, and in which language?
- Whose voice: a reference recording to clone, a preset speaker, or a description?

## Inputs (Voice Clone, the default group)
| Node | Set |
|---|---|
| `Load Audio` | the reference voice: 10–20 s, one speaker, no music |
| `🎭 Qwen3-TTS VoiceClone` | `target_text` (**you write this**), `language`; `ref_text` = the reference's exact words if you have them (then `x_vector_only=false`) |

For a preset speaker or a described voice, switch groups: `--group "Voice Clone=off" --group "Custom_Voice=on"` (or `"Design Voice=on"`), and set that node's `text` and `instruct`.

## Run
```bash
$RUN qwen3-text-to-speech \
  --set "Load Audio.audio=@voice.wav" \
  --set "🎭 Qwen3-TTS VoiceClone.target_text=Ciao, questa è una prova." \
  --set "🎭 Qwen3-TTS VoiceClone.language=Italian"
```
Output: `output/qwen3-text-to-speech/speech` (FLAC).

## Check
- **Listen:** right words, right language, no skipped or repeated words.
- **The voice matches the reference.**
