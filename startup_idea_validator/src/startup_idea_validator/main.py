#!/usr/bin/env python
import sys

from startup_idea_validator.crew import StartupIdeaValidator

def run():
    inputs = {
        'idea': 'i wanted to make a reel to notes web app so that users can convert their reels to notes and any market research and content creation, can repourpous the content for different platforms like linkedin, twitter, instagram etc. and anylist can prepare data set from bulk reels for training models'
    }
    
    try:
        StartupIdeaValidator().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


