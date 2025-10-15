Feature: Redis Mock Testing
  As a developer
  I want to have reliable Redis mocks for testing
  So that I can write tests without a real Redis server

  Background:
    Given test entities are defined

  Scenario: Store and retrieve a simple key-value pair with Redis mock
    Given a configured Redis mock
    When I store the key "user-id" with value "12345" in Redis mock
    Then the sync store operation should succeed
    When I retrieve the value for key "user-id" from Redis mock
    Then the sync retrieved value should be "12345"

  Scenario: Remove a key with Redis mock
    Given a configured Redis mock
    When I store the key "session-token" with value "abcde" in Redis mock
    Then the sync store operation should succeed
    When I remove the key "session-token" from Redis mock
    Then the sync remove operation should delete one key
    When I check if "session-token" exists in Redis mock
    Then the sync key should not exist

  Scenario: Manage a list of items with Redis mock
    Given a configured Redis mock
    When I add "apple, banana, orange" to the list "fruits" in Redis mock
    Then the sync list "fruits" should have 3 items
    When I fetch all items from the list "fruits" in Redis mock
    Then the sync list "fruits" should contain "apple, banana, orange"

  Scenario: Handle a hash structure with Redis mock
    Given a configured Redis mock
    When I assign "name" to "Alice" in the hash "profile" in Redis mock
    Then the sync hash assignment should succeed
    When I retrieve the "name" field from the hash "profile" in Redis mock
    Then the sync retrieved field value should be "Alice"

  Scenario: Manage a set of colors with Redis mock
    Given a configured Redis mock
    When I add "red, blue, green" to the set "colors" in Redis mock
    Then the sync set "colors" should have 3 members
    When I fetch all members from the set "colors" in Redis mock
    Then the sync set "colors" should contain "red, blue, green"

  @async
  Scenario: Store and retrieve a key-value pair asynchronously with Redis mock
    Given a configured async Redis mock
    When I store the key "order-id" with value "67890" in async Redis mock
    Then the async store operation should succeed
    When I retrieve the value for key "order-id" from async Redis mock
    Then the async retrieved value should be "67890"

  @async
  Scenario: Remove a key asynchronously with Redis mock
    Given a configured async Redis mock
    When I store the key "cache-key" with value "xyz" in async Redis mock
    Then the async store operation should succeed
    When I remove the key "cache-key" from async Redis mock
    Then the async remove operation should delete one key
    When I check if "cache-key" exists in async Redis mock
    Then the async key should not exist

  @async
  Scenario: Manage a list of tasks asynchronously with Redis mock
    Given a configured async Redis mock
    When I add "task1, task2, task3" to the list "tasks" in async Redis mock
    Then the async list "tasks" should have 3 items
    When I fetch all items from the list "tasks" in async Redis mock
    Then the async list "tasks" should contain "task1, task2, task3"

  @async
  Scenario: Handle a hash structure asynchronously with Redis mock
    Given a configured async Redis mock
    When I assign "email" to "bob@example.com" in the hash "contact" in async Redis mock
    Then the async hash assignment should succeed
    When I retrieve the "email" field from the hash "contact" in async Redis mock
    Then the async retrieved field value should be "bob@example.com"

  @async
  Scenario: Manage a set of tags asynchronously with Redis mock
    Given a configured async Redis mock
    When I add "tag1, tag2, tag3" to the set "tags" in async Redis mock
    Then the async set "tags" should have 3 members
    When I fetch all members from the set "tags" in async Redis mock
    Then the async set "tags" should contain "tag1, tag2, tag3"
