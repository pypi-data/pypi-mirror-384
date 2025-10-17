Feature: Cattle Drive

    Background:
        Given An account called "Alice"

    Scenario:
        Given "Alice" created an actor called "Alyssa"
        When "Alice" deletes the actor "Alyssa"
        Then "Alice" has no actors

    Scenario:
        Given "Alice" created an actor called "Alice"
        When "Alice" sends the trigger action "send_message" with content
            """
            {}
            """
        Then "Alice" receives an error

    Scenario:
        Given "Alice" created an actor called "Alice"
        When "Alice" sends the trigger action "send_message" with content
            """
            {
                "actor": "__Alice_ID__"
            }
            """
        Then "Alice" receives an error