# Support-Copilot Cross-Question Prep

## Golden Answer

If judges ask how we calculated the numbers, say:

> We did not present these as final production results. We used credible external benchmarks from Gartner, McKinsey, Freshworks, and Salesforce, then built a conservative planning model for a 100-ticket/day L2 queue. The actual numbers will be validated in a two-week pilot using our own ticket history, resolution rate, escalation rate, first response time, and manual effort saved.

This answer is honest, defensible, and mature.

## How We Calculated The 100-Ticket Model

Base assumption:

- 100 L2 tickets per day
- 22 business days per month
- 2,200 tickets per month

Direct resolution assumption:

- We assumed 45% direct AI resolution for known/documented repeat issues.
- 2,200 monthly tickets x 45% = 990 tickets avoided manually.

Time saved assumption:

- We assumed each manual L2 ticket takes around 30 minutes of human effort.
- 990 avoided tickets x 30 minutes = 29,700 minutes.
- 29,700 minutes / 60 = 495 hours saved per month.

FTE capacity:

- 1 full-time person is roughly 160 hours/month.
- 495 hours / 160 = about 3.1 FTE capacity unlocked.

Cost estimate:

- If support cost is $35/hour fully loaded:
- 495 hours x $35 = $17,325/month.
- $17,325 x 12 = $207,900/year.

## If They Ask: “Is 45% Resolution Realistic?”

Answer:

> We chose 45% as a conservative pilot target for documented repeat issues, not all issues. Gartner predicts agentic AI can resolve 80% of common customer service issues by 2029, and Freshworks reports AI/chatbot deflection and resolution-time improvements in real deployments. Since L2 issues are more complex, we intentionally did not assume 80%. We used 45% to stay realistic for a first pilot.

## If They Ask: “Why Not Claim 80%?”

Answer:

> 80% is Gartner’s forecast for common customer service issues by 2029. L2 technical support is more complex, so we use that as a market direction, not as our immediate pilot target. Our pilot target is lower: 30%+ manual L2 volume reduction and 45%+ direct resolution for documented repeat issues.

## If They Ask: “How Will You Prove This Works?”

Answer:

> We will compare before and after metrics on the same type of ticket queue. The KPIs are first response time, average resolution time, direct AI resolution rate, escalation rate, L2 manual-touch reduction, and quality of Jira handoff. We can also audit AI answers against source documents to make sure the assistant is grounded.

## If They Ask: “What If AI Gives Wrong Answers?”

Answer:

> The system is designed with confidence-based routing. If confidence is high, it answers with source-backed context. If details are missing, it asks clarifying questions. If it cannot find a reliable answer, it escalates to Jira instead of guessing. That is why this is safer than a generic chatbot.

## If They Ask: “How Is This Different From ChatGPT?”

Answer:

> ChatGPT is general. Support-Copilot is connected to our support workflow. It uses our documentation through RAG, applies confidence gates, stores chat history, creates Jira tickets with structured fields, and gives admins analytics about resolution rate, escalation rate, knowledge gaps, and common issue patterns.

## If They Ask: “Will This Replace L2 Engineers?”

Answer:

> No. It removes repeatable work from L2 engineers. The goal is to let L2 focus on high-severity incidents, root cause analysis, product defects, and engineering collaboration. AI handles known issues, documentation lookup, clarification, and ticket preparation.

## If They Ask: “How Does It Help 24/7?”

Answer:

> Today, off-hours tickets may wait in a queue. With Support-Copilot, every ticket gets immediate triage. Known issues can be solved instantly, vague issues get clarification questions, and unknown issues are escalated with a complete summary before the human team starts work.

## If They Ask: “What Data Does It Need?”

Answer:

> It needs product documentation, troubleshooting runbooks, FAQs, known error guides, and optionally historical resolved tickets. The better the knowledge base, the higher the direct resolution rate. The system also identifies repeated escalations, which tells us where documentation is missing.

## If They Ask: “How Do You Avoid Hallucination?”

Answer:

> The RAG pipeline retrieves trusted knowledge chunks first. The confidence service checks retrieval quality, relevance, and completeness. If the answer is not sufficiently supported, the assistant asks follow-up questions or escalates. We also prevent fallback or hallucinated answers from polluting the knowledge base.

## If They Ask: “Why Is Jira Integration Important?”

Answer:

> Escalation is where many AI support tools fail. They may hand off a raw chat transcript and make the agent restart investigation. Support-Copilot creates a structured Jira ticket with summary, severity, product module, environment, error messages, steps to reproduce, troubleshooting attempted, and source references. That saves L2 time even when AI cannot solve the issue.

## If They Ask: “What Are The Main Risks?”

Answer:

> The main risks are poor documentation, low-quality historical tickets, and incorrect confidence thresholds. Our mitigation is to start with high-quality docs, measure answer quality, tune confidence thresholds, and use human review for escalated or low-confidence issues.

## Source Links

- Gartner: https://www.gartner.com/en/newsroom/press-releases/2025-03-05-gartner-predicts-agentic-ai-will-autonomously-resolve-80-percent-of-common-customer-service-issues-without-human-intervention-by-20290
- McKinsey: https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/The-economic-potential-of-generative-AI-The-next-productivity-frontier
- Freshworks 2024: https://www.freshworks.com/theworks/customer-experience/freshworks-customer-service-benchmark-report-2024/
- Freshworks 2025: https://www.freshworks.com/theworks/customer-experience/freshworks-20205-cx-benchmark-thriving-with-ai/
- Salesforce: https://www.salesforce.com/news/stories/customer-service-statistics-2024/
