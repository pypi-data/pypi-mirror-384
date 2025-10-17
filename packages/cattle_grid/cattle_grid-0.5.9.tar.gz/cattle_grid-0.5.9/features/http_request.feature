Feature: Requesting object with HTTP

    Background:
        Given A new user called "Alice"

    Scenario:
        When The request URL is the actor object of "Alice"
        And The request requests the content-type "application/activity+json"
        And The request is made
        Then The response code is "401"

    Scenario: No webpage representation
        When The request URL is the actor object of "Alice"
        And The request requests the content-type "text/html"
        And The request is made
        Then The response code is "406"

    Scenario: "Has a webpage"
        Given "Alice" sets her display name to "alex"
        When The request URL is the actor object of "Alice"
        And The request requests the content-type "text/html"
        And The request is made
        Then The response is a webpage