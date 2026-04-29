import json
import os
import uuid
from datetime import datetime
from typing import List
from dotenv import load_dotenv
from pathlib import Path
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tools import tool

# Load environment variables
load_dotenv()

llm = LLM(model="openai/gpt-4o")

# ─────────────────────────────────────────────
# DATA PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = Path("/Users/sakshamgupta/customer_support_agent/src/DATABASE")      
KB_PATH  = Path("/Users/sakshamgupta/customer_support_agent/src/DATABASE/knowledge_base.md")


# ─────────────────────────────────────────────
# CUSTOM tools (JSON database reads)
# ─────────────────────────────────────────────

@tool("search_knowledge_base")
def search_knowledge_base(query: str) -> str:
    """Search the Glowmart knowledge base markdown file for a query keyword.
    Returns all sections that contain any of the search keywords."""
    if not KB_PATH.exists():
        return "Knowledge base file not found."
    content = KB_PATH.read_text()
    sections = content.split("## ")
    results = []
    # Split query into individual keywords for matching
    query_words = [w for w in query.lower().split() if len(w) > 2]
    for section in sections:
        section_lower = section.lower()
        # Match if ANY keyword from query appears in the section
        if any(word in section_lower for word in query_words):
            # Return first 400 chars of matching section
            results.append(section[:400].strip())
    if not results:
        return f"No sections found matching '{query}' in the knowledge base."
    return "\n\n---\n\n".join(results)


@tool("lookup_order")
def lookup_order(order_id: str) -> str:
    """Look up a specific order by order ID from orders.json.
    Returns the full order object or an error message."""
    path = DATA_DIR / "orders.json"
    data = json.loads(path.read_text())
    for order in data["orders"]:
        if order["order_id"].lower() == order_id.strip().lower():
            return json.dumps(order, indent=2)
    return json.dumps({"error": f"Order {order_id} not found."})


@tool("lookup_customer")
def lookup_customer(email: str) -> str:
    """Look up a customer record by email address from customers.json.
    Returns customer profile AND their actual orders from orders.json."""
    # Find customer
    customer_path = DATA_DIR / "customers.json"
    customer_data = json.loads(customer_path.read_text())
    customer = None
    for c in customer_data["customers"]:
        if c["email"].lower() == email.strip().lower():
            customer = c
            break

    if not customer:
        return json.dumps({"error": f"No customer found with email {email}."})

    # Find customer's orders from orders.json
    orders_path = DATA_DIR / "orders.json"
    orders_data = json.loads(orders_path.read_text())
    customer_orders = [
        order for order in orders_data["orders"]
        if order["customer_email"].lower() == email.strip().lower()
    ]

    # Return customer + their actual orders
    result = {
        **customer,
        "orders": customer_orders
    }
    return json.dumps(result, indent=2)


@tool("check_inventory")
def check_inventory(product_id: str) -> str:
    """Check stock availability for a product by product_id from products.json.
    Returns product name, in_stock status, and quantity."""
    path = DATA_DIR / "products.json"
    data = json.loads(path.read_text())
    for product in data["products"]:
        if product["product_id"].lower() == product_id.strip().lower():
            return json.dumps({
                "product_id": product["product_id"],
                "name": product["name"],
                "in_stock": product["in_stock"],
                "quantity": product["quantity"],
                "price": product["price"]
            }, indent=2)
    return json.dumps({"error": f"Product {product_id} not found."})


@tool("create_ticket")
def create_ticket(
    customer_email: str,
    subject: str,
    priority: str,
    summary: str,
    original_message: str
) -> str:
    """Create a new escalation support ticket and save it to tickets.json.
    Priority must be: low, medium, high, or critical."""
    path = DATA_DIR / "tickets.json"
    data = json.loads(path.read_text())
    ticket_id = f"TKT-{str(len(data['tickets']) + 1).zfill(4)}"
    ticket = {
        "ticket_id": ticket_id,
        "customer_email": customer_email,
        "subject": subject,
        "priority": priority,
        "status": "open",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "summary": summary,
        "original_message": original_message,
        "assigned_to": None,
        "resolved_at": None
    }
    data["tickets"].append(ticket)
    path.write_text(json.dumps(data, indent=2))
    return json.dumps({"ticket_id": ticket_id, "status": "created"})


@tool("send_notification")
def send_notification(ticket_id: str, priority: str) -> str:
    """Send an alert notification to the human support team for a ticket.
    Use this for high or critical priority tickets only."""
    # In production: call Slack webhook, send email, etc.
    # For demo: just log it
    print(f"[ALERT] Ticket {ticket_id} created with priority: {priority}")
    return json.dumps({
        "sent": True,
        "ticket_id": ticket_id,
        "channel": "slack",
        "message": f"New {priority} priority ticket {ticket_id} needs attention."
    })


# ─────────────────────────────────────────────
# CREW CLASS
# ─────────────────────────────────────────────

@CrewBase
class GlowmartSupportCrew:
    """Glowmart multi-agent customer support system."""

    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    # ── AGENTS ──────────────────────────────

    @agent
    def classifier_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["classifier_agent"],
            verbose=True,
            llm=llm,
            allow_delegation=False,
        )

    @agent
    def faq_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["faq_agent"],
            tools=[search_knowledge_base],
            verbose=True,
            llm=llm,
            allow_delegation=False,
        )

    @agent
    def technical_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_agent"],
            tools=[lookup_order, lookup_customer, check_inventory],
            verbose=True,
            llm=llm,
            function_calling_llm=llm,
            allow_delegation=False,
            max_iter=3,
        )

    @agent
    def escalation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["escalation_agent"],
            tools=[create_ticket, send_notification],
            verbose=True,
            llm=llm,
            allow_delegation=False,
        )

    # ── TASKS ───────────────────────────────

    @task
    def classify_task(self) -> Task:
        return Task(
            config=self.tasks_config["classify_task"],
            agent=self.classifier_agent(),
        )

    @task
    def faq_task(self) -> Task:
        return Task(
            config=self.tasks_config["faq_task"],
            agent=self.faq_agent(),
            context=[self.classify_task()],
        )

    @task
    def technical_task(self) -> Task:
        return Task(
            config=self.tasks_config["technical_task"],
            agent=self.technical_agent(),
            context=[self.classify_task()],
        )

    @task
    def escalation_task(self) -> Task:
        return Task(
            config=self.tasks_config["escalation_task"],
            agent=self.escalation_agent(),
            context=[self.classify_task(), self.technical_task()],
        )

    # ── CREW ────────────────────────────────

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.classifier_agent(),
                self.faq_agent(),
                self.technical_agent(),
                self.escalation_agent(),
            ],
            tasks=[self.classify_task()],  # only classify runs first;
            # routing logic in main.py selects which sub-task runs next
            process=Process.sequential,
            verbose=True,
        )