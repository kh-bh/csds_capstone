import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

reviews_df = pd.read_csv('reviews_matched.csv')

# 1. Clean and prepare text data
# Ensure missing review text is removed
reviews_df = reviews_df.dropna(subset=['review_text']).copy()

stop_words_expansion = ['hospital', 'just', 'like', 'got', 'went', 'came', 'go'
]

# Merge standard sklearn English stop words with our expanded list
from sklearn.feature_extraction import text
custom_stop_words = list(text.ENGLISH_STOP_WORDS.union(stop_words_expansion))

# 2. Vectorize the review text into a document-term matrix
# Filter out words appearing in >85% or <10 documents to improve cluster quality
vectorizer = CountVectorizer(
    max_df=0.85,
    min_df=10,
    stop_words=custom_stop_words,
    token_pattern=r'(?u)\b[a-zA-Z]{3,}\b'  # Only words with 3+ letters
)

doc_term_matrix = vectorizer.fit_transform(reviews_df['review_text'])

# 3. Train the LDA Model
NUM_TOPICS = 10  # Adjust based on how many topics you want to extract

lda_model = LatentDirichletAllocation(
    n_components=NUM_TOPICS,
    max_iter=15,
    learning_method='online',
    random_state=42,
    n_jobs=-1  # Use all available CPU cores
)

lda_output = lda_model.fit_transform(doc_term_matrix)

# 4. Display the top words for each discovered topic
def print_top_words(model, feature_names, n_top_words=10):
    for topic_idx, topic in enumerate(model.components_):
        top_features_ind = topic.argsort()[:-n_top_words - 1:-1]
        top_words = [feature_names[i] for i in top_features_ind]
        print(f"Topic #{topic_idx + 1}: {', '.join(top_words)}")

feature_names = vectorizer.get_feature_names_out()
print("--- Discovered Review Topics ---")
print_top_words(lda_model, feature_names, n_top_words=10)

# 5. Assign dominant topic and topic probabilities back to the DataFrame
reviews_df['dominant_topic'] = lda_output.argmax(axis=1) + 1
reviews_df['topic_confidence'] = lda_output.max(axis=1)

# Optional: Add topic labels based on your findings (example mapping)
# topic_labels = {1: "ER Wait Times", 2: "Bedside Manner", 3: "Billing & Admin", 4: "Facilities", 5: "Surgery & Care"}
# reviews_df['topic_label'] = reviews_df['dominant_topic'].map(topic_labels)

# View distribution of reviews across topics
print("\n--- Review Count per Topic ---")
print(reviews_df['dominant_topic'].value_counts().sort_index())

# Map the 10 LDA topics to 4 high-level operational categories
topic_to_category = {
    1: 'Admin, Billing & Communication',
    2: 'Specialized & Pediatric Care',
    3: 'Facility Amenities & Cleanliness',
    4: 'Critical & Acute Clinical Conditions',
    5: 'ER & Family Treatment Experience',
    6: 'Positive Staff Praise & Gratitude',
    7: 'Wait Times & Patient Care',
    8: 'Wait Times & Patient Care',
    9: 'Positive Staff Praise & Gratitude',
    10: 'Wait Times & Patient Care'
}

# Apply to DataFrame
reviews_df['operational_category'] = reviews_df['dominant_topic'].map(topic_to_category)

# Display final category distribution
print("--- Reviews per Operational Category ---")
print(reviews_df['operational_category'].value_counts())
print("\nPercentage Distribution:")
print(reviews_df['operational_category'].value_counts(normalize=True) * 100)
reviews_df.to_csv('reviews_with_topics.csv', index=False)