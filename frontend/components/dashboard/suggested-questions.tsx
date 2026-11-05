"use client";

import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  GraduationCap,
  Trophy,
  Users,
} from "lucide-react";

export type SuggestedQuestion = {
  id: string;
  prompt: string;
  title: string;
  subtitle: string;
  icon: LucideIcon;
};

export const SUGGESTED_QUESTIONS: SuggestedQuestion[] = [
  {
    id: "blocks",
    prompt: "How many active students are in each block in 2024-25?",
    title: "Students by block",
    subtitle: "Active headcount per block this year",
    icon: Users,
  },
  {
    id: "sports",
    prompt: "Top 5 sports by participation this year",
    title: "Sports participation",
    subtitle: "Most popular activities ranked",
    icon: Trophy,
  },
  {
    id: "exams",
    prompt: "Average exam score by grade",
    title: "Exam performance",
    subtitle: "Mean scores across grades",
    icon: GraduationCap,
  },
  {
    id: "trends",
    prompt: "Show monthly student attendance trend for this academic year",
    title: "Attendance trends",
    subtitle: "Month-over-month attendance",
    icon: BarChart3,
  },
];

type SuggestedQuestionsProps = {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
};

export function SuggestedQuestions({ onSelect, disabled }: SuggestedQuestionsProps) {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <p className="mb-3 text-center text-xs font-medium uppercase tracking-wider text-muted-foreground">
        Suggested questions
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {SUGGESTED_QUESTIONS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              disabled={disabled}
              onClick={() => onSelect(item.prompt)}
              className="suggestion-card group disabled:pointer-events-none disabled:opacity-50"
            >
              <span className="mb-3 inline-flex size-10 items-center justify-center rounded-lg border border-border bg-background text-primary">
                <Icon className="size-5" aria-hidden />
              </span>
              <span className="block text-sm font-medium text-foreground group-hover:text-primary">
                {item.title}
              </span>
              <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
                {item.subtitle}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
