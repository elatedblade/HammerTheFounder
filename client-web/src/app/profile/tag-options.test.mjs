import assert from "node:assert/strict";
import test from "node:test";
import { appendTagValue, getTagOptions, tagInputIssue } from "./tag-options.ts";
import { ROLE_GROUPS, ROLE_SUGGESTIONS, LOCATION_SUGGESTIONS } from "./profile-suggestions.ts";

test("role suggestions cover different professions without restricting custom titles", () => {
  assert.ok(Object.keys(ROLE_GROUPS).length >= 12);
  assert.ok(ROLE_SUGGESTIONS.length >= 250);
  for (const query of ["nurse", "teacher", "electrician", "accountant", "chef", "engineer", "lawyer"]) {
    assert.ok(getTagOptions(query, [], ROLE_SUGGESTIONS).matchingCount > 0, query);
  }
  const custom = "Senior Marine Robotics Strategist";
  assert.deepEqual(appendTagValue([], custom), [custom]);
  assert.deepEqual(getTagOptions(custom, [], ROLE_SUGGESTIONS).options[0], { value: custom, custom: true });
});

test("locations include global choices and preserve commas and unlisted places", () => {
  assert.ok(LOCATION_SUGGESTIONS.length >= 300);
  for (const query of ["India", "London", "Toronto", "Singapore", "Remote"]) {
    assert.ok(getTagOptions(query, [], LOCATION_SUGGESTIONS).matchingCount > 0, query);
  }
  assert.deepEqual(appendTagValue([], "  Pune, India  "), ["Pune, India"]);
  const custom = "My village, Example district";
  assert.deepEqual(appendTagValue([], custom), [custom]);
});

test("browsing and filtering are bounded without hiding exact matches", () => {
  const { options, matchingCount } = getTagOptions("", [], ROLE_SUGGESTIONS);
  assert.equal(options.length, 50);
  assert.equal(matchingCount, ROLE_SUGGESTIONS.length);
  const suggestions = [...Array.from({ length: 80 }, (_, i) => `Engineer ${i}`), "Engineer"];
  assert.deepEqual(getTagOptions("Engineer", [], suggestions).options[0], { value: "Engineer", custom: false });
  const partial = getTagOptions("Engineer", [], ["Software Engineer"]);
  assert.deepEqual(partial.options[0], { value: "Engineer", custom: true });
});

test("existing values, duplicates, and API limits are respected", () => {
  const saved = ["Unlisted legacy role"];
  assert.deepEqual(appendTagValue(saved, "New custom role"), ["Unlisted legacy role", "New custom role"]);
  assert.deepEqual(saved, ["Unlisted legacy role"]);
  assert.equal(appendTagValue(saved, "unlisted LEGACY role"), saved);
  assert.equal(getTagOptions("", ["software engineer"], ["Software Engineer", "Software Engineer"]).matchingCount, 0);
  const full = Array.from({ length: 10 }, (_, i) => `Role ${i}`);
  assert.equal(appendTagValue(full, "Another role"), full);
  assert.match(tagInputIssue(full, "Another role"), /up to 10/);
  assert.equal(appendTagValue(saved, "x".repeat(101)), saved);
  assert.match(tagInputIssue([], "x".repeat(101)), /100/);
  assert.equal(appendTagValue(saved, "   "), saved);
});

test("catalog labels are unique and fit backend entry limits", () => {
  for (const catalog of [ROLE_SUGGESTIONS, LOCATION_SUGGESTIONS]) {
    assert.equal(new Set(catalog.map(value => value.toLowerCase())).size, catalog.length);
    assert.ok(catalog.every(value => value.trim() && value.length <= 100));
  }
});
