#street words: http://www.enchantedlearning.com/wordlist/roadways.shtml
#1000 most common words: http://www.giwersworld.org/computers/linux/common-words-freq.phtml

blacklist = [
'establishment',
'restaurant',
'store',

#===============================================================================
# General Words
#===============================================================================
'receive',
'get',
' ',

#===============================================================================
# deal description words
#===============================================================================
'dollar',
'dollars',
'buy',
'sold',
'sells',
'beat',
'stuff',
'rule',
'rules',
'awesome',
'great',
'good',
'haha',
'cool',
'avenue',
'purchase',
'free',
'technology',
'inc',
'users',
'user',
'valid',

#===============================================================================
# Foursquare Words
#===============================================================================
'checkin',
'personcheckin', ## from person/checkin
'foursquare',
'unlocked',
'item',
'check',
"bar", 
"1st", 
"save", 
"location", 
"hm", 
"youll", 
"vuii", 
"visit", 
"unlock", 
"tufts", 
"thru", 
"submit", 
"sticks", 
"stadium", 
"skins", 
"session", 
"rpx", 
"request", 
"regal", 
"reception", 
"pm", 
"phoenix", 
"perfect", 
"monday", 
"minute", 
"medical", 
"landing", 
"join", 
"hitdx", 
"hgff", 
"guest", 
"greatest", 
"gdr", 
"fridays", 
"friday", 
"excludes", 
"everyday", 
"doctors", 
"diseases", 
"dirty", 
"cover", 
"complimentary", 
"clubla", 
"cheers", 
"checking", 
"catering", 
"benefits", 
"appointment", 
"answering", 
"activate", 
"acoustic", 
"aaa", 
"4sq", 
"1day", 
"11pm3pm",
"sports", 
"plaza", 
"sky", 
"signature", 
"offer", 
"happy", 
"enjoy", 
"youve", 
"w", 
"thursdays", 
"sunshine", 
"shape", 
"savings", 
"register", 
"purchases", 
"professor", 
"ordering", 
"link", 
"learn", 
"judy", 
"jock", 
"jealous", 
"id", 
"holders", 
"gets", 
"everyone", 
"estate", 
"employees", 
"eligible", 
"eclectic", 
"downstairs", 
"customers", 
"current", 
"columbus", 
"choices", 
"checked", 
"button", 
"broadway", 
"bitlyky0bnw", 
"bh", 
"bergdorf", 
"allowed", 
"admission",

#===============================================================================
# Roadway words
#===============================================================================
'ave',
'boulevard',
'blvd',
'bridge',
'circle',
'drive',
'dr',
'highway',
'hwy',
'lane',
'ln',
'street',
'st',
'parkway',
'pkwy',
'pass',
'passage',
'place',
'pl',
'road',
'rd',
'roadway',
'rdwy',
'route',
'rt',
'rte',
'span',
'speedway',
'street',
'st',
'str',
'trail',
'tr',
'walk',
'wk',
'walkway',
'way',

##Common Words
'the',
'of',
'and',
'to',
'a',
'in',
'that',
'is',
'was',
'he',
'for',
'it',
'with',
'as',
'his',
'on',
'be',
'at',
'by',
'i',
'this',
'had',
'not',
'are',
'but',
'from',
'or',
'have',
'an',
'they',
'which',
'one',
'were',
'you',
'all',
'her',
'she',
'there',
'would',
'their',
'we',
'him',
'been',
'has',
'when',
'who',
'will',
'no',
'more',
'if',
'out',
'its',
'so',
'up',
'said',
'what',
'about',
'than',
'into',
'them',
'can',
'only',
'other',
'time',
'new',
'some',
'could',
'these',
'two',
'may',
'first',
'then',
'do',
'any',
'like',
'my',
'now',
'over',
'such',
'our',
'man',
'me',
'even',
'most',
'made',
'after',
'also',
'well',
'did',
'many',
'before',
'must',
'years',
'back',
'through',
'much',
'where',
'your',
'way',
'down',
'should',
'because',
'long',
'each',
'just',
'state',
'people',
'those',
'too',
'how',
'mr',
'little',
'good',
'world',
'make',
'very',
'year',
'still',
'see',
'own',
'work',
'men',
'day',
'get',
'here',
'old',
'between',
'both',
'life',
'being',
'under',
'three',
'never',
'know',
'same',
'last',
'another',
'while',
'us',
'off',
'might',
'great',
'states',
'go',
'come',
'since',
'against',
'right',
'came',
'take',
'used',
'himself',
'few',
'house',
'use',
'place',
'during',
'high',
'without',
'again',
'home',
'around',
'small',
'however',
'found',
'mrs',
'part',
'school',
'thought',
'went',
'say',
'general',
'once',
'upon',
'every',
'left',
'war',
'dont',
'does',
'got',
'united',
'number',
'hand',
'course',
'until',
'always',
'away',
'public',
'something',
'fact',
'less',
'through',
'far',
'put',
'head',
'think',
'called',
'set',
'almost',
'enough',
'end',
'took',
'government',
'night',
'yet',
'system',
'better',
'four',
'nothing',
'told',
'eyes',
'going',
'president',
'why',
'days',
'present',
'point',
'didnt',
'look',
'find',
'asked',
'second',
'group',
'later',
'next',
'room',
'social',
'business',
'knew',
'program',
'give',
'half',
'side',
'face',
'toward',
'white',
'five',
'let',
'young',
'form',
'given',
'per',
'order',
'large',
'several',
'national',
'important',
'possible',
'rather',
'big',
'among',
'case',
'often',
'early',
'john',
'things',
'looked',
'ever',
'become',
'best',
'need',
'within',
'felt',
'along',
'children',
'saw',
'church',
'light',
'power',
'least',
'development',
'interest',
'others',
'open',
'thing',
'seemed',
'want',
'area',
'god',
'members',
'mind',
'help',
'country',
'service',
'turned',
'door',
'done',
'although',
'whole',
'line',
'problem',
'sense',
'certain',
'different',
'kind',
'began',
'thus',
'means',
'matter',
'perhaps',
'name',
'times',
'york',
'itself',
'action',
'human',
'above',
'week',
'company',
'free',
'example',
'hands',
'local',
'show',
'history',
'whether',
'act',
'either',
'gave',
'death',
'feet',
'today',
'across',
'body',
'past',
'quite',
'taken',
'anything',
'field',
'having',
'seen',
'word',
'car',
'experience',
'im',
'money',
'really',
'class',
'words',
'already',
'college',
'information',
'tell',
'making',
'sure',
'themselves',
'together',
'full',
'air',
'shall',
'held',
'known',
'period',
'keep',
'political',
'real',
'miss',
'probably',
'century',
'question',
'seems',
'behind',
'cannot',
'major',
'office',
'brought',
'special',
'whose',
'boy',
'cost',
'federal',
'economic',
'self',
'south',
'problems',
'heard',
'six',
'study',
'ago',
'became',
'moment',
'run',
'available',
'job',
'result',
'short',
'west',
'age',
'change',
'position',
'board',
'individual',
'reason',
'turn',
'close',
'areas',
'am',
'love',
'society',
'level',
'court',
'control',
'true',
'community',
'force',
'ill',
'type',
'front',
'center',
'future',
'hard',
'seem',
'clear',
'town',
'voice',
'wanted',
'common',
'girl',
'black',
'party',
'land',
'necessary',
'surface',
'top',
'following',
'rate',
'sometimes',
'tax',
'students',
'low',
'military',
'child',
'further',
'third',
'red',
'university',
'college',
'able',
'education',
'feel',
'provide',
'effect',
'morning',
'nations',
'total',
'near',
'road',
'stood',
'art',
'figure',
'outside',
'north',
'million',
'washington',
'leave',
'value',
'cut',
'usually',
'fire',
'plan',
'play',
'sound',
'therefore',
'english',
'evidence',
'strong',
'range',
'believe',
'living',
'peace',
'various',
'mean',
'modern',
'says',
'soon',
'lines',
'looking',
'schools',
'single',
'alone',
'longer',
'minutes',
'personal',
'process',
'secretary',
'gone',
'idea',
'months',
'situation',
'increase',
'nor',
'section',
'america',
'pressure',
'private',
'started',
'dark',
'dr',
'east',
'stage',
'finally',
'kept',
'call',
'needed',
'values',
'greater',
'expected',
'view',
'thats',
'space',
'ten',
'union',
'basis',
'spirit',
'brown',
'required',
'taking',
'complete',
'conditions',
'except',
'hundred',
'late',
'moved',
'ones',
'wrote',
'hours',
'return',
'support',
'attention',
'hour',
'live',
'particular',
'recent',
'data',
'hope',
'person',
'beyond',
'coming',
'dead',
'middle',
'cold',
'costs',
'else',
'forces',
'heart',
'material',
'couldnt',
'developed',
'feeling',
'fine',
'story',
'inside',
'lost',
'read',
'report',
'research',
'twenty',
'industry',
'instead',
'miles',
'added',
'amount',
'followed',
'makes',
'move',
'pay',
'basic',
'cant',
'including',
'building',
'defense',
'hold',
'reached',
'simply',
'tried',
'central',
'wide',
'committee',
'equipment',
'picture',
'island',
'simple',
'actually',
'care',
'religious',
'shown',
'friends',
'beginning',
'getting',
'higher',
'received',
'rest',
'sort',
'boys',
'doing',
'floor',
'foreign',
'terms',
'trying',
'indeed',
'administration',
'cent',
'difficult',
'subject',
'especially',
'meeting',
'earth',
'market',
'paper',
'passed',
'walked',
'blue',
'bring',
'county',
'labor',
'hall',
'natural',
'police',
'similar',
'training',
'england',
'final',
'growth',
'international',
'property',
'talk',
'working',
'written',
'congress',
'girls',
'start',
'wasnt',
'answer',
'hear',
'issue',
'purpose',
'suddenly',
'weeks',
'western',
'needs',
'stand',
'youre',
'considered',
'countries',
'fall',
'hair',
'likely',
'nation',
'lay',
'sat',
'cases',
'color',
'entire',
'french',
'happened',
'paid',
'production',
'ready',
'results',
'square',
'difference',
'earlier',
'involved',
'meet',
'step',
'stock',
'thinking',
'william',
'christian',
'letter',
'aid',
'increased',
'lot',
'month',
'particularly',
'whom',
'below',
'effort',
'knowledge',
'lower',
'points',
'sent',
'trade',
'using',
'industrial',
'size',
'yes',
'bad',
'bill',
'certainly',
'eye',
'ideas',
'temperature',
'addition',
'deal',
'due',
'method',
'methods',
'moral',
'reading',
'decided',
'directly',
'nearly',
'neither',
'questions',
'record',
'showed',
'statements',
'throughout',
'anyone',
'programs',
'try',
'according',
'member',
'physical',
'science',
'services',
'southern',
'hot',
'remember',
'soviet',
'strength',
'comes',
'normal',
'trouble',
'understand',
'volume',
'population',
'summer',
'trial',
'appeared',
'bed',
'concerned',
'district',
'led',
'merely',
'sales',
'student',
'direction',
'friend',
'maybe',
'piece',
'ran',
'continued',
'degree',
'direct',
'evening',
'game',
'green',
'husband',
'list',
'literature',
'plane',
'association',
'average',
'cause',
'generally',
'george',
'influence',
'met',
'provided',
'seven',
'systems',
'chance',
'changes',
'easy',
'former',
'freedom',
'hell',
'meaning',
'opened',
'shot',
'spring',
'ways',
'works',
'wrong',
'fear',
'organization',
'planning',
'series',
'term',
'theory',
'ask',
'effective',
'lead',
'myself',
'respect',
'stopped',
'wouldnt',
'clearly',
'efforts',
'forms',
'groups',
'movement',
'plant',
'truth',
'worked',
'based',
'beautiful',
'consider',
'farm',
'horse',
'mans',
'note',
'press',
'somewhat',
'treatment',
'arms',
'charge',
'placed',
'apparently',
'carried',
'feed',
'herself',
'hes',
'hit',
'ive',
'length',
'numbers',
'operation',
'persons',
'reaction',
'born',
'manner',
'oh',
'recently',
'running',
'approach',
'chief',
'deep',
'eight',
'immediately',
'larger',
'performance',
'price',
'sun',
'couple',
'gun',
'lived',
'main',
'stop',
'straight',
'heavy',
'image',
'march',
'opportunity',
'technical',
'test',
'understanding',
'writing',
'additional',
'british',
'decision',
'described',
'determined',
'europe',
'fiscal',
'progress',
'served',
'window',
'character',
'quality',
'religion',
'reported',
'responsibility',
'steps',
'appear',
'serious',
'account',
'ball',
'communist',
'corner',
'design',
'learned',
'moving',
'post',
'activity',
'forward',
'pattern',
'poor',
'slowly',
'specific',
'staff',
'types',
'activities',
'audience',
'choice',
'filled',
'growing',
'justice',
'latter',
'letters',
'nuclear',
'obtained',
'returned',
'democratic',
'doubt',
'obviously',
'parts',
'plans',
'thirty',
'established',
'figures',
'foot',
'function',
'include',
'leaders',
'mass',
'saying',
'standard',
'stay',
'attack',
'closed',
'drive',
'gives',
'speak',
'waiting',
'whatever',
'completely',
'covered',
'faith',
'hospital',
'language',
'race',
'season',
'wish',
'built',
'designed',
'distance',
'effects',
'extent',
'glass',
'income',
'lack',
'products',
'ahead',
'analysis',
'corps',
'elements',
'existence',
'expect',
'firm',
'married',
'principle',
'theres',
]