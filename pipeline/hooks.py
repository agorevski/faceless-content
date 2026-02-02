"""
Hooks Module - TikTok Retention & Engagement System

⚠️ NOTE: No modern equivalent exists yet in src/faceless/services/.
This module will be migrated in a future update.

Implements first-frame hooks, pattern interrupts, mid-video retention,
and comment bait strategies from FUTURE_IMPROVEMENTS.md
"""

import random

from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# FIRST-FRAME HOOKS (0.5-Second Attention Window)
# =============================================================================

FIRST_FRAME_HOOKS = {
    "scary-stories": {
        "text_question": [
            "Would you enter this door?",
            "Have you ever felt like you're being watched?",
            "What's the scariest thing you've ever seen?",
            "Would you stay in this house alone?",
            "Do you believe in things you can't explain?",
            "What would you do if you heard this at 3AM?",
            "Have you ever seen something you couldn't explain?",
            "Would you open this if you found it?",
            "Do you know what's watching you right now?",
            "Have you checked behind you recently?",
        ],
        "shocking_statement": [
            "I should have listened to my instincts.",
            "That was the last time I ever went there.",
            "I still can't sleep with the lights off.",
            "They never found what made those sounds.",
            "No one believed me until they saw it themselves.",
            "I'll never forget what I saw that night.",
            "Some doors should never be opened.",
            "I wasn't alone in that house.",
            "The scratching stopped. That's when I knew.",
            "It was behind me the whole time.",
        ],
        "number_promise": [
            "3 signs you're not alone in your house",
            "5 things you should NEVER do at 3AM",
            "The 1 rule that saved my life",
            "4 warning signs I ignored",
            "3 sounds that mean you need to RUN",
        ],
        "direct_address": [
            "You know that feeling when something's wrong?",
            "You've felt this before, haven't you?",
            "You're going to want to watch this to the end.",
            "You won't believe what happened next.",
            "You need to hear this before it's too late.",
        ],
    },
    "finance": {
        "text_question": [
            "Are you making this money mistake?",
            "Why are you still broke?",
            "Do you know where your money really goes?",
            "Think you're good with money?",
            "How much are you losing every month?",
            "Would you pass a financial IQ test?",
            "Are you secretly going broke?",
            "Do you know your real net worth?",
        ],
        "shocking_statement": [
            "The #1 reason you'll never be rich.",
            "Rich people NEVER do this.",
            "This one habit keeps you poor.",
            "Your bank is stealing from you.",
            "You're losing money while you sleep.",
            "Stop doing this with your money.",
            "This is why you're always broke.",
            "Your financial advisor lied to you.",
        ],
        "number_promise": [
            "3 money habits of millionaires",
            "5 things keeping you poor",
            "The 1% rule for building wealth",
            "7 money mistakes I wish I knew earlier",
            "3 investments that actually work",
            "5 signs you're secretly going broke",
        ],
        "direct_address": [
            "You're working too hard for too little.",
            "You've been lied to about money.",
            "You're one decision away from wealth.",
            "You need to stop what you're doing with money.",
            "You're making this mistake right now.",
        ],
    },
    "luxury": {
        "text_question": [
            "Guess how much this costs?",
            "Would you pay this much for a watch?",
            "Can you spot the $50,000 detail?",
            "What makes this worth millions?",
            "Would you drive this every day?",
            "Can you tell real from fake?",
        ],
        "shocking_statement": [
            "This costs more than your house.",
            "Only 10 people in the world own this.",
            "This car costs $100,000 PER MONTH.",
            "The waitlist is 5 years long.",
            "They destroy unsold inventory.",
            "This watch took 3 years to make.",
        ],
        "number_promise": [
            "5 things only the ultra-rich buy",
            "3 luxury items that are actually worth it",
            "The $1 million daily routine",
            "7 signs of quiet luxury",
            "3 things billionaires never buy",
        ],
        "direct_address": [
            "You've never seen anything like this.",
            "You won't believe what this costs.",
            "You're looking at pure perfection.",
            "You could own this. Here's how.",
            "You're about to see real luxury.",
        ],
    },
    "true-crime": {
        "text_question": [
            "What really happened that night?",
            "Why did no one believe her?",
            "What did the police miss?",
            "Who was really responsible?",
            "Why was this case never solved?",
        ],
        "shocking_statement": [
            "The killer was in the house the whole time.",
            "They got the wrong person.",
            "The evidence was hidden for 30 years.",
            "No one saw what was right in front of them.",
            "This case changed everything.",
        ],
        "number_promise": [
            "3 clues everyone missed",
            "5 red flags ignored by police",
            "The 1 piece of evidence that solved it all",
            "4 suspects who were never investigated",
        ],
        "direct_address": [
            "You think you know this case. You don't.",
            "You won't believe what was overlooked.",
            "You need to hear the real story.",
        ],
    },
    "psychology-facts": {
        "text_question": [
            "Why does your brain do this?",
            "Are you being manipulated?",
            "What does this say about you?",
            "Why can't you stop thinking about it?",
            "What's your attachment style?",
        ],
        "shocking_statement": [
            "Your brain lies to you every day.",
            "This is why people don't like you.",
            "You're more predictable than you think.",
            "Narcissists always do this.",
            "Your childhood trauma shows up here.",
        ],
        "number_promise": [
            "5 signs of high intelligence",
            "3 manipulation tactics to recognize",
            "7 signs someone is lying",
            "4 traits of emotionally intelligent people",
        ],
        "direct_address": [
            "You've done this without realizing it.",
            "You're being manipulated and don't know it.",
            "You need to understand why you do this.",
        ],
    },
    "history": {
        "text_question": [
            "What really happened in 1347?",
            "Why did they hide this from history books?",
            "What would you have done?",
            "How did they survive this?",
        ],
        "shocking_statement": [
            "History books got this completely wrong.",
            "They never taught you this in school.",
            "This changed the world forever.",
            "No one saw it coming.",
            "This is the moment everything changed.",
        ],
        "number_promise": [
            "5 things they didn't teach you in school",
            "3 moments that changed history",
            "The 1 decision that altered everything",
            "7 historical facts that seem impossible",
        ],
        "direct_address": [
            "You think you know history. Think again.",
            "You were lied to in school.",
            "You need to know what really happened.",
        ],
    },
    "motivation": {
        "text_question": [
            "Why haven't you started yet?",
            "What's really holding you back?",
            "Are you living or just existing?",
            "When will you finally change?",
        ],
        "shocking_statement": [
            "You're not lazy. You're scared.",
            "Success is easier than you think.",
            "You've already wasted too much time.",
            "The only thing stopping you is you.",
            "Champions are made in the dark.",
        ],
        "number_promise": [
            "5 habits that changed my life",
            "3 things successful people do before 6AM",
            "The 1 rule for unstoppable momentum",
            "7 signs you're about to level up",
        ],
        "direct_address": [
            "You're stronger than you know.",
            "You have what it takes.",
            "You're one decision away from a different life.",
        ],
    },
    "space-astronomy": {
        "text_question": [
            "What's at the edge of the universe?",
            "Are we alone in the cosmos?",
            "What happens inside a black hole?",
            "How big is the universe really?",
        ],
        "shocking_statement": [
            "This star is bigger than our solar system.",
            "We just discovered something impossible.",
            "There are more stars than grains of sand on Earth.",
            "The universe is expanding faster than light.",
            "This planet rains diamonds.",
        ],
        "number_promise": [
            "5 mind-blowing facts about space",
            "3 discoveries that changed astronomy",
            "The 1 photo that proves we're not alone",
            "7 things about the universe that make no sense",
        ],
        "direct_address": [
            "You can't comprehend how big this is.",
            "You're about to question everything.",
            "You've never seen anything like this.",
        ],
    },
    "conspiracy-mysteries": {
        "text_question": [
            "What are they hiding?",
            "Why was this deleted from the internet?",
            "What don't they want you to know?",
            "Have you ever wondered why...?",
        ],
        "shocking_statement": [
            "This was covered up for decades.",
            "The truth is stranger than you think.",
            "They don't want you to see this.",
            "Everything you know is wrong.",
            "This changes everything.",
        ],
        "number_promise": [
            "5 things that don't add up",
            "3 coincidences that are too perfect",
            "The 1 document that reveals everything",
            "7 questions they refuse to answer",
        ],
        "direct_address": [
            "You've been lied to your whole life.",
            "You need to connect these dots.",
            "You're not crazy for questioning this.",
        ],
    },
    "animal-facts": {
        "text_question": [
            "Did you know animals could do this?",
            "What animal is smarter than you think?",
            "Can you guess what this creature does?",
            "Why does this animal do this?",
        ],
        "shocking_statement": [
            "This animal can kill you in seconds.",
            "Scientists just discovered this ability.",
            "This creature defies all logic.",
            "This animal remembers every face it sees.",
            "You won't believe what this animal can do.",
        ],
        "number_promise": [
            "5 animals smarter than you thought",
            "3 creatures with superpowers",
            "The 1 animal fact that changes everything",
            "7 animals that can survive anything",
        ],
        "direct_address": [
            "You've never seen an animal do this.",
            "You're about to rethink everything.",
            "You won't believe your eyes.",
        ],
    },
    "health-wellness": {
        "text_question": [
            "Are you doing this wrong?",
            "Is your body trying to tell you something?",
            "What's really causing your fatigue?",
            "Are you secretly unhealthy?",
        ],
        "shocking_statement": [
            "Your doctor isn't telling you this.",
            "This 'healthy' food is making you sick.",
            "You're destroying your body without knowing.",
            "This one habit changes everything.",
            "Stop doing this to your body.",
        ],
        "number_promise": [
            "5 signs your body needs help",
            "3 morning habits for better health",
            "The 1 thing destroying your gut",
            "7 foods you should never eat",
        ],
        "direct_address": [
            "You're making this mistake every day.",
            "You need to know this about your body.",
            "You can fix this in one week.",
        ],
    },
    "relationship-advice": {
        "text_question": [
            "Is this a red flag?",
            "Why do you keep attracting the same type?",
            "What's your attachment style?",
            "Are they really into you?",
        ],
        "shocking_statement": [
            "If they do this, leave.",
            "You're settling and you know it.",
            "This is why your relationships fail.",
            "Healthy love doesn't feel like this.",
            "They're showing you who they are.",
        ],
        "number_promise": [
            "5 green flags to look for",
            "3 red flags everyone ignores",
            "The 1 thing that predicts breakups",
            "7 signs they're not the one",
        ],
        "direct_address": [
            "You deserve better than this.",
            "You know what you need to do.",
            "You're not asking for too much.",
        ],
    },
    "tech-gadgets": {
        "text_question": [
            "Have you seen this gadget?",
            "Is this worth the hype?",
            "What can this thing actually do?",
            "Should you upgrade?",
        ],
        "shocking_statement": [
            "This gadget changes everything.",
            "You're using your phone wrong.",
            "This feature was hidden from you.",
            "Technology has gone too far.",
            "This costs less than you think.",
        ],
        "number_promise": [
            "5 gadgets you didn't know existed",
            "3 features you're not using",
            "The 1 upgrade worth your money",
            "7 tech hacks for your phone",
        ],
        "direct_address": [
            "You need this in your life.",
            "You've been missing out on this.",
            "You won't believe what it can do.",
        ],
    },
    "life-hacks": {
        "text_question": [
            "Why didn't I think of this?",
            "Have you been doing this wrong?",
            "Does this actually work?",
            "Why doesn't everyone know this?",
        ],
        "shocking_statement": [
            "You've been doing it wrong your whole life.",
            "This hack saved me hours.",
            "I can't believe this actually works.",
            "Game changer alert!",
            "This will blow your mind.",
        ],
        "number_promise": [
            "5 hacks you'll use every day",
            "3 tricks that save time and money",
            "The 1 hack that changes everything",
            "7 life hacks you need right now",
        ],
        "direct_address": [
            "You need to try this immediately.",
            "You're going to thank me later.",
            "You've been missing this your whole life.",
        ],
    },
    "mythology-folklore": {
        "text_question": [
            "What was this creature really?",
            "Did the gods actually exist?",
            "What's the true story behind this legend?",
            "Could this myth be real?",
        ],
        "shocking_statement": [
            "This god was more terrifying than you know.",
            "The real story is much darker.",
            "Ancient people witnessed something unexplainable.",
            "This legend was based on truth.",
            "They feared this creature for good reason.",
        ],
        "number_promise": [
            "5 myths that might be real",
            "3 gods you don't want to anger",
            "The 1 legend that haunts cultures worldwide",
            "7 mythical creatures that actually existed",
        ],
        "direct_address": [
            "You've never heard the real story.",
            "You'll never see this myth the same way.",
            "You need to know what they really believed.",
        ],
    },
    "unsolved-mysteries": {
        "text_question": [
            "What really happened here?",
            "Why has no one solved this?",
            "Where did they go?",
            "What are we missing?",
        ],
        "shocking_statement": [
            "This case makes no sense.",
            "The evidence contradicts everything.",
            "No one can explain this.",
            "They disappeared without a trace.",
            "This mystery has haunted investigators for decades.",
        ],
        "number_promise": [
            "5 mysteries that defy explanation",
            "3 disappearances no one can solve",
            "The 1 clue everyone overlooked",
            "7 cases that keep detectives awake",
        ],
        "direct_address": [
            "You won't be able to explain this.",
            "You'll be thinking about this for days.",
            "You decide what happened.",
        ],
    },
    "geography-facts": {
        "text_question": [
            "Did you know this country exists?",
            "Where is the strangest place on Earth?",
            "Can you find this on a map?",
            "What's special about this border?",
        ],
        "shocking_statement": [
            "This place shouldn't exist.",
            "Most people can't find this on a map.",
            "This country is smaller than you think.",
            "Geography is weirder than you know.",
            "This border makes no sense.",
        ],
        "number_promise": [
            "5 countries you've never heard of",
            "3 borders that make no sense",
            "The 1 place on Earth like no other",
            "7 geography facts that seem fake",
        ],
        "direct_address": [
            "You probably can't point to this on a map.",
            "You've never seen a place like this.",
            "You'll want to visit after this.",
        ],
    },
    "ai-future-tech": {
        "text_question": [
            "Is this the future?",
            "Will AI replace you?",
            "What can AI do now?",
            "Are we ready for this?",
        ],
        "shocking_statement": [
            "AI can now do this better than humans.",
            "The future arrived faster than expected.",
            "This technology will change everything.",
            "We're not ready for what's coming.",
            "This AI breakthrough changes everything.",
        ],
        "number_promise": [
            "5 AI tools you need to try",
            "3 jobs AI will replace first",
            "The 1 technology that changes everything",
            "7 predictions for the next decade",
        ],
        "direct_address": [
            "You need to adapt to this now.",
            "You're falling behind if you don't know this.",
            "You won't believe what's possible.",
        ],
    },
    "philosophy": {
        "text_question": [
            "What is the meaning of life?",
            "Are we living in a simulation?",
            "What would you sacrifice?",
            "Is free will an illusion?",
        ],
        "shocking_statement": [
            "Everything you believe could be wrong.",
            "This question has no answer.",
            "The ancient Greeks knew something we forgot.",
            "Your reality isn't what you think.",
            "This idea will change how you see everything.",
        ],
        "number_promise": [
            "5 questions that have no answers",
            "3 philosophical ideas that change everything",
            "The 1 concept that rewires your brain",
            "7 paradoxes that break logic",
        ],
        "direct_address": [
            "You've never thought about it this way.",
            "You can't unknow this.",
            "You'll be thinking about this for days.",
        ],
    },
    "book-summaries": {
        "text_question": [
            "What's the main idea of this book?",
            "Is this book worth reading?",
            "What can you learn in 60 seconds?",
            "Have you read this yet?",
        ],
        "shocking_statement": [
            "This book changed millions of lives.",
            "The author reveals the one secret to success.",
            "This idea took 300 pages to explain.",
            "You can learn this in 60 seconds.",
            "This book was banned for a reason.",
        ],
        "number_promise": [
            "5 key lessons from this book",
            "3 ideas that will change your life",
            "The 1 takeaway you need",
            "7 books summarized in 60 seconds",
        ],
        "direct_address": [
            "You need to read this book.",
            "You'll thank me for this summary.",
            "You can't afford to miss these ideas.",
        ],
    },
    "celebrity-net-worth": {
        "text_question": [
            "Guess how much they make?",
            "Who's richer?",
            "How did they get so wealthy?",
            "Is this celebrity broke?",
        ],
        "shocking_statement": [
            "They make $1 million per day.",
            "This celebrity is secretly broke.",
            "Their net worth dropped by 90%.",
            "They make more than you think.",
            "From nothing to billions.",
        ],
        "number_promise": [
            "5 richest celebrities of 2024",
            "3 celebrities who lost everything",
            "The 1 celebrity richer than you thought",
            "7 shocking celebrity salaries",
        ],
        "direct_address": [
            "You won't believe how much they make.",
            "You're about to feel poor.",
            "You need to see these numbers.",
        ],
    },
    "survival-tips": {
        "text_question": [
            "Could you survive this?",
            "What would you do in this situation?",
            "Do you know this survival skill?",
            "Are you prepared for this?",
        ],
        "shocking_statement": [
            "This mistake kills most people.",
            "You have 3 minutes to act.",
            "Most people wouldn't survive this.",
            "This one skill saves lives.",
            "They did everything wrong.",
        ],
        "number_promise": [
            "5 survival skills everyone should know",
            "3 mistakes that could kill you",
            "The 1 thing to do first",
            "7 wilderness survival tips",
        ],
        "direct_address": [
            "You need to learn this now.",
            "You're not as prepared as you think.",
            "You could save a life with this.",
        ],
    },
    "sleep-relaxation": {
        "text_question": [
            "Can't fall asleep?",
            "Why do you wake up tired?",
            "Is your sleep quality bad?",
            "What's keeping you awake?",
        ],
        "shocking_statement": [
            "This is why you can't sleep.",
            "You're ruining your sleep without knowing.",
            "Fall asleep in 2 minutes with this.",
            "Your nighttime routine is wrong.",
            "This sound puts anyone to sleep.",
        ],
        "number_promise": [
            "5 tricks for better sleep",
            "3 things ruining your rest",
            "The 1 habit for perfect sleep",
            "7 ways to fall asleep faster",
        ],
        "direct_address": [
            "You'll be asleep in minutes.",
            "You need to try this tonight.",
            "You deserve restful sleep.",
        ],
    },
    "netflix-recommendations": {
        "text_question": [
            "What should you watch tonight?",
            "Looking for your next binge?",
            "Need something new to watch?",
            "Ever heard of this hidden gem?",
        ],
        "shocking_statement": [
            "This show will ruin your sleep schedule.",
            "Netflix doesn't want you to find this.",
            "The most underrated show on Netflix right now.",
            "This got cancelled but it's INCREDIBLE.",
            "Everyone's sleeping on this movie.",
        ],
        "number_promise": [
            "5 shows you'll binge in one sitting",
            "3 movies that will blow your mind",
            "The 1 series you NEED to watch",
            "7 hidden gems on Netflix",
        ],
        "direct_address": [
            "You've been missing this masterpiece.",
            "You won't be able to stop watching.",
            "You'll thank me for this recommendation.",
        ],
    },
    "mockumentary-howmade": {
        "text_question": [
            "Ever wonder how this is made?",
            "What goes into making THIS?",
            "How does THIS get manufactured?",
            "What's the factory process for this?",
        ],
        "shocking_statement": [
            "The factory process is INSANE.",
            "You won't believe how this is made.",
            "The manufacturing process is wild.",
            "This requires exactly 47 specialized workers.",
            "Here at the facility, we take this seriously.",
        ],
        "number_promise": [
            "5 steps to make the perfect product",
            "3 factory secrets they don't tell you",
            "The 1 process that takes 6 months",
            "17 quality control checkpoints",
        ],
        "direct_address": [
            "You've never seen a factory like this.",
            "You'll never look at this the same way.",
            "You're about to learn something incredible.",
        ],
    },
}


# =============================================================================
# PATTERN INTERRUPT OPENERS
# =============================================================================

PATTERN_INTERRUPTS = {
    "audio": [
        "sudden_silence",  # Silence after trending sound
        "record_scratch",  # Classic attention-grabber
        "whisper_start",  # Whispered opening
        "reversed_audio",  # 0.5 sec reversed audio
        "heartbeat",  # Tension builder
        "glass_break",  # Sharp pattern break
    ],
    "visual": [
        "inverted_colors",  # Inverted for first 0.5 sec
        "extreme_closeup",  # Close-up that pulls back
        "black_screen_text",  # Black screen with single word
        "glitch_transition",  # Glitch effect in
        "flash_frame",  # Quick flash of upcoming reveal
        "zoom_blur",  # Blur to sharp focus
    ],
}


# =============================================================================
# MID-VIDEO RETENTION HOOKS (30-50% Mark)
# =============================================================================

MID_VIDEO_HOOKS = {
    "verbal": {
        "scary-stories": [
            "But here's where it gets worse...",
            "Wait until you see what happens next.",
            "That's not even the scary part.",
            "I saved the worst for last.",
            "But they made one mistake...",
            "And then I heard it again.",
            "That's when everything changed.",
            "But I wasn't prepared for what came next.",
            "Little did I know...",
            "And that's when I realized the truth.",
        ],
        "finance": [
            "But here's what they don't tell you...",
            "Wait, it gets better.",
            "This is where it gets interesting.",
            "But the real secret is...",
            "Here's the part that changes everything.",
            "Most people miss this crucial detail.",
            "But there's a catch...",
            "Now here's the game-changer.",
        ],
        "luxury": [
            "But wait until you see inside...",
            "That's not even the impressive part.",
            "Here's what makes it truly special.",
            "But the real luxury is hidden.",
            "This is where it gets exclusive.",
            "Wait until you see the price tag.",
            "But there's something even more rare.",
            "Here's what you don't see.",
        ],
        "true-crime": [
            "But here's what the police missed...",
            "That's when investigators found something disturbing.",
            "Wait until you hear what they discovered.",
            "But the evidence told a different story.",
            "This is where the case gets strange.",
            "Then they found the one clue that changed everything.",
        ],
        "psychology-facts": [
            "But here's the fascinating part...",
            "This is where it gets interesting.",
            "Now here's what studies actually show...",
            "But your brain does something even stranger.",
            "Wait until you hear why this happens.",
            "The research reveals something surprising.",
        ],
        "history": [
            "But here's what history books leave out...",
            "That's when everything changed forever.",
            "Wait until you hear what happened next.",
            "But the real story is even more dramatic.",
            "This is the moment that altered history.",
            "Then came the turning point.",
        ],
        "motivation": [
            "But here's what separates winners...",
            "This is where most people quit.",
            "Now here's what actually works...",
            "But the real secret is simpler than you think.",
            "Wait until you hear the truth.",
            "This is where you need to pay attention.",
        ],
        "space-astronomy": [
            "But here's what scientists just discovered...",
            "Wait until you see the scale of this.",
            "That's not even the most incredible part.",
            "But the universe gets even stranger.",
            "This is where it gets mind-blowing.",
            "Then they found something impossible.",
        ],
        "conspiracy-mysteries": [
            "But here's what they don't want you to know...",
            "That's when things got suspicious.",
            "Wait until you connect these dots.",
            "But the rabbit hole goes deeper.",
            "This is where it gets interesting.",
            "Then they tried to cover it up.",
        ],
        "animal-facts": [
            "But here's the incredible part...",
            "Wait until you see what it does next.",
            "That's not even their coolest ability.",
            "But nature gets even weirder.",
            "This is where it gets amazing.",
            "Then scientists discovered something incredible.",
        ],
        "health-wellness": [
            "But here's what doctors don't mention...",
            "This is where most people go wrong.",
            "Wait until you hear the solution.",
            "But the real fix is simpler than you think.",
            "Now here's what actually works.",
            "This changes everything.",
        ],
        "relationship-advice": [
            "But here's the real issue...",
            "That's when you need to pay attention.",
            "Wait until you hear what this really means.",
            "But healthy relationships do this instead.",
            "This is where most people mess up.",
            "Now here's what you should do.",
        ],
        "tech-gadgets": [
            "But wait until you see this feature...",
            "That's not even the best part.",
            "Here's what makes it truly special.",
            "But the real innovation is hidden.",
            "This is where it gets impressive.",
            "Now let me show you something cool.",
        ],
        "life-hacks": [
            "But here's the game-changer...",
            "Wait until you see the results.",
            "That's not even the best hack.",
            "But here's an even better trick.",
            "This is where it gets satisfying.",
            "Now watch what happens.",
        ],
        "mythology-folklore": [
            "But the legend gets darker...",
            "That's when the gods intervened.",
            "Wait until you hear what happened next.",
            "But the ancient texts reveal more.",
            "This is where the myth gets terrifying.",
            "Then the prophecy came true.",
        ],
        "unsolved-mysteries": [
            "But here's where it gets strange...",
            "That's when investigators hit a dead end.",
            "Wait until you hear this detail.",
            "But the evidence makes no sense.",
            "This is where the mystery deepens.",
            "Then something unexplainable happened.",
        ],
        "geography-facts": [
            "But here's what makes it truly unique...",
            "Wait until you see the comparison.",
            "That's not even the strangest part.",
            "But the geography gets weirder.",
            "This is where it gets mind-blowing.",
            "Now here's the surprising fact.",
        ],
        "ai-future-tech": [
            "But here's what AI can do now...",
            "Wait until you see this capability.",
            "That's not even the most advanced part.",
            "But the technology goes even further.",
            "This is where it gets revolutionary.",
            "Now here's what's coming next.",
        ],
        "philosophy": [
            "But here's where it gets deep...",
            "That's when the paradox emerges.",
            "Wait until you consider this perspective.",
            "But the implications go further.",
            "This is where it changes everything.",
            "Now think about this.",
        ],
        "book-summaries": [
            "But here's the key insight...",
            "That's not even the main idea.",
            "Wait until you hear this takeaway.",
            "But the author reveals something bigger.",
            "This is where it gets powerful.",
            "Now here's what you can apply today.",
        ],
        "celebrity-net-worth": [
            "But wait until you see how much...",
            "That's not even their main income.",
            "Here's where the real money comes from.",
            "But their net worth gets crazier.",
            "This is where it gets insane.",
            "Now here's the shocking number.",
        ],
        "survival-tips": [
            "But here's the critical mistake...",
            "That's when survival becomes unlikely.",
            "Wait until you learn this technique.",
            "But the most important step is next.",
            "This is where most people fail.",
            "Now here's what could save your life.",
        ],
        "sleep-relaxation": [
            "But here's what actually helps...",
            "This is where relaxation begins.",
            "Now let your mind drift...",
            "But the real secret is simple.",
            "Feel yourself becoming calmer.",
            "Now take a deep breath.",
        ],
        "netflix-recommendations": [
            "But the plot twist changes everything...",
            "This is where it gets REALLY good.",
            "Now here's why critics loved it...",
            "But the ending will shock you.",
            "This scene alone makes it worth watching.",
            "Now let me tell you about the cast.",
        ],
        "mockumentary-howmade": [
            "But here's where the magic happens...",
            "This is where most factories fail.",
            "Now the assembly line gets interesting.",
            "But the quality control is crucial.",
            "This step takes exactly 3.7 minutes.",
            "Now the product enters Phase 2.",
        ],
    },
    "text_overlay": [
        "WAIT FOR IT",
        "👀",
        "HERE IT COMES",
        "WATCH THIS",
        "DON'T SCROLL",
        "IT GETS WORSE",
        "KEEP WATCHING",
        "3... 2... 1...",
    ],
    "visual_cues": [
        "arrow_pointing_forward",
        "countdown_timer",
        "flash_of_upcoming",
        "zoom_emphasis",
        "split_second_reveal",
    ],
}


# =============================================================================
# COMMENT BAIT & ENGAGEMENT TRIGGERS
# =============================================================================

COMMENT_TRIGGERS = {
    "controversial_endings": {
        "scary-stories": [
            "I think this is actually NOT that scary - what do you think?",
            "Honestly, I would have stayed. Would you?",
            "Was this real or fake? You decide.",
            "I think they made it up. Change my mind.",
            "The scariest part wasn't even shown. Can you guess?",
        ],
        "finance": [
            "This is why renting is smarter than buying. Fight me.",
            "College is a waste of money. Agree or disagree?",
            "Crypto is dead. Change my mind.",
            "The 9-5 is actually the safest path. Debate me.",
            "Rich people aren't that smart. They're just lucky.",
        ],
        "luxury": [
            "This is overpriced garbage. Change my mind.",
            "Rich people have no taste. Just money.",
            "This is actually tacky. Real wealth is subtle.",
            "You don't need this to be happy. Or do you?",
            "Old money would never buy this.",
        ],
        "true-crime": [
            "I think they got the wrong person. Thoughts?",
            "The police completely failed here. Agree?",
            "This case is actually solved. Fight me.",
            "The real killer was never caught.",
            "What do YOU think happened?",
        ],
        "psychology-facts": [
            "This is actually pseudoscience. Change my mind.",
            "Everyone thinks they're the exception to this.",
            "I disagree with this study. Here's why.",
            "You're probably doing this right now.",
            "Which type are you? Comment below.",
        ],
        "history": [
            "History books got this completely wrong.",
            "This leader is overrated. Fight me.",
            "We learned nothing from this. Prove me wrong.",
            "This moment changed everything. Or did it?",
            "What would YOU have done?",
        ],
        "motivation": [
            "Hard work is overrated. Strategy matters more.",
            "Not everyone can do this. Be realistic.",
            "This advice is toxic positivity. Change my mind.",
            "You're already capable. You just don't believe it.",
            "What's YOUR excuse?",
        ],
        "space-astronomy": [
            "We're definitely not alone. Change my mind.",
            "Space exploration is a waste of money. Fight me.",
            "The universe is probably a simulation.",
            "This proves life exists elsewhere.",
            "What do you think is out there?",
        ],
        "conspiracy-mysteries": [
            "This is obviously true. Open your eyes.",
            "There's more to this story.",
            "Coincidence? I don't think so.",
            "They want you to forget about this.",
            "What do YOU think really happened?",
        ],
        "animal-facts": [
            "Humans are actually the weirdest animals.",
            "This animal is underrated. Change my mind.",
            "We don't deserve animals.",
            "What's your favorite animal fact?",
            "Did you know this? Comment below.",
        ],
        "health-wellness": [
            "This health advice is actually dangerous.",
            "Doctors don't want you to know this.",
            "Most diet advice is wrong. Fight me.",
            "Are you guilty of this? Be honest.",
            "What's YOUR health tip?",
        ],
        "relationship-advice": [
            "This is actually toxic advice. Change my mind.",
            "Red flag or green flag? Debate below.",
            "Not everyone deserves a second chance.",
            "You can't change someone. Accept it.",
            "What's YOUR biggest relationship lesson?",
        ],
        "tech-gadgets": [
            "This is overpriced garbage. Fight me.",
            "Android is better than iPhone. Debate.",
            "You don't need this. Marketing lies.",
            "This changed my life. Or it's a gimmick.",
            "What tech could you not live without?",
        ],
        "life-hacks": [
            "This hack is actually useless. Prove me wrong.",
            "Why doesn't everyone know this?",
            "This seems fake. Did it work for you?",
            "Best hack I've ever seen. Or is it?",
            "Share YOUR best life hack below.",
        ],
        "mythology-folklore": [
            "This myth was based on real events.",
            "Zeus was actually the villain. Fight me.",
            "Ancient people knew more than we think.",
            "Which mythology is the most interesting?",
            "What's YOUR favorite myth?",
        ],
        "unsolved-mysteries": [
            "I think I know what happened. Hear me out.",
            "This will never be solved.",
            "The answer is obvious. Change my mind.",
            "What's YOUR theory?",
            "Drop your theories below 👇",
        ],
        "geography-facts": [
            "This country is underrated. Fight me.",
            "Americans can't find this on a map.",
            "Borders are just imaginary lines. Debate.",
            "Can YOU find this on a map?",
            "What's the strangest fact you know?",
        ],
        "ai-future-tech": [
            "AI is overhyped. Change my mind.",
            "This will replace your job. Accept it.",
            "We're not ready for this technology.",
            "Exciting or terrifying? You decide.",
            "What AI tool do YOU use most?",
        ],
        "philosophy": [
            "Free will doesn't exist. Change my mind.",
            "Morality is subjective. Fight me.",
            "Nothing actually matters. Or does it?",
            "What do YOU think the meaning of life is?",
            "Drop your philosophical hot take 👇",
        ],
        "book-summaries": [
            "This book is overrated. Change my mind.",
            "You should read the full book.",
            "Summaries miss the point. Fight me.",
            "What's YOUR favorite book?",
            "Should I summarize this book next?",
        ],
        "celebrity-net-worth": [
            "They don't deserve this wealth. Thoughts?",
            "Money doesn't buy happiness. Or does it?",
            "Who's YOUR favorite rich celebrity?",
            "Which celebrity is overpaid?",
            "Guess the net worth before I reveal it.",
        ],
        "survival-tips": [
            "You'd probably panic and forget all this.",
            "Most people couldn't survive a week outdoors.",
            "This tip could actually save your life.",
            "What would YOU do in this situation?",
            "Share YOUR survival tip below.",
        ],
        "sleep-relaxation": [
            "Does this actually work for you?",
            "What helps YOU fall asleep?",
            "Save this for tonight 😴",
            "Tag someone who needs better sleep.",
            "Sweet dreams 💤",
        ],
        "netflix-recommendations": [
            "This show is actually overrated - change my mind.",
            "The ending ruined the whole series.",
            "This is the most underrated show on Netflix.",
            "Hot take: this movie is a masterpiece.",
            "Comment your unpopular Netflix opinions!",
        ],
        "mockumentary-howmade": [
            "Wait, is this actually how it's made?",
            "This can't be real... right?",
            "The factory workers deserve better pay.",
            "This process seems inefficient.",
            "Someone fact-check this please.",
        ],
    },
    "opinion_requests": [
        "Rate this from 1-10 👇",
        "Would you do this? Yes or no",
        "Which is better - A or B?",
        "What would YOU have done?",
        "Drop a 🔥 if you agree",
        "Comment your answer below",
        "Tell me I'm wrong 👇",
        "Who else experienced this?",
    ],
    "fill_in_blank": {
        "scary-stories": [
            "The scariest place I've ever been is ____",
            "I'll never forget the time I ____",
            "The creepiest thing that happened to me was ____",
            "My biggest fear is ____",
        ],
        "finance": [
            "My biggest money mistake was ____",
            "I wish I had known ____ about money earlier",
            "The best financial advice I got was ____",
            "I save money by ____",
        ],
        "luxury": [
            "The most expensive thing I own is ____",
            "My dream luxury item is ____",
            "The most overrated luxury brand is ____",
            "I would never pay ____ for anything",
        ],
        "true-crime": [
            "The case I'm most obsessed with is ____",
            "I think the real killer was ____",
            "The scariest true crime story is ____",
        ],
        "psychology-facts": [
            "My biggest cognitive bias is ____",
            "I realized I was ____ after learning this",
            "The psychology fact that changed me is ____",
        ],
        "history": [
            "The historical figure I admire most is ____",
            "I wish I could witness ____ in history",
            "The most underrated historical event is ____",
        ],
        "motivation": [
            "The quote that motivates me is ____",
            "My biggest life lesson is ____",
            "I'm currently working on ____",
        ],
        "space-astronomy": [
            "I think alien life looks like ____",
            "The space fact that blows my mind is ____",
            "I want NASA to explore ____ next",
        ],
        "conspiracy-mysteries": [
            "The theory I actually believe is ____",
            "The one thing they're hiding is ____",
            "I can't explain ____ that happened to me",
        ],
        "animal-facts": [
            "My favorite animal is ____",
            "The coolest animal ability is ____",
            "I want to see ____ in the wild",
        ],
        "health-wellness": [
            "My best health tip is ____",
            "I improved my health by ____",
            "The habit that changed my life is ____",
        ],
        "relationship-advice": [
            "My biggest relationship lesson is ____",
            "The best dating advice is ____",
            "I knew they were the one when ____",
        ],
        "tech-gadgets": [
            "The gadget I can't live without is ____",
            "My dream tech product is ____",
            "The most overrated tech is ____",
        ],
        "life-hacks": [
            "The hack that saved me time is ____",
            "I wish I knew ____ sooner",
            "My weird but effective hack is ____",
        ],
        "mythology-folklore": [
            "My favorite mythological creature is ____",
            "The god/goddess I relate to is ____",
            "The scariest myth I know is ____",
        ],
        "unsolved-mysteries": [
            "The mystery I want solved is ____",
            "My theory about this case is ____",
            "The creepiest unsolved mystery is ____",
        ],
        "geography-facts": [
            "The country I want to visit is ____",
            "The strangest border fact I know is ____",
            "A place that surprised me is ____",
        ],
        "ai-future-tech": [
            "The AI tool I use daily is ____",
            "I think AI will ____ in 10 years",
            "The tech I'm most excited about is ____",
        ],
        "philosophy": [
            "My personal philosophy is ____",
            "The question I think about most is ____",
            "I believe the meaning of life is ____",
        ],
        "book-summaries": [
            "The book that changed my life is ____",
            "Everyone should read ____",
            "My current read is ____",
        ],
        "celebrity-net-worth": [
            "The celebrity I think is overpaid is ____",
            "My celebrity crush is ____",
            "I want the wealth of ____",
        ],
        "survival-tips": [
            "My emergency preparedness tip is ____",
            "I'd survive in ____ environment",
            "The skill everyone should learn is ____",
        ],
        "sleep-relaxation": [
            "I fall asleep to ____",
            "My nighttime routine is ____",
            "The thing that relaxes me is ____",
        ],
        "netflix-recommendations": [
            "The show I binged in one sitting was ____",
            "My favorite Netflix original is ____",
            "A movie that made me cry is ____",
        ],
        "mockumentary-howmade": [
            "The weirdest factory I've seen makes ____",
            "I always wondered how ____ was made",
            "The most interesting manufacturing process is ____",
        ],
    },
    "part_2_bait": [
        "Should I make a part 2?",
        "Comment 'MORE' if you want the full story",
        "Part 2? Let me know 👇",
        "This is just the beginning...",
        "Want to know what happened next?",
        "Follow for part 2",
        "The rest of the story drops tomorrow",
    ],
}


# =============================================================================
# PINNED COMMENT TEMPLATES
# =============================================================================

PINNED_COMMENTS = {
    "scary-stories": [
        "What's the scariest thing that's ever happened to you? 👇",
        "Fun fact: the original story was even longer. Want the full version?",
        "This happened in [location]. Anyone else from there? 👀",
        "I have 10 more stories like this. Which one should I post next?",
        "POV: You're reading this at 3AM 💀",
        "The ending isn't even the scariest part... comment if you caught it",
    ],
    "finance": [
        "Okay but which of these money mistakes have YOU made? Be honest 😂",
        "Drop your biggest money regret below 👇",
        "What's your net worth goal for this year?",
        "Controversial take: most financial advice is garbage. Agree?",
        "Which tip are you implementing first? Let me know!",
        "I learned this the hard way. Don't make my mistakes.",
    ],
    "luxury": [
        "Would you buy this if you could afford it? 👇",
        "Guess the price before I reveal it!",
        "What's on your luxury wishlist?",
        "Real or fake? Can you tell the difference?",
        "What's the most you've ever spent on one item?",
        "Drop a 💎 if this is your dream",
    ],
    "true-crime": [
        "What's YOUR theory about this case? 👇",
        "Should I cover more cases like this?",
        "Which case should I investigate next?",
        "The evidence doesn't add up. What do you think happened?",
        "Share if someone you know should hear this story.",
        "Follow for more true crime breakdowns 🔍",
    ],
    "psychology-facts": [
        "Which of these do YOU do? Be honest 👇",
        "Drop a 🧠 if you learned something new!",
        "Tag someone who needs to see this.",
        "What psychology topic should I cover next?",
        "Fun fact: you're doing one of these right now.",
        "Follow for daily psychology facts!",
    ],
    "history": [
        "What historical event should I cover next? 👇",
        "Did you learn about this in school? Most didn't.",
        "Drop a 📚 if you love history!",
        "Share with someone who loves history.",
        "Which historical figure fascinates you most?",
        "Follow for more hidden history!",
    ],
    "motivation": [
        "Save this for when you need motivation 💪",
        "Tag someone who needs to hear this today.",
        "What's YOUR biggest goal right now? 👇",
        "Drop a 🔥 if you're ready to level up!",
        "Which advice resonated with you most?",
        "Follow for daily motivation!",
    ],
    "space-astronomy": [
        "What space topic should I cover next? 🚀",
        "Drop a 🌟 if space blows your mind!",
        "Which planet is most fascinating to you?",
        "Do you think we're alone in the universe? 👇",
        "Share with a space nerd friend!",
        "Follow for more cosmic content!",
    ],
    "conspiracy-mysteries": [
        "What do YOU think really happened? 👇",
        "Drop a 👁️ if you're a truth seeker!",
        "Which theory should I cover next?",
        "Share if you think people need to see this.",
        "What's the one thing they're hiding?",
        "Follow for more hidden truths!",
    ],
    "animal-facts": [
        "What's YOUR favorite animal? 👇",
        "Drop a 🐾 if you learned something new!",
        "Which animal should I feature next?",
        "Tag a friend who would love this!",
        "Share if you're an animal lover!",
        "Follow for amazing animal facts!",
    ],
    "health-wellness": [
        "Which tip are you trying first? 👇",
        "Save this for later! 📌",
        "Tag someone who needs to see this.",
        "What health topic should I cover next?",
        "Drop a 💚 if health is your priority!",
        "Follow for more wellness tips!",
    ],
    "relationship-advice": [
        "Does this describe anyone you know? 👇",
        "Tag someone who needs to hear this!",
        "What relationship topic should I cover next?",
        "Drop a ❤️ if you've experienced this.",
        "Save this for someone who needs it.",
        "Follow for more relationship wisdom!",
    ],
    "tech-gadgets": [
        "Would you buy this? Yes or no? 👇",
        "What gadget should I review next?",
        "Drop a 📱 if you're a tech lover!",
        "Tag a friend who needs to see this!",
        "Android or iPhone? Comment below!",
        "Follow for more tech content!",
    ],
    "life-hacks": [
        "Did this hack work for you? 👇",
        "Save this before you forget! 📌",
        "Tag someone who needs this hack!",
        "What hack should I show next?",
        "Drop a 💡 if this blew your mind!",
        "Follow for more life-changing hacks!",
    ],
    "mythology-folklore": [
        "What myth should I tell next? 👇",
        "Drop a ⚡ if you love mythology!",
        "Which god/goddess is your favorite?",
        "Share with someone who loves ancient stories!",
        "Greek, Norse, or Egyptian mythology? Vote below!",
        "Follow for more legendary tales!",
    ],
    "unsolved-mysteries": [
        "What's YOUR theory? 👇",
        "Which mystery should I cover next?",
        "Drop a 🔍 if you're obsessed with mysteries!",
        "Share if you want this case solved.",
        "The truth is out there... what do you think?",
        "Follow for more unsolved cases!",
    ],
    "geography-facts": [
        "Can you find this on a map? 🗺️",
        "What country should I feature next?",
        "Drop a 🌍 if you love geography!",
        "Tag a friend who's a geography nerd!",
        "What's the most interesting place you've visited?",
        "Follow for more world facts!",
    ],
    "ai-future-tech": [
        "Are you excited or scared about this? 👇",
        "What AI tool should I cover next?",
        "Drop a 🤖 if you're ready for the future!",
        "Share with someone who needs to know about this.",
        "How do you think AI will change your job?",
        "Follow for more future tech!",
    ],
    "philosophy": [
        "What's YOUR take on this? 👇",
        "Drop a 🧠 if this made you think!",
        "Which philosopher should I cover next?",
        "Share with someone who loves deep conversations.",
        "What question keeps you up at night?",
        "Follow for more philosophical content!",
    ],
    "book-summaries": [
        "What book should I summarize next? 👇",
        "Drop a 📖 if you're a book lover!",
        "Have you read this book? What did you think?",
        "Save this summary for later!",
        "Tag a friend who needs to read this!",
        "Follow for more book summaries!",
    ],
    "celebrity-net-worth": [
        "Guess the net worth before I reveal it! 👇",
        "Which celebrity should I cover next?",
        "Drop a 💰 if this surprised you!",
        "Who do you think is overpaid?",
        "Share if you found this interesting!",
        "Follow for more celebrity money facts!",
    ],
    "survival-tips": [
        "Could YOU survive this situation? 👇",
        "What survival topic should I cover next?",
        "Save this - it could save your life! 📌",
        "Drop a 🏕️ if you're a survivalist!",
        "Tag someone who needs to see this!",
        "Follow for more survival tips!",
    ],
    "sleep-relaxation": [
        "Save this for bedtime 😴",
        "Did this help you relax? 👇",
        "Tag someone who needs better sleep!",
        "What should I post next for relaxation?",
        "Sweet dreams 💤",
        "Follow for more calming content!",
    ],
    "netflix-recommendations": [
        "Have you watched this yet? 👇",
        "What show should I recommend next?",
        "Save this for your next binge session! 📺",
        "Drop a 🍿 if you love binge-watching!",
        "Tag someone who needs a show recommendation!",
        "Follow for more Netflix finds!",
    ],
    "mockumentary-howmade": [
        "Did you learn something new today? 🏭",
        "What product should I explain next?",
        "The factory workers approve this message 👷",
        "Drop a ⚙️ if you love how things are made!",
        "Tag someone who needs to see this process!",
        "Follow for more totally real factory tours!",
    ],
}


# =============================================================================
# LOOP STRUCTURE TEMPLATES
# =============================================================================

LOOP_STRUCTURES = {
    "audio_loop": {
        "description": "End and begin with the same sound/music beat",
        "technique": "Match last 0.5s audio to first 0.5s",
    },
    "visual_loop": {
        "description": "Last frame matches or leads into first frame",
        "technique": "End on same visual element as opening",
    },
    "narrative_loop": {
        "description": "End mid-sentence, continue from the start",
        "examples": [
            "And that's when I realized... [loop to start]",
            "I still don't know what it was, but... [loop]",
            "To this day, I wonder... [loop]",
        ],
    },
    "question_loop": {
        "description": "End with question that the video answers",
        "examples": [
            "Why did I go back? [loop to start showing why]",
            "How did I survive? [loop to story]",
            "What was watching me? [loop to reveal]",
        ],
    },
}


# =============================================================================
# HOOK GENERATION FUNCTIONS
# =============================================================================


def get_first_frame_hook(
    niche: str,
    hook_type: str = None,
    custom_context: str = None,
) -> dict:
    """
    Get a first-frame hook for a video.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        hook_type: Optional specific type (text_question, shocking_statement, etc.)
        custom_context: Optional context to customize the hook

    Returns:
        Dict with hook text and metadata
    """
    if niche not in FIRST_FRAME_HOOKS:
        niche = "scary-stories"  # Fallback

    hooks = FIRST_FRAME_HOOKS[niche]

    if hook_type and hook_type in hooks:
        hook_list = hooks[hook_type]
    else:
        # Random type selection with weights
        types = list(hooks.keys())
        weights = [0.3, 0.3, 0.2, 0.2]  # Favor questions and statements
        hook_type = random.choices(types, weights=weights)[0]
        hook_list = hooks[hook_type]

    hook_text = random.choice(hook_list)

    return {
        "text": hook_text,
        "type": hook_type,
        "niche": niche,
        "display_duration": 3.0,  # Seconds to display
        "position": "center",  # Where to overlay text
    }


def get_pattern_interrupt(interrupt_type: str = None) -> dict:
    """
    Get a pattern interrupt technique.

    Args:
        interrupt_type: "audio" or "visual", or None for random

    Returns:
        Dict with interrupt details
    """
    if interrupt_type is None:
        interrupt_type = random.choice(["audio", "visual"])

    technique = random.choice(PATTERN_INTERRUPTS[interrupt_type])

    return {
        "type": interrupt_type,
        "technique": technique,
        "duration": 0.5,  # Seconds
    }


def get_mid_video_hook(niche: str, hook_format: str = None) -> dict:
    """
    Get a mid-video retention hook.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        hook_format: "verbal", "text_overlay", or "visual_cues"

    Returns:
        Dict with hook details
    """
    if hook_format is None:
        hook_format = random.choice(["verbal", "text_overlay"])

    if hook_format == "verbal":
        if niche not in MID_VIDEO_HOOKS["verbal"]:
            niche = "scary-stories"
        hook_content = random.choice(MID_VIDEO_HOOKS["verbal"][niche])
    elif hook_format == "text_overlay":
        hook_content = random.choice(MID_VIDEO_HOOKS["text_overlay"])
    else:
        hook_content = random.choice(MID_VIDEO_HOOKS["visual_cues"])

    return {
        "format": hook_format,
        "content": hook_content,
        "insert_at_percent": random.randint(30, 50),  # 30-50% mark
        "duration": 2.0 if hook_format == "text_overlay" else None,
    }


def get_comment_trigger(niche: str, trigger_type: str = None) -> dict:
    """
    Get a comment-triggering ending.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        trigger_type: Type of trigger or None for random

    Returns:
        Dict with trigger details
    """
    if trigger_type is None:
        trigger_type = random.choice(
            [
                "controversial_endings",
                "opinion_requests",
                "fill_in_blank",
                "part_2_bait",
            ]
        )

    if trigger_type == "controversial_endings":
        if niche not in COMMENT_TRIGGERS["controversial_endings"]:
            niche = "scary-stories"
        content = random.choice(COMMENT_TRIGGERS["controversial_endings"][niche])
    elif trigger_type == "opinion_requests":
        content = random.choice(COMMENT_TRIGGERS["opinion_requests"])
    elif trigger_type == "fill_in_blank":
        if niche not in COMMENT_TRIGGERS["fill_in_blank"]:
            niche = "scary-stories"
        content = random.choice(COMMENT_TRIGGERS["fill_in_blank"][niche])
    else:
        content = random.choice(COMMENT_TRIGGERS["part_2_bait"])

    return {
        "type": trigger_type,
        "content": content,
        "niche": niche,
    }


def get_pinned_comment(niche: str) -> str:
    """
    Get a pinned comment suggestion.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Suggested pinned comment text
    """
    if niche not in PINNED_COMMENTS:
        niche = "scary-stories"
    return random.choice(PINNED_COMMENTS[niche])


def get_loop_structure(loop_type: str = None) -> dict:
    """
    Get loop structure guidance.

    Args:
        loop_type: Specific loop type or None for recommendation

    Returns:
        Dict with loop structure details
    """
    if loop_type is None:
        loop_type = random.choice(list(LOOP_STRUCTURES.keys()))

    structure = LOOP_STRUCTURES[loop_type].copy()
    structure["type"] = loop_type

    return structure


def generate_engagement_package(niche: str) -> dict:
    """
    Generate a complete engagement package for a video.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Dict with all engagement elements
    """
    return {
        "first_frame_hook": get_first_frame_hook(niche),
        "pattern_interrupt": get_pattern_interrupt(),
        "mid_video_hook": get_mid_video_hook(niche),
        "comment_trigger": get_comment_trigger(niche),
        "pinned_comment": get_pinned_comment(niche),
        "loop_structure": get_loop_structure(),
    }


# =============================================================================
# STANDALONE USAGE
# =============================================================================

# All available niches
ALL_NICHES = list(FIRST_FRAME_HOOKS.keys())

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate engagement hooks for TikTok content"
    )
    parser.add_argument(
        "--niche",
        "-n",
        choices=ALL_NICHES,
        default="scary-stories",
        help="Content niche",
    )
    parser.add_argument(
        "--full",
        "-f",
        action="store_true",
        help="Generate full engagement package",
    )

    args = parser.parse_args()

    if args.full:
        package = generate_engagement_package(args.niche)
        logger.info("Generated engagement package", niche=args.niche, package=package)
    else:
        hook = get_first_frame_hook(args.niche)
        logger.info("Generated hook", hook_text=hook["text"], hook_type=hook["type"])
