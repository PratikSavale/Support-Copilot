#!/usr/bin/env node

/**
 * LLM Code Review Script
 * Calls the Google Gemini API to review a PR diff and outputs structured feedback.
 */

const { GoogleGenerativeAI } = require("@google/generative-ai");
const fs = require("fs");

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

async function runCodeReview() {
  const diff = fs.readFileSync("/tmp/pr_diff.txt", "utf8");
  const prTitle = process.env.PR_TITLE || "Untitled PR";
  const prDescription = process.env.PR_DESCRIPTION || "No description provided";
  const prAuthor = process.env.PR_AUTHOR || "Unknown";
  const baseBranch = process.env.BASE_BRANCH || "main";
  const headBranch = process.env.HEAD_BRANCH || "feature";
  const changedFiles = process.env.CHANGED_FILES || "";
  const isDiffTruncated = diff.length >= 30000;
  const isFilesTruncated = changedFiles.split("\n").filter(Boolean).length >= 30;

  if (!diff.trim()) {
    console.log("No diff found, skipping review.");
    const emptyReview = {
      summary: "No code changes detected in this PR.",
      comments: [],
      overallScore: 10,
      recommendation: "APPROVE",
    };
    fs.writeFileSync("/tmp/review_output.json", JSON.stringify(emptyReview));
    return;
  }

  const systemInstruction = `You are an expert code reviewer with deep knowledge of software engineering best practices, security, performance, and maintainability. Your job is to review pull request diffs and provide actionable, constructive feedback.

Review focus areas (in order of priority):
1. **Security vulnerabilities** - SQL injection, XSS, auth issues, secrets in code, etc.
2. **Bugs & correctness** - Logic errors, off-by-one, null/undefined handling, race conditions
3. **Performance** - N+1 queries, unnecessary computation, memory leaks
4. **Code quality** - Readability, naming, duplication, complexity
5. **Testing** - Missing test coverage for critical paths
6. **Best practices** - Language/framework idioms, SOLID principles

Be concise and actionable. Prioritize high-severity issues. Focus on correctness, security, and performance.
Avoid excessive wordiness in descriptions. If a fix is obvious, keep the suggestion short.

You MUST respond with a JSON object following the provided schema.
Rules:
- overallScore: 8-10 = good, 5-7 = needs minor fixes, 1-4 = needs major fixes
- APPROVE if score >= 8 and no high-severity issues
- REQUEST_CHANGES if score < 6 or any high-severity security/bug issues
- COMMENT otherwise
- Maximum 8-10 comments; focus on the most important issues.
- Omit low-severity style comments unless there are very few real issues.`;

  const userPrompt = `Please review this pull request:

**PR Title:** ${prTitle}
**Author:** ${prAuthor}
**Branch:** ${headBranch} → ${baseBranch}
**Changed Files:**
${changedFiles}

**PR Description:**
${prDescription || "_(none provided)_"}

**Diff:**
\`\`\`diff
${diff}
\`\`\`

Respond ONLY with the JSON review object.`;

  console.log("Calling Gemini API for code review...");
  console.log(`Diff length: ${diff.length} chars`);

  const responseSchema = {
    type: "object",
    properties: {
      summary: { type: "string" },
      overallScore: { type: "integer" },
      recommendation: { type: "string" },
      comments: {
        type: "array",
        items: {
          type: "object",
          properties: {
            title: { type: "string" },
            severity: { type: "string" },
            file: { type: "string" },
            description: { type: "string" },
            suggestion: { type: "string" }
          },
          required: ["title", "severity", "description"]
        }
      }
    },
    required: ["summary", "overallScore", "recommendation", "comments"]
  };

  const model = genAI.getGenerativeModel({
    model: "gemini-2.5-flash",
    systemInstruction,
    generationConfig: {
      responseMimeType: "application/json",
      responseSchema,
      maxOutputTokens: 4096,
      temperature: 0.1,
    },
  });

  const result = await model.generateContent(userPrompt);
  const responseText = result.response.text();

  console.log("Raw response (first 200 chars):", responseText.slice(0, 200) + "...");

  let review;
  try {
    // Robust cleaning: Find the first '{' and last '}' to extract JSON
    const firstBrace = responseText.indexOf("{");
    const lastBrace = responseText.lastIndexOf("}");

    if (firstBrace === -1 || lastBrace === -1) {
      throw new Error("No JSON object found in response");
    }

    let clean = responseText.substring(firstBrace, lastBrace + 1);

    // Remove potential trailing commas before closing braces/brackets
    // This handles cases like: { "a": 1, } or [ 1, 2, ]
    clean = clean.replace(/,\s*([}\]])/g, '$1');

    review = JSON.parse(clean);
  } catch (err) {
    console.error("Failed to parse JSON response:", err.message);
    console.error("Full response for debugging:", responseText);
    review = {
      summary: "The AI reviewer encountered an issue processing the diff. Please review manually.",
      comments: [],
      overallScore: 5,
      recommendation: "COMMENT",
    };
  }

  review.overallScore = Math.max(1, Math.min(10, Number(review.overallScore) || 5));
  review.recommendation = ["APPROVE", "REQUEST_CHANGES", "COMMENT"].includes(review.recommendation)
    ? review.recommendation
    : "COMMENT";
  review.comments = (review.comments || []).slice(0, 10);

  review.isTruncated = isDiffTruncated || isFilesTruncated;

  fs.writeFileSync("/tmp/review_output.json", JSON.stringify(review, null, 2));
  console.log(`Review complete. Score: ${review.overallScore}/10, Recommendation: ${review.recommendation}`);
  console.log(`Found ${review.comments.length} comment(s).`);
}

runCodeReview().catch((err) => {
  console.error("Code review failed:", err);
  const fallback = {
    summary: `Review failed: ${err.message}. Please review this PR manually.`,
    comments: [],
    overallScore: 5,
    recommendation: "COMMENT",
  };
  fs.writeFileSync("/tmp/review_output.json", JSON.stringify(fallback));
  process.exit(1);
});
