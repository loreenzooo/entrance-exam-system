# Figma Make kit

Two files that describe the whole product so Figma Make can rebuild it.

| File | What it is |
|---|---|
| `figma-make-prompt.md` | The prompt: product description, every screen with layout, exact copy, component states, behaviour and responsive rules. |
| `design-tokens.json` | Colours, fonts, radii, shadows, spacing, status badge colours. |

## How to use it

1. Open **Figma Make** and create a new file.
2. Paste the contents of `figma-make-prompt.md` as the first prompt.
3. Attach your captured screens as reference images — the kiosk (home, face capture, register + consent modal, batch selection, confirmation, time-in result) and the admin (login, dashboard, batches, attendance). The prompt describes them, but the images keep proportions and spacing faithful.
4. If it drifts, follow up with just the section you care about ("use the Component states section exactly", "make the kiosk home a 50/50 split").

The token file can be pasted alongside the prompt, or used to set up Figma variables (colour, radius, shadow) before generating.

## Notes

- The split-screen pages are **50/50**, with a 280px side panel only on the kiosk step pages.
- Headings are Source Serif 4; everything else is Inter.
- There is no "Late" status — Present, Not yet timed in, Absent.
- Buttons/inputs in the prompt list their hover and focus values, so the generated frames can be turned into component variants.
