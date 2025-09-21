"""
Configuration for article categorization including keywords, patterns, and rules.
"""

# Comprehensive keyword mappings for each category with weights
CATEGORY_CONFIG = {
    'sports': {
        'keywords': {
            'high_weight': {
                # Australian sports
                'afl', 'aflw', 'nrl', 'rugby', 'cricket', 'a-league', 'netball',
                # International sports
                'football', 'soccer', 'tennis', 'golf', 'basketball', 'baseball',
                'swimming', 'athletics', 'cycling', 'boxing', 'mma', 'ufc',
                # Olympics and major events
                'olympics', 'commonwealth games', 'world cup', 'grand prix',
                'grand slam', 'championship', 'tournament', 'premiership',
                # Specific Australian teams/leagues
                'broncos', 'raiders', 'storm', 'roosters', 'rabbitohs', 'eels',
                'bulldogs', 'tigers', 'panthers', 'sharks', 'warriors', 'titans',
                'cowboys', 'knights', 'dragons', 'manly', 'eagles',
                # AFL teams
                'crows', 'lions', 'blues', 'magpies', 'bombers', 'dockers',
                'cats', 'suns', 'giants', 'hawks', 'demons', 'kangaroos',
                'power', 'tigers', 'saints', 'swans', 'eagles'
            },
            'medium_weight': {
                'team', 'teams', 'player', 'players', 'coach', 'coaching',
                'match', 'game', 'fixture', 'season', 'round', 'final', 'finals',
                'win', 'wins', 'won', 'loss', 'loses', 'lost', 'draw', 'tied',
                'score', 'scores', 'scored', 'goal', 'goals', 'point', 'points',
                'stadium', 'ground', 'arena', 'field', 'court', 'track',
                'training', 'fitness', 'injury', 'injured', 'comeback',
                'debut', 'retirement', 'veteran', 'rookie', 'draft'
            },
            'contextual': {
                'defeat', 'victory', 'champion', 'winner', 'medal', 'trophy',
                'record', 'performance', 'competition', 'league', 'club',
                'fan', 'fans', 'crowd', 'spectator', 'attendance'
            }
        },
        'url_patterns': [
            '/sport/', '/sports/', '/afl/', '/nrl/', '/cricket/', '/tennis/',
            '/golf/', '/rugby/', '/football/', '/basketball/', '/olympics/'
        ],
        'content_indicators': [
            'played against', 'final score', 'half time', 'full time',
            'minutes remaining', 'overtime', 'extra time', 'penalty',
            'referee', 'umpire', 'offside', 'foul', 'yellow card', 'red card'
        ],
        'exclude_keywords': {
            'entertainment', 'movie', 'film', 'music', 'concert', 'album'
        }
    },

    'finance': {
        'keywords': {
            'high_weight': {
                # Australian financial terms
                'asx', 'aud', 'rba', 'reserve bank', 'asic', 'apra',
                # General finance
                'shares', 'stock', 'stocks', 'market', 'markets', 'trading',
                'investment', 'investor', 'portfolio', 'dividend', 'earnings',
                'profit', 'revenue', 'income', 'expense', 'budget', 'cost',
                'price', 'prices', 'inflation', 'deflation', 'interest rate',
                'economy', 'economic', 'gdp', 'recession', 'growth',
                'bank', 'banking', 'loan', 'mortgage', 'credit', 'debt',
                'currency', 'dollar', 'exchange rate', 'forex'
            },
            'medium_weight': {
                'business', 'company', 'companies', 'corporation', 'startup',
                'industry', 'sector', 'ceo', 'cfo', 'executive', 'board',
                'announcement', 'merger', 'acquisition', 'ipo', 'listing',
                'quarterly', 'annual', 'report', 'results', 'forecast',
                'analyst', 'analysis', 'recommendation', 'upgrade', 'downgrade'
            },
            'contextual': {
                'money', 'financial', 'economic', 'commercial', 'trade',
                'sales', 'purchase', 'buy', 'sell', 'invest', 'funding'
            }
        },
        'url_patterns': [
            '/business/', '/finance/', '/economy/', '/money/', '/market/',
            '/asx/', '/shares/', '/investment/', '/banking/'
        ],
        'content_indicators': [
            'asx:', 'share price', 'market cap', 'p/e ratio', 'eps',
            'basis points', 'percentage', '%', '$', 'million', 'billion'
        ],
        'exclude_keywords': {
            'sports', 'music', 'entertainment', 'lifestyle', 'health'
        }
    },

    'lifestyle': {
        'keywords': {
            'high_weight': {
                'health', 'wellness', 'fitness', 'diet', 'nutrition',
                'exercise', 'workout', 'yoga', 'meditation', 'mindfulness',
                'food', 'recipe', 'cooking', 'chef', 'restaurant', 'cafe',
                'travel', 'holiday', 'vacation', 'destination', 'tourism',
                'fashion', 'style', 'beauty', 'skincare', 'makeup',
                'relationship', 'dating', 'marriage', 'family', 'parenting',
                'home', 'garden', 'interior', 'design', 'decoration',
                'pet', 'pets', 'dog', 'cat', 'animal'
            },
            'medium_weight': {
                'advice', 'tips', 'guide', 'how to', 'lifestyle',
                'personal', 'self', 'improvement', 'habit', 'routine',
                'mental health', 'psychology', 'therapy', 'stress',
                'hobby', 'leisure', 'entertainment', 'activity',
                'trend', 'trending', 'popular', 'viral', 'social'
            },
            'contextual': {
                'daily', 'weekly', 'routine', 'schedule', 'balance',
                'quality', 'improve', 'better', 'best', 'top', 'expert'
            }
        },
        'url_patterns': [
            '/lifestyle/', '/health/', '/food/', '/travel/', '/fashion/',
            '/beauty/', '/home/', '/garden/', '/relationships/', '/wellness/'
        ],
        'content_indicators': [
            'according to experts', 'study shows', 'research suggests',
            'tips for', 'how to', 'step by step', 'benefits of'
        ],
        'exclude_keywords': {
            'afl', 'nrl', 'cricket', 'shares', 'asx', 'market', 'economy'
        }
    },

    'music': {
        'keywords': {
            'high_weight': {
                'music', 'song', 'songs', 'album', 'albums', 'track', 'tracks',
                'artist', 'artists', 'musician', 'musicians', 'band', 'bands',
                'singer', 'vocalist', 'performer', 'concert', 'concerts',
                'gig', 'gigs', 'tour', 'touring', 'festival', 'festivals',
                'record', 'recording', 'studio', 'producer', 'production',
                'single', 'ep', 'lp', 'vinyl', 'cd', 'streaming', 'spotify',
                'aria', 'grammy', 'award', 'nomination', 'chart', 'charts',
                'billboard', 'top 40', 'hit', 'hits', 'platinum', 'gold'
            },
            'medium_weight': {
                'genre', 'rock', 'pop', 'hip hop', 'rap', 'jazz', 'blues',
                'country', 'folk', 'electronic', 'classical', 'indie',
                'alternative', 'punk', 'metal', 'reggae', 'soul', 'r&b',
                'instrument', 'guitar', 'piano', 'drums', 'bass', 'violin',
                'lyrics', 'melody', 'rhythm', 'beat', 'sound', 'audio',
                'venue', 'stage', 'performance', 'live', 'acoustic'
            },
            'contextual': {
                'listen', 'hear', 'play', 'sing', 'compose', 'write',
                'release', 'debut', 'latest', 'new', 'upcoming', 'announced'
            }
        },
        'url_patterns': [
            '/music/', '/entertainment/music/', '/arts/music/', '/culture/music/',
            '/concerts/', '/festivals/', '/albums/', '/artists/'
        ],
        'content_indicators': [
            'available on', 'streaming on', 'released on', 'features',
            'collaboration', 'feat.', 'ft.', 'remix', 'cover', 'tribute'
        ],
        'exclude_keywords': {
            'afl', 'nrl', 'cricket', 'sport', 'team', 'game', 'match',
            'asx', 'shares', 'market', 'business', 'economy'
        }
    }
}

# URL pattern weights for classification
URL_PATTERN_WEIGHTS = {
    'high': 0.8,    # Strong URL indicator (e.g., /sport/, /business/)
    'medium': 0.6,  # Moderate URL indicator (e.g., /news/sport/)
    'low': 0.3      # Weak URL indicator (e.g., /entertainment/)
}

# Keyword weights for scoring
KEYWORD_WEIGHTS = {
    'high_weight': 3.0,
    'medium_weight': 2.0,
    'contextual': 1.0
}

# Text section weights (title is most important)
TEXT_SECTION_WEIGHTS = {
    'title': 3.0,
    'summary': 2.0,
    'content': 1.0,
    'tags': 1.5
}

# Confidence thresholds for different classification methods
CONFIDENCE_THRESHOLDS = {
    'keyword': 0.6,
    'hybrid': 0.7,
    'ml': 0.8
}