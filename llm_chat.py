"""LLM-powered chat for Spotify listening data — powered by Google Gemini."""

import io
import traceback
from contextlib import redirect_stdout

import pandas as pd
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are a Spotify data analyst. You answer questions about a user's listening history stored in a pandas DataFrame called `df`.

## DataFrame Schema
Columns:
- played_at (datetime, tz=Africa/Harare): when the track was played
- artist_name (str): artist name
- track_name (str): track name
- minutes_played (float): minutes played for that stream
- ms_played (int): milliseconds played
- year (int): year extracted from played_at
- month (str): "YYYY-MM" format
- date (date): date only
- hour (int): 0-23
- day_of_week (str): e.g. "Monday"
- is_skip (bool): True if ms_played < 30000
- play (int): always 1 (for counting)

## Rules
1. Write a short Python snippet using `df` that computes the answer, then print a human-friendly result.
2. Only use pandas/numpy. The variable `df` is already available.
3. Wrap your code in ```python ... ``` block.
4. Always end with print() statements that give a clear, conversational answer.
5. Keep code minimal. No plots.
6. If the question is vague or a greeting, respond conversationally (no code needed) and suggest example questions.

## Data Summary
{summary}
"""


def build_summary(df: pd.DataFrame) -> str:
    top_artists = df.groupby("artist_name")["minutes_played"].sum().nlargest(10)
    top_tracks  = df.groupby("track_name")["minutes_played"].sum().nlargest(10)
    return f"""- Rows: {len(df):,}
- Date range: {df['played_at'].min()} to {df['played_at'].max()}
- Years: {sorted(df['year'].unique().tolist())}
- Unique artists: {df['artist_name'].nunique():,}
- Unique tracks: {df['track_name'].nunique():,}
- Total hours: {df['minutes_played'].sum()/60:,.1f}
- Skip rate: {df['is_skip'].mean()*100:.1f}%
- Top 10 artists by minutes: {dict(top_artists.round(1))}
- Top 10 tracks by minutes: {dict(top_tracks.round(1))}"""


def extract_code(text: str) -> str | None:
    if "```python" in text:
        return text.split("```python")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return None


def run_query(code: str, df: pd.DataFrame) -> str:
    buf = io.StringIO()
    local_ns = {"df": df, "pd": pd}
    try:
        with redirect_stdout(buf):
            exec(code, {"__builtins__": {}}, local_ns)
        output = buf.getvalue().strip()
        return output if output else "Query executed but produced no output."
    except Exception:
        return f"Error running query:\n{traceback.format_exc()}"


def chat(query: str, df: pd.DataFrame, history: list, api_key: str, model: str = "gemini-2.0-flash-lite") -> str:
    client  = genai.Client(api_key=api_key)
    summary = build_summary(df)
    system  = SYSTEM_PROMPT.format(summary=summary)

    # Build conversation history in Gemini format
    gemini_history = []
    for msg in history[-10:]:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    gemini_history.append(types.Content(role="user", parts=[types.Part(text=query)]))

    resp   = client.models.generate_content(
        model=model,
        contents=gemini_history,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2,
            max_output_tokens=1024,
        ),
    )
    answer = resp.text

    code = extract_code(answer)
    if code:
        return run_query(code, df)
    return answer
