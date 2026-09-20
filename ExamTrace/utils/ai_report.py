"""
LangChain-based AI Integrity Report Agent Module.
Converts structured session proctoring data into concise, factual natural language summaries
using LangChain + Google Gemini LLM with safe deterministic offline fallback.
"""

import os
from dotenv import load_dotenv
from config import Config
from utils.scoring import evaluate_session_integrity, get_risk_level, calculate_face_presence_ratio

load_dotenv()

# Strict factual prompt template for LangChain
REPORT_PROMPT_TEMPLATE = """You are an objective, professional AI Integrity Reporting Agent for an Online Examination Monitoring Platform.
Your task is to generate a concise, factual integrity evaluation summary for an invigilator based strictly on the structured monitoring data provided below.

EXAMINATION METRICS:
- Exam Duration: {duration_minutes} minutes ({duration_seconds} seconds)
- Tab Switches Recorded: {tab_switches}
- Focus Loss Events: {focus_losses}
- Copy Attempts: {copy_attempts}
- Paste Attempts: {paste_attempts}
- Right Click Attempts: {right_clicks}
- Keyboard Shortcuts Used: {shortcuts}
- Face Missing Count: {face_missing_count}
- Multiple Faces Count: {multiple_face_count}
- Total Face Absent Duration: {face_absent_seconds} seconds
- Face Presence Ratio: {face_presence_ratio}%
- Academic Score: {score_info}
- Final Integrity Score: {integrity_score}/100
- Risk Classification: {risk_level}

STRICT GUIDELINES:
1. Summarize ONLY the provided observations and metrics.
2. DO NOT invent events, numbers, or external evidence.
3. DO NOT change the integrity score or risk classification.
4. DO NOT assert that cheating definitely occurred; state recorded events objectively.
5. Format the output clearly into:
   - Summary Statement
   - Monitored Behavior Highlights
   - Invigilator Recommendation

Generate the concise integrity report now:"""


def _generate_fallback_summary(metrics, score_info=""):
    """
    Deterministic rule-based fallback generator used when LLM API is unreachable or unconfigured.
    Ensures safe, crash-free operation in all testing and deployment environments.
    """
    suspicious = []
    if metrics["face_missing_count"] > 0:
        suspicious.append(f"Face absent {metrics['face_missing_count']} time(s) totaling ~{metrics['face_absent_seconds']}s.")
    if metrics["multiple_face_count"] > 0:
        suspicious.append(f"Multiple faces detected {metrics['multiple_face_count']} time(s).")
    if metrics["tab_switches"] > 0:
        suspicious.append(f"Candidate switched browser tabs {metrics['tab_switches']} time(s).")
    if metrics["focus_losses"] > 0:
        suspicious.append(f"Exam window lost focus {metrics['focus_losses']} time(s).")
    if metrics["right_clicks"] > 0:
        suspicious.append(f"Right click attempted {metrics['right_clicks']} time(s).")
    if metrics["copy_attempts"] > 0:
        suspicious.append(f"Copy operation attempted {metrics['copy_attempts']} time(s).")
    if metrics["paste_attempts"] > 0:
        suspicious.append(f"Paste operation attempted {metrics['paste_attempts']} time(s).")
    if metrics["shortcuts"] > 0:
        suspicious.append(f"Restricted shortcuts attempted {metrics['shortcuts']} time(s).")

    if not suspicious:
        activity_text = "No suspicious proctoring events were detected during the examination."
    else:
        activity_text = "\n".join("- " + item for item in suspicious)

    risk = metrics["risk_level"]
    if risk == "Low":
        rec = "Candidate behavior was compliant with proctoring guidelines. Normal evaluation recommended."
    elif risk == "Medium":
        rec = "Moderate proctoring events recorded. Review flagged timestamps before finalizing results."
    else:
        rec = "Significant anomalies recorded. Comprehensive manual review of session logs and evidence required."

    score_line = f"\nAcademic Score: {score_info}" if score_info else ""

    return f"""Candidate maintained face presence for {metrics['face_presence_ratio']}% of the examination session.{score_line}
The final integrity score is {metrics['integrity_score']}/100, resulting in a {risk} risk classification.

Monitored Observations:
{activity_text}

Recommendation:
{rec}"""


def generate_ai_summary(monitor_or_dict, score=None, percentage=None):
    """
    Generate an AI Integrity Summary for a session using LangChain + LLM,
    falling back seamlessly to rule-based generation if unavailable.
    """
    # Extract structured metrics from ExamMonitor object or dictionary
    if hasattr(monitor_or_dict, "get_metrics_dict"):
        metrics = monitor_or_dict.get_metrics_dict()
    elif isinstance(monitor_or_dict, dict):
        metrics = monitor_or_dict
    else:
        # Generic fallback
        metrics = evaluate_session_integrity()

    score_info = f"{score} marks ({percentage}%)" if score is not None and percentage is not None else ""
    duration_secs = int(metrics.get("duration_seconds", 1800))
    duration_mins = max(1, duration_secs // 60)

    # Attempt LangChain LLM generation if API Key is configured
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            from langchain_core.prompts import PromptTemplate
            from langchain_google_genai import ChatGoogleGenerativeAI

            prompt = PromptTemplate(
                template=REPORT_PROMPT_TEMPLATE,
                input_variables=[
                    "duration_minutes",
                    "duration_seconds",
                    "tab_switches",
                    "focus_losses",
                    "copy_attempts",
                    "paste_attempts",
                    "right_clicks",
                    "shortcuts",
                    "face_missing_count",
                    "multiple_face_count",
                    "face_absent_seconds",
                    "face_presence_ratio",
                    "score_info",
                    "integrity_score",
                    "risk_level"
                ]
            )

            llm = ChatGoogleGenerativeAI(
                model=Config.GEMINI_MODEL,
                google_api_key=api_key,
                temperature=0.2,
                max_output_tokens=1000,
                timeout=10,
                max_retries=1
            )

            chain = prompt | llm
            response = chain.invoke({
                "duration_minutes": duration_mins,
                "duration_seconds": duration_secs,
                "tab_switches": metrics.get("tab_switches", 0),
                "focus_losses": metrics.get("focus_losses", 0),
                "copy_attempts": metrics.get("copy_attempts", 0),
                "paste_attempts": metrics.get("paste_attempts", 0),
                "right_clicks": metrics.get("right_clicks", 0),
                "shortcuts": metrics.get("shortcuts", 0),
                "face_missing_count": metrics.get("face_missing_count", 0),
                "multiple_face_count": metrics.get("multiple_face_count", 0),
                "face_absent_seconds": metrics.get("face_absent_seconds", 0),
                "face_presence_ratio": metrics.get("face_presence_ratio", 100.0),
                "score_info": score_info or "Not graded",
                "integrity_score": metrics.get("integrity_score", 100),
                "risk_level": metrics.get("risk_level", "Low")
            })

            if isinstance(response.content, list):
                content = "\n".join(
                    item if isinstance(item, str) else item.get("text", "")
                    for item in response.content
                )
            elif isinstance(response.content, str):
                content = response.content
            else:
                content = str(response.content)

            if content and len(content.strip()) > 20:
                return content.strip()

        except Exception as e:
            print(f"[AI_REPORT] LangChain LLM warning (using deterministic fallback): {e}")

    # Deterministic fallback
    return _generate_fallback_summary(metrics, score_info)