"""
Hashtag Strategy Module

⚠️ NOTE: No modern equivalent exists yet in src/faceless/services/.
This module will be migrated in a future update.

Implements the hashtag ladder system from FUTURE_IMPROVEMENTS.md
Provides niche-specific hashtag recommendations for maximum reach
"""

import random

from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# HASHTAG LADDER SYSTEM
# =============================================================================
# Structure:
# LEVEL 1 (1x): Mega hashtag - 10B+ views
# LEVEL 2 (2x): Niche broad - 100M-1B views
# LEVEL 3 (2x): Niche specific - 1M-100M views
# LEVEL 4 (1x): Trending topic - Currently relevant
# LEVEL 5 (1x): Original series - Your own branding

HASHTAG_LADDER = {
    "scary-stories": {
        "mega": [
            "#fyp",
            "#foryou",
            "#viral",
            "#trending",
            "#foryoupage",
        ],
        "niche_broad": [
            "#scarystory",
            "#horror",
            "#creepy",
            "#scary",
            "#spooky",
            "#haunted",
            "#paranormal",
            "#ghost",
        ],
        "niche_specific": [
            "#nosleep",
            "#redditstories",
            "#truescary",
            "#horrorstory",
            "#creepypasta",
            "#scarystories",
            "#horrortok",
            "#creepytok",
            "#truehorror",
            "#scaryvideos",
            "#nightmarefuel",
            "#darkstories",
        ],
        "series_suggestions": [
            "#MidnightArchives",
            "#3AMStories",
            "#DarkTales",
            "#CreepyCorner",
            "#HauntedHistories",
        ],
    },
    "finance": {
        "mega": [
            "#fyp",
            "#foryou",
            "#viral",
            "#trending",
            "#foryoupage",
        ],
        "niche_broad": [
            "#moneytok",
            "#finance",
            "#investing",
            "#money",
            "#wealth",
            "#stocks",
            "#crypto",
        ],
        "niche_specific": [
            "#financetips",
            "#moneytips",
            "#personalfinance",
            "#debtfree",
            "#budgeting",
            "#financialfreedom",
            "#moneymindset",
            "#investingtips",
            "#stockmarket",
            "#wealthbuilding",
            "#passiveincome",
            "#sidehustle",
        ],
        "series_suggestions": [
            "#MoneyMistakeMonday",
            "#WealthWednesday",
            "#FinanceFriday",
            "#MoneyMindset",
            "#WealthSecrets",
        ],
    },
    "luxury": {
        "mega": [
            "#fyp",
            "#foryou",
            "#viral",
            "#trending",
            "#foryoupage",
        ],
        "niche_broad": [
            "#luxury",
            "#luxurylifestyle",
            "#rich",
            "#wealthy",
            "#millionaire",
            "#billionaire",
        ],
        "niche_specific": [
            "#luxurylife",
            "#expensivethings",
            "#luxurycars",
            "#luxuryhomes",
            "#luxurywatches",
            "#highend",
            "#luxuryliving",
            "#richlifestyle",
            "#luxurytravel",
            "#finerthings",
            "#quietluxury",
            "#oldmoney",
        ],
        "series_suggestions": [
            "#PriceOfPerfection",
            "#BillionaireBreakdown",
            "#GuessThePrice",
            "#QuietLuxurySecrets",
            "#MegaYachtMonday",
        ],
    },
    "true-crime": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#truecrime",
            "#crime",
            "#mystery",
            "#detective",
            "#coldcase",
            "#investigation",
        ],
        "niche_specific": [
            "#truecrimetok",
            "#truecrimecommunity",
            "#murdermystery",
            "#serialkiller",
            "#unsolvedmurder",
            "#crimejunkie",
            "#crimetok",
            "#truecrimestory",
            "#forensics",
            "#coldcasefile",
        ],
        "series_suggestions": [
            "#ColdCaseFiles",
            "#CrimeBreakdown",
            "#UnsolvedCases",
            "#TrueCrimeTuesday",
            "#JusticeForVictims",
        ],
    },
    "psychology-facts": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#psychology",
            "#psychologyfacts",
            "#mentalhealth",
            "#mindset",
            "#brain",
            "#humanpsychology",
        ],
        "niche_specific": [
            "#psychtok",
            "#psychologytok",
            "#darkpsychology",
            "#bodylanguage",
            "#manipulation",
            "#emotionalintelligence",
            "#cognitivebias",
            "#humanbehavior",
            "#psychologytricks",
            "#mindblown",
        ],
        "series_suggestions": [
            "#PsychFacts",
            "#MindGames",
            "#BrainSecrets",
            "#PsychologyDaily",
            "#HumanMindExplained",
        ],
    },
    "history": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#history",
            "#historyfacts",
            "#historical",
            "#ancienthistory",
            "#worldhistory",
            "#historytok",
        ],
        "niche_specific": [
            "#historytiktok",
            "#didyouknow",
            "#historylesson",
            "#ancientcivilization",
            "#ww2",
            "#medievalhistory",
            "#historynerd",
            "#historybuff",
            "#thisday",
            "#historicalfacts",
        ],
        "series_suggestions": [
            "#HistoryUnveiled",
            "#TodayInHistory",
            "#ForgottenHistory",
            "#HistoricalMoments",
            "#EpicHistory",
        ],
    },
    "motivation": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#motivation",
            "#motivational",
            "#inspiration",
            "#success",
            "#mindset",
            "#grind",
        ],
        "niche_specific": [
            "#motivationtok",
            "#successmindset",
            "#motivationalquotes",
            "#selfimprovement",
            "#goalgetter",
            "#neverquit",
            "#hustle",
            "#millionairemindset",
            "#winnermentality",
            "#believeinyourself",
        ],
        "series_suggestions": [
            "#MondayMotivation",
            "#DailyMotivation",
            "#SuccessSecrets",
            "#MindsetMonday",
            "#RiseAndGrind",
        ],
    },
    "space-astronomy": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#space",
            "#astronomy",
            "#universe",
            "#cosmos",
            "#nasa",
            "#science",
        ],
        "niche_specific": [
            "#spacetok",
            "#spacefacts",
            "#astrophotography",
            "#planets",
            "#galaxy",
            "#blackhole",
            "#stars",
            "#solarsystem",
            "#jameswebb",
            "#spaceexploration",
        ],
        "series_suggestions": [
            "#CosmicFacts",
            "#SpaceDaily",
            "#UniverseExplained",
            "#AstronomyFacts",
            "#CosmicWonders",
        ],
    },
    "conspiracy-mysteries": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#conspiracy",
            "#conspiracytheory",
            "#mystery",
            "#hidden",
            "#secrets",
            "#truth",
        ],
        "niche_specific": [
            "#conspiracytok",
            "#conspiracytheories",
            "#deepstate",
            "#hiddentruth",
            "#wakeup",
            "#questioneverything",
            "#coverup",
            "#illuminati",
            "#mysterytok",
            "#strangerthings",
        ],
        "series_suggestions": [
            "#HiddenTruth",
            "#ConspiracyCorner",
            "#RedPilled",
            "#DeepDive",
            "#TheRabbitHole",
        ],
    },
    "animal-facts": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#animals",
            "#wildlife",
            "#nature",
            "#animalfacts",
            "#animalsoftiktok",
            "#naturelover",
        ],
        "niche_specific": [
            "#animaltok",
            "#wildlifephotography",
            "#amazinganimals",
            "#animalworld",
            "#didyouknow",
            "#crazyanimalfacts",
            "#oceanlife",
            "#jungleanimals",
            "#endangeredspecies",
            "#animallovers",
        ],
        "series_suggestions": [
            "#AnimalFactsDaily",
            "#WildlifeFriday",
            "#NatureNuggets",
            "#CreatureFeature",
            "#AnimalKingdom",
        ],
    },
    "health-wellness": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#health",
            "#wellness",
            "#healthy",
            "#fitness",
            "#healthylifestyle",
            "#selfcare",
        ],
        "niche_specific": [
            "#healthtok",
            "#wellnesstok",
            "#healthtips",
            "#nutrition",
            "#healthyhabits",
            "#holistichealth",
            "#mentalwellness",
            "#healthyliving",
            "#wellnessjourney",
            "#healthyhacks",
        ],
        "series_suggestions": [
            "#WellnessWednesday",
            "#HealthHacks",
            "#DailyWellness",
            "#HealthyYou",
            "#WellnessWins",
        ],
    },
    "relationship-advice": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#relationships",
            "#relationshipadvice",
            "#dating",
            "#love",
            "#couples",
            "#datingadvice",
        ],
        "niche_specific": [
            "#relationshiptok",
            "#datingtok",
            "#toxicrelationship",
            "#redflag",
            "#greenflag",
            "#situationship",
            "#attachmentstyle",
            "#loveadvice",
            "#couplegoals",
            "#relationshiptips",
        ],
        "series_suggestions": [
            "#RedFlagAlert",
            "#DatingDiaries",
            "#LoveLessons",
            "#RelationshipReality",
            "#HeartToHeart",
        ],
    },
    "tech-gadgets": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#tech",
            "#technology",
            "#gadgets",
            "#techtok",
            "#techreview",
            "#innovation",
        ],
        "niche_specific": [
            "#techgadgets",
            "#newtech",
            "#cooltech",
            "#gadgetreview",
            "#smartphone",
            "#apple",
            "#android",
            "#techlife",
            "#futuretech",
            "#techlover",
        ],
        "series_suggestions": [
            "#TechTuesday",
            "#GadgetOfTheDay",
            "#TechReviews",
            "#FutureTech",
            "#TechFinds",
        ],
    },
    "life-hacks": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#lifehacks",
            "#hacks",
            "#diy",
            "#tips",
            "#tricks",
            "#howto",
        ],
        "niche_specific": [
            "#lifehack",
            "#hacksoftiktok",
            "#homehacks",
            "#cleaninghacks",
            "#organizationhacks",
            "#moneysavinghacks",
            "#productivityhacks",
            "#kitchenhacks",
            "#smartliving",
            "#lifetips",
        ],
        "series_suggestions": [
            "#HackOfTheDay",
            "#LifeHackFriday",
            "#SmartHacks",
            "#HacksYouNeed",
            "#GameChanger",
        ],
    },
    "mythology-folklore": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#mythology",
            "#folklore",
            "#myths",
            "#legends",
            "#ancientmyths",
            "#gods",
        ],
        "niche_specific": [
            "#mythologytok",
            "#greekmythology",
            "#norsemythology",
            "#egyptianmythology",
            "#mythicalcreatures",
            "#ancientgods",
            "#legendsandmyths",
            "#folkloretok",
            "#mythsandlegends",
            "#mythologyfacts",
        ],
        "series_suggestions": [
            "#MythMonday",
            "#LegendaryTales",
            "#GodsAndMonsters",
            "#MythologyExplained",
            "#AncientMysteries",
        ],
    },
    "unsolved-mysteries": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#mystery",
            "#unsolved",
            "#mysterious",
            "#unexplained",
            "#coldcase",
            "#missing",
        ],
        "niche_specific": [
            "#unsolvedmysteries",
            "#mysterytok",
            "#coldcasefiles",
            "#missingpersons",
            "#strangemysteries",
            "#disappearances",
            "#unsolvedcases",
            "#mysteryfiles",
            "#creepymysteries",
            "#paranormalmystery",
        ],
        "series_suggestions": [
            "#MysteryMonday",
            "#UnsolvedFiles",
            "#ColdCaseChronicles",
            "#StillUnsolved",
            "#MysteryDeepDive",
        ],
    },
    "geography-facts": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#geography",
            "#maps",
            "#world",
            "#countries",
            "#travel",
            "#earth",
        ],
        "niche_specific": [
            "#geographytok",
            "#geographyfacts",
            "#mapfacts",
            "#worldfacts",
            "#countryfacts",
            "#bordergore",
            "#geopolitics",
            "#travelfacts",
            "#amazingplaces",
            "#worldgeography",
        ],
        "series_suggestions": [
            "#GeographyFriday",
            "#WorldFacts",
            "#MapMania",
            "#CountrySpotlight",
            "#GeographyNerd",
        ],
    },
    "ai-future-tech": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#ai",
            "#artificialintelligence",
            "#future",
            "#technology",
            "#futuristic",
            "#innovation",
        ],
        "niche_specific": [
            "#aitok",
            "#chatgpt",
            "#aiart",
            "#robotics",
            "#machinelearning",
            "#futuretech",
            "#aitools",
            "#techfuture",
            "#singularity",
            "#airevolution",
        ],
        "series_suggestions": [
            "#AIDaily",
            "#FutureFriday",
            "#TechOfTomorrow",
            "#AIExplained",
            "#FutureIsNow",
        ],
    },
    "philosophy": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#philosophy",
            "#philosophical",
            "#deepthoughts",
            "#wisdom",
            "#thinking",
            "#existential",
        ],
        "niche_specific": [
            "#philosophytok",
            "#stoicism",
            "#existentialism",
            "#philosophyquotes",
            "#thinkdeep",
            "#lifephilosophy",
            "#philosophers",
            "#wisdomtok",
            "#criticalthinking",
            "#meaningoflife",
        ],
        "series_suggestions": [
            "#PhilosophyFriday",
            "#DeepThoughts",
            "#WisdomWednesday",
            "#ThinkDifferent",
            "#PhilosophyBites",
        ],
    },
    "book-summaries": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#books",
            "#booktok",
            "#reading",
            "#booksummary",
            "#bookclub",
            "#literature",
        ],
        "niche_specific": [
            "#booksummaries",
            "#bookrecommendations",
            "#mustread",
            "#selfhelpbooks",
            "#bookreviews",
            "#readinglist",
            "#bookworm",
            "#booklover",
            "#nonfiction",
            "#bookstoread",
        ],
        "series_suggestions": [
            "#BookOfTheWeek",
            "#5MinuteBooks",
            "#BookBreakdown",
            "#ReadThisBook",
            "#BookWisdom",
        ],
    },
    "celebrity-net-worth": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#celebrity",
            "#celebrities",
            "#networth",
            "#rich",
            "#famous",
            "#entertainment",
        ],
        "niche_specific": [
            "#celebritynetworth",
            "#howmuch",
            "#richcelebrities",
            "#celebritylife",
            "#famousrich",
            "#moneycelebrities",
            "#starworth",
            "#billionairecelebs",
            "#celebmoney",
            "#hollywoodrich",
        ],
        "series_suggestions": [
            "#NetWorthRevealed",
            "#CelebMoney",
            "#HowRichAreThey",
            "#StarWealth",
            "#CelebrityFinances",
        ],
    },
    "survival-tips": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#survival",
            "#survivalist",
            "#prepper",
            "#outdoors",
            "#wilderness",
            "#bushcraft",
        ],
        "niche_specific": [
            "#survivaltips",
            "#survivaltok",
            "#survivalhacks",
            "#outdoorsurvival",
            "#emergencyprep",
            "#bugoutbag",
            "#wildernesssurvival",
            "#preppercommunity",
            "#survivalgear",
            "#survivalskills",
        ],
        "series_suggestions": [
            "#SurvivalSaturday",
            "#SurvivalHacks",
            "#PrepperTips",
            "#WildernessWisdom",
            "#SurviveThis",
        ],
    },
    "sleep-relaxation": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#sleep",
            "#relaxation",
            "#calm",
            "#peaceful",
            "#asmr",
            "#meditation",
        ],
        "niche_specific": [
            "#sleeptok",
            "#sleeptips",
            "#relaxing",
            "#sleephacks",
            "#insomnia",
            "#bettersleep",
            "#calmdown",
            "#peacefulvibes",
            "#nightroutine",
            "#sleepmusic",
        ],
        "series_suggestions": [
            "#SleepSounds",
            "#CalmNights",
            "#RelaxWithMe",
            "#SleepyTime",
            "#PeacefulDreams",
        ],
    },
    "netflix-recommendations": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#netflix",
            "#tvshows",
            "#movies",
            "#streaming",
            "#binge",
            "#whattowatch",
        ],
        "niche_specific": [
            "#netflixtok",
            "#netflixrecommendations",
            "#movienight",
            "#tvseries",
            "#bingewatching",
            "#streamingservice",
            "#moviereview",
            "#tvreview",
            "#hiddengems",
            "#underrated",
        ],
        "series_suggestions": [
            "#NetflixFinds",
            "#WatchThis",
            "#StreamingPicks",
            "#BingeGuide",
            "#HiddenGems",
        ],
    },
    "mockumentary-howmade": {
        "mega": ["#fyp", "#foryou", "#viral", "#trending", "#foryoupage"],
        "niche_broad": [
            "#comedy",
            "#funny",
            "#humor",
            "#parody",
            "#satire",
            "#mockumentary",
        ],
        "niche_specific": [
            "#howitsmade",
            "#factorytour",
            "#comedyskit",
            "#absurdcomedy",
            "#deadpancomedy",
            "#fakeducational",
            "#comedytok",
            "#parodyvideo",
            "#satiretok",
            "#weirdtok",
        ],
        "series_suggestions": [
            "#HowItsMadeParody",
            "#FakeFactory",
            "#TotallyReal",
            "#DefinitelyFactual",
            "#FactoryTours",
        ],
    },
}


# =============================================================================
# TRENDING TOPIC SUGGESTIONS (Updated periodically)
# =============================================================================

TRENDING_TOPICS = {
    "scary-stories": [
        "#storytime",
        "#paranormaltiktok",
        "#hauntedtiktok",
        "#scaryseason",
        "#spookyseason",
        "#truecrime",
    ],
    "finance": [
        "#inflation",
        "#recession",
        "#stocktips",
        "#cryptotok",
        "#realestate",
        "#housingmarket",
    ],
    "luxury": [
        "#luxurytok",
        "#aspirational",
        "#lifestyle",
        "#goals",
        "#dreamlife",
        "#expensive",
    ],
    "true-crime": [
        "#justicefor",
        "#criminalminds",
        "#dateline",
        "#crimewatch",
        "#murderpodcast",
        "#crimestory",
    ],
    "psychology-facts": [
        "#therapytok",
        "#mentalhealthawareness",
        "#anxietytips",
        "#narcissist",
        "#toxicpeople",
        "#selfawareness",
    ],
    "history": [
        "#onthisday",
        "#historymemes",
        "#ancientrome",
        "#worldwar",
        "#historicaldocumentary",
        "#historynerds",
    ],
    "motivation": [
        "#morningroutine",
        "#productivitytips",
        "#disciplined",
        "#levelup",
        "#becomingher",
        "#bossup",
    ],
    "space-astronomy": [
        "#marsrover",
        "#spacex",
        "#jameswebbtelescope",
        "#solarsystem",
        "#alienlife",
        "#cosmology",
    ],
    "conspiracy-mysteries": [
        "#governmentcover",
        "#strangebutrue",
        "#whattheydonttellyou",
        "#openminds",
        "#mysteriesoftheworld",
        "#decodethetruth",
    ],
    "animal-facts": [
        "#cuteanimals",
        "#wildanimals",
        "#oceantok",
        "#animalbehavior",
        "#naturedocumentary",
        "#savewildlife",
    ],
    "health-wellness": [
        "#guthealthtok",
        "#sleephacks",
        "#hormonehealth",
        "#antiinflammatory",
        "#biohacking",
        "#healthychoices",
    ],
    "relationship-advice": [
        "#datingtips",
        "#lovelife",
        "#exes",
        "#breakupadvice",
        "#healthyrelationship",
        "#communicationtips",
    ],
    "tech-gadgets": [
        "#iphone",
        "#samsunggalaxy",
        "#smartwatch",
        "#gadget2024",
        "#techunboxing",
        "#musthavetech",
    ],
    "life-hacks": [
        "#amazonfinds",
        "#tiktokfinds",
        "#cleaningtok",
        "#organizewithme",
        "#savemoney",
        "#smartshopping",
    ],
    "mythology-folklore": [
        "#fantasybooks",
        "#witchtok",
        "#pagantok",
        "#mythicmondays",
        "#legendarybeasts",
        "#ancientwisdom",
    ],
    "unsolved-mysteries": [
        "#mysteriesexplained",
        "#lostcivilizations",
        "#paranormalactivity",
        "#strangedisappearances",
        "#mysterybox",
        "#unsolvable",
    ],
    "geography-facts": [
        "#traveltok",
        "#worldtravel",
        "#destinationguide",
        "#interestingfacts",
        "#mapporn",
        "#traveltheworld",
    ],
    "ai-future-tech": [
        "#openai",
        "#gpt4",
        "#aitools",
        "#aivideo",
        "#midjourney",
        "#techtrends",
    ],
    "philosophy": [
        "#mindfulness",
        "#stoic",
        "#ancientwisdom",
        "#deepquotes",
        "#lifelessons",
        "#perspective",
    ],
    "book-summaries": [
        "#bookrecs",
        "#readwithme",
        "#atomichabits",
        "#bookchallenge",
        "#goodreads",
        "#bestbooks",
    ],
    "celebrity-net-worth": [
        "#celebritynews",
        "#hollywoodgossip",
        "#richlist",
        "#billionaires",
        "#famouspeoples",
        "#starnews",
    ],
    "survival-tips": [
        "#outdooradventure",
        "#campinghacks",
        "#shtf",
        "#homesteading",
        "#offgrid",
        "#emergencykit",
    ],
    "sleep-relaxation": [
        "#asmrsounds",
        "#sleepytime",
        "#relaxingmusic",
        "#nighttime",
        "#winddown",
        "#peacefulsleep",
    ],
    "netflix-recommendations": [
        "#bingeworthy",
        "#newreleases",
        "#streamingwars",
        "#netflixoriginal",
        "#watchparty",
        "#weekendvibes",
    ],
    "mockumentary-howmade": [
        "#comedytok",
        "#parody",
        "#absurdhumor",
        "#deadpan",
        "#factorylife",
        "#educational",
    ],
}


# =============================================================================
# HASHTAG GENERATION FUNCTIONS
# =============================================================================


def generate_hashtag_set(
    niche: str,
    series_tag: str = None,
    include_trending: bool = True,
    total_count: int = 7,
) -> list:
    """
    Generate an optimized hashtag set using the ladder system.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        series_tag: Optional custom series hashtag
        include_trending: Whether to include trending topics
        total_count: Target number of hashtags (5-7 recommended)

    Returns:
        List of hashtags in optimal order
    """
    if niche not in HASHTAG_LADDER:
        niche = "scary-stories"  # Fallback

    ladder = HASHTAG_LADDER[niche]
    hashtags = []

    # Level 1: 1 mega hashtag
    hashtags.append(random.choice(ladder["mega"]))

    # Level 2: 2 niche broad hashtags
    broad_tags = random.sample(
        ladder["niche_broad"], min(2, len(ladder["niche_broad"]))
    )
    hashtags.extend(broad_tags)

    # Level 3: 2 niche specific hashtags
    specific_tags = random.sample(
        ladder["niche_specific"], min(2, len(ladder["niche_specific"]))
    )
    hashtags.extend(specific_tags)

    # Level 4: 1 trending topic (if enabled)
    if include_trending and niche in TRENDING_TOPICS:
        hashtags.append(random.choice(TRENDING_TOPICS[niche]))

    # Level 5: 1 series/original tag
    if series_tag:
        hashtags.append(series_tag if series_tag.startswith("#") else f"#{series_tag}")
    else:
        hashtags.append(random.choice(ladder["series_suggestions"]))

    # Trim to target count
    return hashtags[:total_count]


def generate_hashtag_string(
    niche: str,
    series_tag: str = None,
    include_trending: bool = True,
) -> str:
    """
    Generate hashtags as a ready-to-paste string.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        series_tag: Optional custom series hashtag
        include_trending: Whether to include trending topics

    Returns:
        Space-separated hashtag string
    """
    hashtags = generate_hashtag_set(niche, series_tag, include_trending)
    return " ".join(hashtags)


def get_series_suggestions(niche: str) -> list:
    """
    Get suggested series hashtags for a niche.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        List of suggested series hashtags
    """
    if niche not in HASHTAG_LADDER:
        return []
    return HASHTAG_LADDER[niche].get("series_suggestions", [])


def get_all_hashtags(niche: str) -> dict:
    """
    Get all hashtags organized by level for a niche.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Dict with hashtags by level
    """
    if niche not in HASHTAG_LADDER:
        return {}

    result = HASHTAG_LADDER[niche].copy()
    if niche in TRENDING_TOPICS:
        result["trending"] = TRENDING_TOPICS[niche]
    return result


def analyze_hashtag_coverage(hashtags: list, niche: str) -> dict:
    """
    Analyze a hashtag set for ladder coverage.

    Args:
        hashtags: List of hashtags to analyze
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Dict with analysis of coverage by level
    """
    if niche not in HASHTAG_LADDER:
        return {"error": f"Unknown niche: {niche}"}

    ladder = HASHTAG_LADDER[niche]
    normalized = [h.lower() for h in hashtags]

    analysis = {
        "total_count": len(hashtags),
        "mega_count": sum(
            1 for h in normalized if h in [t.lower() for t in ladder["mega"]]
        ),
        "broad_count": sum(
            1 for h in normalized if h in [t.lower() for t in ladder["niche_broad"]]
        ),
        "specific_count": sum(
            1 for h in normalized if h in [t.lower() for t in ladder["niche_specific"]]
        ),
        "has_series": any(
            h.lower() in [t.lower() for t in ladder["series_suggestions"]]
            for h in normalized
        ),
        "recommendations": [],
    }

    # Generate recommendations
    if analysis["mega_count"] == 0:
        analysis["recommendations"].append(
            "Add at least 1 mega hashtag (#fyp, #foryou)"
        )
    if analysis["broad_count"] < 2:
        analysis["recommendations"].append("Add more niche broad hashtags")
    if analysis["specific_count"] < 2:
        analysis["recommendations"].append("Add more niche specific hashtags")
    if not analysis["has_series"]:
        analysis["recommendations"].append("Consider adding a series/branded hashtag")
    if analysis["total_count"] < 5:
        analysis["recommendations"].append("Use 5-7 hashtags for optimal reach")
    if analysis["total_count"] > 10:
        analysis["recommendations"].append("Consider reducing to 5-7 hashtags")

    return analysis


# =============================================================================
# CONTENT-SPECIFIC HASHTAG SUGGESTIONS
# =============================================================================


def get_format_specific_hashtags(niche: str, format_name: str) -> list:
    """
    Get additional hashtags specific to a content format.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        format_name: Name of the TikTok format being used

    Returns:
        List of additional format-specific hashtags
    """
    format_hashtags = {
        "scary-stories": {
            "pov_horror": ["#pov", "#povhorror", "#scarypov"],
            "rules_of_location": ["#rules", "#ruleshorror", "#therules"],
            "creepy_text_messages": ["#texthorror", "#creepytexts", "#scarytext"],
            "split_screen_reaction": ["#reaction", "#scaryfootage"],
        },
        "finance": {
            "financial_red_flags_dating": [
                "#redflag",
                "#datingadvice",
                "#moneyredflags",
            ],
            "things_that_scream_broke": ["#broke", "#moneymistakes"],
            "roast_my_spending": ["#roast", "#duet", "#spendinghabits"],
            "i_did_the_math": ["#math", "#calculations", "#themath"],
        },
        "luxury": {
            "guess_the_price": ["#guesstheprice", "#pricereveal", "#expensive"],
            "cheap_vs_expensive": ["#cheapvsexpensive", "#spotthefake", "#realvsfake"],
            "luxury_asmr": ["#asmr", "#satisfying", "#luxuryasmr"],
        },
    }

    if niche not in format_hashtags:
        return []
    return format_hashtags[niche].get(format_name, [])


# =============================================================================
# STANDALONE USAGE
# =============================================================================

# All available niches
ALL_NICHES = list(HASHTAG_LADDER.keys())

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate optimized hashtags for TikTok content"
    )
    parser.add_argument(
        "--niche",
        "-n",
        choices=ALL_NICHES,
        default="scary-stories",
        help="Content niche",
    )
    parser.add_argument(
        "--series",
        "-s",
        help="Custom series hashtag",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all hashtags for niche",
    )
    parser.add_argument(
        "--analyze",
        "-a",
        nargs="+",
        help="Analyze provided hashtags",
    )

    args = parser.parse_args()

    if args.list:
        logger.info("Listing hashtags", niche=args.niche)
        all_tags = get_all_hashtags(args.niche)
        for level, tags in all_tags.items():
            logger.info("Hashtag level", level=level.upper(), tags=", ".join(tags))
    elif args.analyze:
        analysis = analyze_hashtag_coverage(args.analyze, args.niche)
        logger.info("Hashtag analysis complete", **analysis)
    else:
        hashtags = generate_hashtag_string(args.niche, args.series)
        logger.info("Generated hashtags", niche=args.niche, hashtags=hashtags)
