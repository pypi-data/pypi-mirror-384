Feature: String Utilities

  Scenario: Remove Arabic vowels from text
    Given a text with Arabic vowels "بِسْمِ ٱللَّٰهِ الرَّحْمٰانِ الرَّحِيمِ"
    When the Arabic vowels are removed
    Then the resulting text should be "بسم الله الرحمان الرحیم"

  Scenario: Normalize Persian characters
    Given a text with unnormalized Persian characters "ۀىي"
    When the Persian characters are normalized
    Then the resulting text should be "هیی"

  Scenario: Normalize punctuation marks
    Given a text with mixed punctuation "خوبی?"
    When the punctuation is normalized
    Then the resulting text should be "خوبی؟"

  Scenario: Normalize numbers to English format
    Given a text with Persian numbers "۱۲۳۴۵۶۷۸۹۰"
    When the numbers are normalized
    Then the resulting text should be "1234567890"

  Scenario: Clean whitespace and spacing issues
    Given a text with spacing issues "Hello  world"
    When the spacing is cleaned
    Then the resulting text should be "Hello world"

  Scenario: Remove punctuation marks
    Given a text with punctuation "Hello, world!!"
    When the punctuation is removed
    Then the resulting text should be "Hello world"

  Scenario: Mask URLs in text
    Given a text containing a URL "Visit https://example.com for info"
    When URLs are masked
    Then the resulting text should be "Visit MASK_URL for info"

  Scenario: Mask emails in text
    Given a text containing an email "Contact me at test@example.com"
    When emails are masked
    Then the resulting text should be "Contact me at MASK_EMAIL"

  Scenario: Mask phone numbers in text
    Given a text containing a phone number "+989123456789"
    When phone numbers are masked
    Then the resulting text should be "MASK_PHONE"

  Scenario: Convert English numbers to Persian
    Given a text with English numbers "1234567890"
    When the English numbers are converted to Persian
    Then the resulting text should be "۱۲۳۴۵۶۷۸۹۰"

  Scenario: Remove emojis from text
    Given a text containing emojis "Hello 😊🌍!"
    When emojis are removed
    Then the resulting text should be "Hello !"

  Scenario: Replace numbers with a mask
    Given a text containing numbers "Order 5 items"
    When numbers are replaced with a mask
    Then the resulting text should be "Order MASK_NUMBERS items"

  Scenario: Replace currencies with a mask
    Given a text containing currency symbols "Price: $100"
    When currencies are replaced with a mask
    Then the resulting text should be "Price: MASK_CURRENCIES 100"

  Scenario: Check if a string is empty
    Given an empty string " "
    When checking if the string is empty
    Then the result should be True

  Scenario: Check if a None string is empty
    Given a None string
    When checking if the string is empty
    Then the result should be True

  Scenario: Apply full text normalization
    Given a complex text "من درب خانه ام را بستم. شماره من ۱۲۳۴ است."
    When full text normalization is applied
    Then the resulting text should be "من درب خانه ام را بستم. شماره من 1234 است."
