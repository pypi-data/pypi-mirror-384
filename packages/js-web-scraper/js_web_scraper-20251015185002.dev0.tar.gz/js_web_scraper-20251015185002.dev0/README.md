# WebScraper
* This program can scrap data from websites using different scrapers, and send an email when 
matches/ changes deadening on the scraper used
* There are 2 types of scrapers:
    - Generic: Can scrap any website, but might not be as exact
    - Specific: Can scrap only specific websites, but will be more exact

## Generic Scrapers
 - Text
 - Diff

## Specific Scrapers
 - Cars.com

## How to use
### Text
1. Set these specific env variables
2. ```dotenv
    SCRAPER=text # Scraper to use
    URL=<URL> # URL to scrape
    TEXT=<TEXT> # Text to look for
   ```
3. Ensure all other required env variables are set

### Diff
1. Set these specific env variables
2. ```dotenv
    SCRAPER=diff # Scraper to use
    URL=<URL> # URL to scrape
    PERCENTAGE=<PERCENTAGE_DIFF> # Percentage difference to look for
   ```
3. Ensure all other required env variables are set

### Cars.com
1. Set these specific env variables
2. ```dotenv
    SCRAPER=cars_com # Scraper to use
    URL=https://www.cars.com/shopping/results/ # URL to scrape, must be on the results page, for a specific search
   ```
3. Ensure all other required env variables are set

### Required env variables
```dotenv
SLEEP_TIME_SEC= # Time to sleep between each scrape
SENDER_EMAIL= # Email to send from
FROM_EMAIL= # Name to send from i.e. '"Web Scraper" <no-reply@jstockley.com>'
RECEIVER_EMAIL= # Email to send to
PASSWORD= # Password for the sender's email
SMTP_SERVER= # SMTP server to use
SMTP_PORT= # SMTP port to use
TLS= # True/False to use TLS
```

### Running multiple of the same scraper
To run 2+ scrapers of the same type, i.e. 2 `diff` scrapers, make sure the host folder mapping is different
Ex:
```yaml
  diff-scraper-1:
    image: jnstockley/web-scraper:latest
    volumes:
      - ./diff-scraper-1-data/:/app/data/
    environment:
      - TZ=America/Chicago
      - SCRAPER=diff
      - URL=https://google.com
      - PERCENTAGE=5
      - SLEEP_TIME_SEC=21600

  diff-scraper-2:
    image: jnstockley/web-scraper:latest
    volumes:
      - ./diff-scraper-2-data/:/app/data/
    environment:
      - TZ=America/Chicago
      - SCRAPER=diff
      - URL=https://yahoo.com
      - PERCENTAGE=5
      - SLEEP_TIME_SEC=21600
```
