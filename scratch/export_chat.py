import json
from pathlib import Path
import re

TRANSCRIPT_PATH = Path(r"C:\Users\EG SERIES\.gemini\antigravity-ide\brain\c0673831-f725-4ca2-89d5-314a5cee567c\.system_generated\logs\transcript.jsonl")
OUTPUT_MD = Path(r"c:\Users\EG SERIES\NyayaRoute\NyayaRoute_Chat_History.md")

def clean_content(text: str) -> str:
    # Remove system prompt tags if any
    text = re.sub(r"<USER_REQUEST>(.*?)</USER_REQUEST>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", text, flags=re.DOTALL)
    text = re.sub(r"<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>", "", text, flags=re.DOTALL)
    return text.strip()

def export_transcript():
    if not TRANSCRIPT_PATH.exists():
        print(f"Transcript not found at {TRANSCRIPT_PATH}")
        return

    lines = []
    lines.append("# NyayaRoute — AI Development Chat History\n")
    lines.append("> Complete conversation log of design discussions, architecture decisions, code fixes, and pipeline implementation.\n\n---\n")

    current_user_msg = ""
    
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue

            msg_type = record.get("type", "")
            source = record.get("source", "")
            content = record.get("content", "")

            if not content:
                continue

            cleaned = clean_content(content)
            if not cleaned:
                continue

            # If user message
            if msg_type == "USER_INPUT" or source == "USER_EXPLICIT":
                # Avoid duplicates
                if cleaned != current_user_msg:
                    current_user_msg = cleaned
                    lines.append(f"## 👤 User\n\n{cleaned}\n\n")
            
            # If assistant response
            elif msg_type == "PLANNER_RESPONSE" or source == "MODEL":
                # Skip pure tool calls / internal steps
                if "tool_calls" in record and not cleaned:
                    continue
                # Skip internal thoughts if isolated
                lines.append(f"## 🤖 Assistant\n\n{cleaned}\n\n---\n\n")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported successfully to: {OUTPUT_MD.resolve()}")

if __name__ == "__main__":
    export_transcript()
