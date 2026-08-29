import {
  BookMarked,
  Sigma,
  GitBranch,
  Wrench,
  ListChecks,
  AlertTriangle,
  Puzzle,
} from "lucide-react";

// One friendly identity per generation category, used on tags, the
// coverage chart, and the trail view. Keys MUST match the backend's
// CardType enum exactly — only the label/color/icon are kid-friendly.
export const CARD_TYPES = {
  definition: { label: "Word Power", icon: BookMarked, color: "#3EC6E0", dim: "#DEF7FC" },
  formula: { label: "Magic Formula", icon: Sigma, color: "#9B6BFF", dim: "#EFE5FF" },
  relationship: { label: "How Things Connect", icon: GitBranch, color: "#FFC93C", dim: "#FFF3D2" },
  method: { label: "Steps To Follow", icon: Wrench, color: "#FF8A3D", dim: "#FFEADA" },
  worked_example: { label: "Try It Out", icon: ListChecks, color: "#5FD36B", dim: "#E5F9E6" },
  misconception: { label: "Watch Out!", icon: AlertTriangle, color: "#FF6FA5", dim: "#FFE3EE" },
  edge_case: { label: "Tricky Bit", icon: Puzzle, color: "#3E9CE0", dim: "#E4F1FC" },
};

export const CARD_TYPE_ORDER = Object.keys(CARD_TYPES);

export function cardTypeMeta(type) {
  return CARD_TYPES[type] || { label: type, icon: BookMarked, color: "#9B6BFF", dim: "#EFE5FF" };
}

export const DIFFICULTY = {
  easy: { label: "Easy Peasy", color: "#5FD36B" },
  medium: { label: "Medium", color: "#FFC93C" },
  hard: { label: "Big Brain", color: "#FF6FA5" },
};

export function difficultyMeta(d) {
  return DIFFICULTY[d] || { label: d, color: "#9B6BFF" };
}
