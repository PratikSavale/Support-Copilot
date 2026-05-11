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
1. **Security vulnerabilities** – SQL injection, XSS, auth issues, secrets in code, etc.
2. **Bugs & correctness** – Logic errors, off-by-one, null/undefined handling, race conditions
3. **Performance** – N+1 queries, unnecessary computation, memory leaks
4. **Code quality** – Readability, naming, duplication, complexity
5. **Testing** – Missing test coverage for critical paths
6. **Best practices** – Language/framework idioms, SOLID principles

Be concise and actionable. Prioritize high-severity issues. Don't nitpick style unless it significantly impacts readability.

You MUST respond with ONLY valid JSON — no markdown fences, no preamble — in this exact schema:
{
  "summary": "2-4 sentence overall assessment of the PR",
  "overallScore": <integer 1-10>,
  "recommendation": "<APPROVE|REQUEST_CHANGES|COMMENT>",
  "comments": [
    {
      "title": "Short title of the issue",
      "severity": "<high|medium|low>",
      "file": "path/to/file.js or null",
      "description": "Clear explanation of the issue",
      "suggestion": "Concrete fix or improvement (optional)"
    }
  ]
}

Rules:
- overallScore: 8-10 = good, 5-7 = needs minor fixes, 1-4 = needs major fixes
- APPROVE if score >= 8 and no high-severity issues
- REQUEST_CHANGES if score < 6 or any high-severity security/bug issues
- COMMENT otherwise
- Maximum 10 comments; focus on the most important issues
- Omit low-severity style comments unless there are very few real issues`;

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

  const model = genAI.getGenerativeModel({
    model: "gemini-flash-latest",
    systemInstruction,
    generationConfig: {
      responseMimeType: "application/json",
      maxOutputTokens: 2048,
      temperature: 0.2,
    },
  });

  const result = await model.generateContent(userPrompt);
  const responseText = result.response.text();

  console.log("Raw response:", responseText.slice(0, 200) + "...");

  let review;
  try {
    const clean = responseText
      .replace(/^```json\s*/i, "")
      .replace(/```\s*$/, "")
      .trim();
    review = JSON.parse(clean);
  } catch (err) {
    console.error("Failed to parse JSON response:", err.message);
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
  process.exit(0);
});
