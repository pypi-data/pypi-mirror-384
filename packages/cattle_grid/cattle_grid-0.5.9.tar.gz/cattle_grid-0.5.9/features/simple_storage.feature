Feature: Simple storage

    Background:
        Given A new user called "Alice"
        And A new user called "Bob"
        And "Bob" follows "Alice"

    Scenario: Publish Activity Works
        When "Alice" publishes a "moo" animal sound to her followers
        Then "Bob" receives an activity
        And the received activity is of type "AnimalSound"
        And "Bob" can retrieve the activity

    Scenario: Publish Object Works
        When "Alice" publishes a message "moo" to her followers
        Then "Bob" receives an activity
        And the received activity is of type "Create"
        And "Bob" can retrieve the activity

    Scenario: Publish Object content is correct
        When "Alice" publishes a message "I <3 milk!" to her followers
        Then "Bob" receives a message saying "I <3 milk!"
