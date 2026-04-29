# main.py
import json
import re
from crewai import Crew, Process, Task
from customer_support_agent.crew import (
    GlowmartSupportCrew,
)

# Quick rule-based guardrail - no LLM cost
GREETINGS = {"hi", "hello", "hey", "hola", "yo", "sup", "howdy", "good morning", "good afternoon", "good evening", "gm", "gn"}
SUPPORT_KEYWORDS = {
    "order", "return", "refund", "shipping", "delivery", "track", "payment", "cancel",
    "broken", "damaged", "wrong", "item", "product", "price", "discount", "offer",
    "account", "login", "password", "email", "help", "support", "complaint",
    "policy", "warranty", "exchange", "money", "pay", "buy", "purchase", "shop",
    "issue", "problem", "question", "query", "assistance", "customer"
}


def is_valid_support_query(message: str) -> tuple[bool, str]:
    """
    Guardrail: Check if message is a valid support query.
    Returns (is_valid, fallback_response).
    """
    msg_lower = message.lower().strip()
    words = msg_lower.split()

    # Check 1: Empty or too short
    if len(words) < 2:
        return False, "Hello! 👋 I'm here to help with your Glowmart orders, returns, shipping, or any store-related questions. How can I assist you today?"

    # Check 2: Pure greeting (single word greetings)
    if msg_lower in GREETINGS or (len(words) == 1 and msg_lower in GREETINGS):
        return False, "Hello! 👋 Welcome to Glowmart Support. I can help you with:\n\n- Order tracking & status\n- Returns & refunds\n- Shipping & delivery\n- Payment issues\n- Product inquiries\n\nWhat can I help you with today?"

    # Check 3: Has support keywords?
    msg_words = set(re.findall(r'\b\w+\b', msg_lower))
    if msg_words & SUPPORT_KEYWORDS:
        return True, ""

    # Check 4: Contains question words
    question_words = {"what", "how", "when", "where", "why", "which", "who", "can", "do", "is", "are", "will", "does"}
    if any(w in msg_words for w in question_words) and len(words) >= 3:
        return True, ""

    # Check 5: Looks like random/off-topic text
    return False, "I'm here to help with Glowmart store-related questions (orders, shipping, returns, payments, etc.).\n\nIf you need general chat, I'm not the right assistant - but if you have a Glowmart question, I'm happy to help! What would you like to know?"


def run(user_message: str, user_email: str = "unknown@email.com"):
    """
    Main entry point for Glowmart customer support.
    Step 0: Guardrail check (saves LLM cost on invalid queries)
    Step 1: Run classifier agent to detect intent.
    Step 2: Route to the correct specialist agent.
    Step 2b: HARD-CODED TOOL CALLING for technical queries (bypasses LLM tool calling)
    """
    # ── STEP 0: Guardrail Check ──────────────
    is_valid, fallback = is_valid_support_query(user_message)
    if not is_valid:
        print("\n[GUARDRAIL] Query filtered (not a support question)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("FINAL RESPONSE TO CUSTOMER:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(fallback)
        return json.dumps({"response": fallback, "sources": [], "handoff": False})

    # Continue with full agent if query is valid
    support = GlowmartSupportCrew()

    inputs = {
        "user_message": user_message,
        "user_email": user_email,
        "escalation_summary": "None",
    }

    # ── STEP 1: Classify ─────────────────────
    print("\n[1/2] Classifying customer message...")
    classify_crew = Crew(
        agents=[support.classifier_agent()],
        tasks=[support.classify_task()],
        process=Process.sequential,
        verbose=True,
    )
    classify_result = classify_crew.kickoff(inputs=inputs)
    raw = str(classify_result).strip()

    # Parse classifier JSON output
    try:
        classification = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON block if there's surrounding text
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        classification = json.loads(match.group()) if match else {}

    category   = classification.get("category", "faq")
    confidence = classification.get("confidence", 0.0)
    reason     = classification.get("reason", "")

    print(f"\n→ Classified as: [{category.upper()}] (confidence: {confidence})")
    print(f"→ Reason: {reason}")

    # ── STEP 2: Route to specialist agent ────
    print(f"\n[2/2] Routing to {category} agent...")

    if category == "faq":
        chosen_task   = support.faq_task()
        chosen_agent  = support.faq_agent()
    elif category == "technical":
        chosen_task   = support.technical_task()
        chosen_agent  = support.technical_agent()
    else:  # escalation
        chosen_task   = support.escalation_task()
        chosen_agent  = support.escalation_agent()

    specialist_crew = Crew(
        agents=[chosen_agent],
        tasks=[chosen_task],
        process=Process.sequential,
        verbose=True,
    )
    final_result = specialist_crew.kickoff(inputs=inputs)

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("FINAL RESPONSE TO CUSTOMER:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    try:
        parsed = json.loads(str(final_result))
        print(parsed.get("response", final_result))
    except:
        print(final_result)

    return final_result


def chat_loop():
    """Interactive chat loop for terminal testing."""
    print("\n" + "=" * 50)
    print("  Glowmart Customer Support Agent")
    print("=" * 50)
    print("Type your message and press Enter.")
    print("Commands: 'exit' or 'quit' to stop")
    print("-" * 50)

    # Ask for email once at start (optional)
    user_email = input("Enter your email (or press Enter to skip): ").strip()
    if not user_email:
        user_email = "guest@glowmart.in"
    print(f"Using email: {user_email}\n")

    while True:
        # Get user message
        user_message = input("You: ").strip()

        # Check for exit
        if user_message.lower() in ["exit", "quit", "bye"]:
            print("\nThank you for using Glowmart Support. Goodbye!")
            break

        if not user_message:
            continue

        # Run the agent
        print("\n" + "-" * 50)
        try:
            result = run(user_message, user_email)
        except Exception as e:
            print(f"\nError: {e}")
        print("-" * 50 + "\n")


def main():
    """Entry point for crewai run command."""
    chat_loop()


if __name__ == "__main__":
    main()