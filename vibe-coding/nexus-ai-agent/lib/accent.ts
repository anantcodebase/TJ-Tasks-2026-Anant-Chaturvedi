import type { AccentName } from "./types";

const ACCENT_ALIASES: Array<[AccentName, RegExp]> = [
  ["lime", /\b(?:lime|green)\b/i],
  ["blue", /\bblue\b/i],
  ["violet", /\b(?:violet|purple)\b/i],
  ["cyan", /\b(?:cyan|teal)\b/i],
  ["red", /\bred\b/i],
  ["orange", /\borange\b/i],
  ["yellow", /\byellow\b/i],
  ["pink", /\bpink\b/i],
];

export function detectAccentCommand(text: string): AccentName | null {
  const command = /\b(?:make|change|set|use|apply|switch|give|turn|choose|pick)\b/i.test(text) &&
    /\b(?:accent|accents|color|colors|colour|colours|theme|dashboard|interface|ui|buttons?|everything)\b/i.test(text);
  const directColorCommand = /\b(?:use|choose|pick)\s+(?:an?\s+)?(?:lime|green|blue|violet|purple|cyan|teal|red|orange|yellow|pink)\b/i.test(text);
  if (!command && !directColorCommand) return null;
  return ACCENT_ALIASES.find(([, pattern]) => pattern.test(text))?.[0] ?? null;
}
