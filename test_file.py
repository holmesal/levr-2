#import string
#from lib.stem.porter import PorterStemmer
#from lib.tokenize.regexp import WhitespaceTokenizer
#from common_word_list import blacklist
#def tokenize_and_stem(text,filtered=True):
#	'''
#	Used to create a list of indexable strings from a single multiword string
#	Tokenizes the input string, and then stems each of the tokens
#	Also converts each token to lowercase
#	@param text: the text to be converted
#	@type text: str
#	@param filtered: Determines whether or not the tokens should be filtered
#	@type filtered: bool
#	@return: a list of tokenized and stemmed words
#	@rtype: list
#	'''
#	# tokenize the motherfuckers
#	tokens = tokenize(text)
#	# filter out black words if you so desire
#	if filtered == True:
#		tokens = filter_stop_words(tokens)
#	# Let's get to the root of this.
#	tokens = stem(tokens)
#	return tokens
#def tokenize_and_filter(text):
#	'''
#	Used to create a list of words that can be used for popular searches and stuff
#	@param text: the text to be converted
#	@type text: str
#	@return: a list of tokenized and filtered words
#	@rtype: list
#	'''
#	tokens = tokenize(text)
#	tokens = filter_stop_words(tokens)
#	return tokens
#def tokenize(text):
#	'''
#	Tokenizes an input string
#	Replaces certain delimeters with spaces, and removes punctuation
#	@param text: A string composed of at least one word
#	@type text: str
#	@return: A list of tokenized words
#	'''
#	# a list of chars that will be replaced with spaces
#	excludu = ['_','/',',','-','|']
#
#	# remove punctuation
#	for punct in string.punctuation:
#		if punct not in excludu:
#			text = text.replace(punct,'')
#	
#	# replace special chars with spaces
#	for character in excludu:
#		text = text.replace(character,' ')
#	
#	# tokenize the mofo!
#	tokenizer = WhitespaceTokenizer()
#	
#	# create tokens
#	return [token.lower() for token in tokenizer.tokenize(text)]
#def stem(tokens):
#	'''
#	Creates stemmed versions of words in a tokenized list
#	@param tokens: A tokenized list of words
#	@type tokens: list
#	@return: A list of stem words
#	@rtype: list
#	'''
#	stemmer = PorterStemmer()
#	return [stemmer.stem(token) for token in tokens]
#def filter_stop_words(tokens):
#	'''
#	Filters a list of strings
#	@param word_list: A tokenized, but not stemmed word list
#	@type word_list: list
#	@return: a list of words without stop words
#	@rtype: list
#	'''
#	return filter(lambda x: x.isdigit() == False \
#				and x not in blacklist,tokens)
#
