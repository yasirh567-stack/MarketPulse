import { useState, type FormEvent } from "react";
import { useSelectedTicker } from "@/hooks/useSelectedTicker";
import { useAssistantQuery } from "@/api/hooks";
import { TickerSearch } from "@/components/TickerSearch";
import { Card } from "@/components/Card";
import { ErrorState, SkeletonBlock } from "@/components/StateViews";

const SUGGESTED_QUESTIONS = [
  "Why is this stock moving?",
  "What are the main risks in the latest news?",
  "Has sentiment become more negative?",
  "Which recent event appears most relevant?",
];

export function AssistantPage() {
  const { ticker, setTicker } = useSelectedTicker();
  const [question, setQuestion] = useState("");
  const askMutation = useAssistantQuery();

  function ask(q: string) {
    setQuestion(q);
    askMutation.mutate({ ticker, question: q });
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (question.trim()) ask(question.trim());
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Market assistant: {ticker}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Ask a question — answers are built entirely from retrieved, cited headlines and stored
            data, never a generative model.
          </p>
        </div>
        <TickerSearch onSelect={setTicker} />
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
          <label htmlFor="assistant-question" className="sr-only">
            Ask a question about {ticker}
          </label>
          <input
            id="assistant-question"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={`Ask about ${ticker}…`}
            className="input flex-1"
          />
          <button
            type="submit"
            disabled={askMutation.isPending || !question.trim()}
            className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-50 dark:bg-white dark:text-slate-900"
          >
            {askMutation.isPending ? "Thinking…" : "Ask"}
          </button>
        </form>
        <div className="mt-3 flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => ask(q)}
              className="rounded-full border border-slate-300 px-3 py-1 text-xs text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              {q}
            </button>
          ))}
        </div>
      </Card>

      {askMutation.isPending && (
        <Card>
          <SkeletonBlock lines={4} />
        </Card>
      )}

      {askMutation.isError && (
        <ErrorState
          title="Couldn't get an answer"
          description={(askMutation.error as Error)?.message}
        />
      )}

      {askMutation.data && (
        <Card>
          <p className="text-xs text-slate-400">
            {new Date().toLocaleString()} ·{" "}
            {askMutation.data.data_sufficient ? "sufficient evidence found" : "limited evidence"}
          </p>
          <p className="mt-2 text-slate-900 dark:text-slate-100">{askMutation.data.answer}</p>
          <p className="mt-3 text-xs italic text-slate-400">{askMutation.data.disclaimer}</p>

          {askMutation.data.citations.length > 0 && (
            <div className="mt-4">
              <h3 className="mb-1 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Citations
              </h3>
              <ul className="space-y-1.5">
                {askMutation.data.citations.map((c, i) => (
                  <li key={i} className="text-sm">
                    {c.url ? (
                      <a
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline"
                      >
                        {c.title}
                      </a>
                    ) : (
                      c.title
                    )}
                    <span className="ml-2 text-xs text-slate-400">
                      ({c.kind}, {new Date(c.published_at).toLocaleDateString()})
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
