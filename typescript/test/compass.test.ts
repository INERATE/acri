// Mirrors tests/test_compass.py's five cases exactly -- same fixture, same
// queries -- so behavior parity with the Python resolver is verified, not
// assumed.

import { test } from "node:test";
import assert from "node:assert/strict";
import { index, type Tool } from "../src/corpus.js";
import { resolve } from "../src/compass.js";

function corpus() {
  const tools: Tool[] = [
    { name: "github_get_pull_request", description: "fetch pull request details from github by number" },
    { name: "github_merge_pull_request", description: "merge an approved pull request into the default branch" },
    { name: "postgres_query", description: "execute sql against a postgres database table" },
    { name: "weather_forecast", description: "fetch forecast temperature for a city location" },
  ];
  return index(tools);
}

test("resolve excludes tools with no shared term", () => {
  const resolved = resolve("merge the github pull request", corpus(), 4);
  const names = new Set(resolved.map((r) => r.tool.name));
  assert.deepEqual(names, new Set(["github_get_pull_request", "github_merge_pull_request"]));
});

test("resolve ranks the stronger match first", () => {
  const resolved = resolve("merge the github pull request", corpus(), 4);
  assert.equal(resolved[0].tool.name, "github_merge_pull_request");
});

test("resolve confidence is relative to best match", () => {
  const resolved = resolve("merge the github pull request", corpus(), 4);
  assert.equal(resolved[0].score, 1.0);
  assert.ok(resolved.every((r) => r.score > 0 && r.score <= 1.0));
  const sorted = [...resolved].sort((a, b) => b.score - a.score);
  assert.deepEqual(resolved, sorted);
});

test("resolve returns nothing for pure noise", () => {
  assert.deepEqual(resolve("xyzzy plugh", corpus(), 5), []);
});

test("resolve respects k", () => {
  assert.equal(resolve("pull request", corpus(), 1).length, 1);
});
