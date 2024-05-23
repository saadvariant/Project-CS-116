import feedparser
import string
import time
import threading
from datetime import datetime
import pytz

# Define a class to represent news stories
class NewsStory:
    def __init__(self, guid, title, description, link, pubdate):
        self.guid = guid
        self.title = title
        self.description = description
        self.link = link
        self.pubdate = pubdate

# Define a class to represent triggers
class Trigger:
    def evaluate(self, story):
        raise NotImplementedError

# Define trigger subclasses
class PhraseTrigger(Trigger):
    def __init__(self, phrase):
        self.phrase = phrase.lower()

    def is_phrase_in(self, text):
        text = text.lower()
        for p in string.punctuation:
            text = text.replace(p, ' ')
        words = text.split()
        phrase_words = self.phrase.split()
        for i in range(len(words) - len(phrase_words) + 1):
            if phrase_words == words[i:i + len(phrase_words)]:
                return True
        return False

    def evaluate(self, story):
        return self.is_phrase_in(story.title) or self.is_phrase_in(story.description)

class TimeTrigger(Trigger):
    def __init__(self, time_string):
        est = pytz.timezone("EST")
        self.time = est.localize(datetime.strptime(time_string, "%d %b %Y %H:%M:%S"))

    def evaluate(self, story):
        return story.pubdate < self.time

# Define composite triggers
class AndTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) and self.trigger2.evaluate(story)

class OrTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) or self.trigger2.evaluate(story)

class NotTrigger(Trigger):
    def __init__(self, trigger):
        self.trigger = trigger

    def evaluate(self, story):
        return not self.trigger.evaluate(story)

# Function to process RSS feed and extract news stories
def process_feed(url):
    feed = feedparser.parse(url)
    entries = feed.entries
    stories = []
    for entry in entries:
        guid = entry.guid
        title = entry.title
        description = entry.description
        link = entry.link
        pubdate = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
        stories.append(NewsStory(guid, title, description, link, pubdate))
    return stories

# Function to filter news stories based on triggers
def filter_stories(stories, triggerlist):
    filtered_stories = []
    for story in stories:
        if all(trigger.evaluate(story) for trigger in triggerlist):
            filtered_stories.append(story)
    return filtered_stories

# Function to read trigger configurations from a file
def read_trigger_config(filename):
    triggers = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('//'):
                parts = line.split(',')
                if len(parts) >= 2:
                    trigger_type = parts[0].strip()
                    if trigger_type == 'TITLE':
                        trigger = PhraseTrigger(parts[1].strip())
                    elif trigger_type == 'DESCRIPTION':
                        trigger = PhraseTrigger(parts[1].strip())
                    elif trigger_type == 'BEFORE':
                        trigger = TimeTrigger(parts[1].strip())
                    elif trigger_type == 'AFTER':
                        trigger = TimeTrigger(parts[1].strip())
                    # Add more trigger types if needed
                    triggers.append(trigger)
    return triggers

# Main function to monitor news feeds
def main_thread():
    try:
        triggerlist = read_trigger_config('triggers.txt')

        while True:
            # Retrieve news stories from RSS feeds
            google_stories = process_feed("http://news.google.com/news?output=rss")
            yahoo_stories = process_feed("http://news.yahoo.com/rss/topstories")
            all_stories = google_stories + yahoo_stories

            # Filter news stories based on triggers
            filtered_stories = filter_stories(all_stories, triggerlist)

            # Display filtered stories (print to console for simplicity)
            for story in filtered_stories:
                print("Title:", story.title)
                print("Description:", story.description)
                print("Link:", story.link)
                print("Publication Date:", story.pubdate)
                print("="*50)

            # Sleep for a specified interval before polling again
            time.sleep(120)

    except Exception as e:
        print("An error occurred:", e)

if __name__ == '__main__':
    main_thread()
