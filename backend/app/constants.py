"""Values shared across layers that are not user-configurable.

`DEMO_SESSION_ID` lives here rather than in `services/bootstrap` because the
access-control layer needs to recognise the demo session, and importing the
seeding module to read one string would drag the whole ingestion pipeline
(and its models) into every request path that checks ownership.
"""

# The seeded, shared, read-only session every visitor can see.
DEMO_SESSION_ID = "demo"
DEMO_SESSION_NAME = "Demo — ask these papers anything"
