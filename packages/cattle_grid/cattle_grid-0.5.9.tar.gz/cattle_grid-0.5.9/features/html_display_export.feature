Feature: Export for HTML Display

    Background:
        Given A new user called "Alice"
        And "Alice" is in the "html_display" group

    Scenario: Can request export token
        When "Alice" requests an export token
        And The export url is retrieved
        Then The response code is "200"


    Scenario: Export contains message
        When "Alice" publishes a message "Who stole my milk?" to her followers
        And "Alice" requests an export token
        And The export url is retrieved
        Then The response code is "200"
        And The response contains "Who stole my milk?"
