
# improties?
import praw, os, pickle
from pprint import pprint
from nltk.tokenize import sent_tokenize as tok_this_bitch

def split_into_individual_sentences(big_fucking_sentence):

    # make a new list to return
    chotu_chotu_sentences = []
    for each_chotu_sentence in tok_this_bitch(big_fucking_sentence):
        chotu_chotu_sentences += [each_chotu_sentence]

    # aapi de ene pachu D:
    return chotu_chotu_sentences

# initiate reddit instance
reddit = praw.Reddit(client_id='aUc0FksYX3zHpg',
         client_secret='T60FQVEhK4oz9g6YAaid_3Z0XxU',
         user_agent='bonnytalon')

# target subreddits for analysis
mbti_subreddits = ["worldnews", "technology", "news", "reactiongifs", "facebook"]
interest = ('facebook' or 'mark zuckerberg' or 'mark')

text_to_store = []
good_ops = []


for each_mbti in mbti_subreddits:

	for submission in reddit.subreddit(each_mbti).new(limit=1000):
		if interest in submission.title.lower():
			all_comments = submission.comments.list()
			for every_comment in all_comments:
				try:
					if ((interest in every_comment.body) and (every_comment.score > 10)):
						print(every_comment.body)
				except:
					pass
				try:
					for each_chotu_sentence in split_into_individual_sentences(every_comment.body):
						if 'http' not in each_chotu_sentence:
							text_to_store += [each_chotu_sentence]
				except:
					pass

	for submission in reddit.subreddit(each_mbti).hot(limit=1000):
		if interest in submission.title.lower():
			all_comments = submission.comments.list()
			for every_comment in all_comments:
				try:
					if ((interest in every_comment.body) and (every_comment.score > 10)):
						print(every_comment.body)
				except:
					pass
				try:
					for each_chotu_sentence in split_into_individual_sentences(every_comment.body):
						if 'http' not in each_chotu_sentence:
							text_to_store += [each_chotu_sentence]
				except:
					pass



# save pickle
with open('good_ops.pkl', 'wb') as handle:
    pickle.dump(good_ops, handle, protocol=pickle.HIGHEST_PROTOCOL)

# save pickle
with open('facebook_related_opinions.pkl', 'wb') as handle:
    pickle.dump(text_to_store, handle, protocol=pickle.HIGHEST_PROTOCOL)

# load pickle and show data gathered
with open('facebook_related_opinions.pkl', 'rb') as handle:
	print(pickle.load(handle)[:-4])
