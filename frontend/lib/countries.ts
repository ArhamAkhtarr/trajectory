export interface Country {
  code: string;
  name: string;
  flag: string;
}

export const COUNTRIES: Country[] = [
  { code: "us", name: "United States", flag: "🇺🇸" },
  { code: "gb", name: "United Kingdom", flag: "🇬🇧" },
  { code: "ca", name: "Canada", flag: "🇨🇦" },
  { code: "de", name: "Germany", flag: "🇩🇪" },
  { code: "pk", name: "Pakistan", flag: "🇵🇰" },
  { code: "in", name: "India", flag: "🇮🇳" },
  { code: "au", name: "Australia", flag: "🇦🇺" },
  { code: "fr", name: "France", flag: "🇫🇷" },
  { code: "nl", name: "Netherlands", flag: "🇳🇱" },
  { code: "sg", name: "Singapore", flag: "🇸🇬" },
  { code: "ae", name: "United Arab Emirates", flag: "🇦🇪" },
  { code: "br", name: "Brazil", flag: "🇧🇷" },
  { code: "jp", name: "Japan", flag: "🇯🇵" },
];
