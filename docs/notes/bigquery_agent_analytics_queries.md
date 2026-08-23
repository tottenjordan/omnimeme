# BigQuery Agent Analytics: Telemetry & User Feedback SQL Queries

This document contains production SQL queries for analyzing OmniMeme telemetry, latency distribution, prompt expansion quality, and user feedback ratings in BigQuery (`hybrid-vertex:omnimeme_telemetry`).

---

## 1. P95 Latency & Generation Count by Interface Mode

```sql
SELECT
  JSON_VALUE(text_payload, "$.generation_mode") AS generation_mode,
  COUNT(*) AS total_generations,
  APPROX_QUANTILES(timestamp_diff(receive_timestamp, insert_timestamp, MILLISECOND), 100)[OFFSET(95)] AS p95_latency_ms
FROM
  `hybrid-vertex.omnimeme_telemetry.completions_view`
GROUP BY
  generation_mode
ORDER BY
  total_generations DESC;
```

---

## 2. Average User Feedback Rating & Category Breakdown

```sql
SELECT
  JSON_VALUE(json_payload, "$.feedback_type") AS feedback_type,
  COUNT(*) AS total_feedback_count,
  ROUND(AVG(CAST(JSON_VALUE(json_payload, "$.rating") AS INT64)), 2) AS avg_rating_stars
FROM
  `hybrid-vertex.omnimeme_telemetry.completions_view`
WHERE
  text_payload LIKE "%User Feedback received%"
GROUP BY
  feedback_type
ORDER BY
  avg_rating_stars DESC;
```

---

## 3. High-Rated Directing Prompts (5-Star Quality Harvesting)

```sql
SELECT
  JSON_VALUE(json_payload, "$.interaction_thread_id") AS thread_id,
  JSON_VALUE(json_payload, "$.prompt") AS raw_prompt,
  JSON_VALUE(json_payload, "$.comment") AS user_comment,
  timestamp
FROM
  `hybrid-vertex.omnimeme_telemetry.completions_view`
WHERE
  JSON_VALUE(json_payload, "$.rating") = "5"
ORDER BY
  timestamp DESC
LIMIT 50;
```
