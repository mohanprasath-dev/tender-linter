# Fact-gathering prompt (paste into a search-enabled chat)

```
You are a researcher. Use only each provider's official documentation, pricing page and terms. Do not rely on memory. If a fact is not on an official page, write NOT FOUND. No em dashes.
Providers: Groq, Google Gemini (AI Studio / Gemini API), plus any other provider that has a free API tier today.
For each provider give: free tier available (yes/no); model names currently offered on it; requests per minute and per day and tokens per minute limits for each model I could use; whether JSON or structured output is supported; documented support for Hindi; whether free-tier inputs may be used to improve models or retained, quoting at most 15 words; any stated deprecation dates; sign-up requirements for students in India; the page URL and access date for each fact.
Finish with a table, then list everything you could not verify.
```

Log the results in `docs/open-verification.md` and only then fill provider config. Do not trust any limit, model name or term until it has a URL and access date.
