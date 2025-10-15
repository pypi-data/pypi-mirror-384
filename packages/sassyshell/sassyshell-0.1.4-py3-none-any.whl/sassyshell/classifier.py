from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def find_most_similar_commands(new_query: str, database: list) -> list | None:
    if not database:
        return None
    
    documents = [' '.join(item['user_query']) for item in database]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    new_query_vector = vectorizer.transform([new_query])

    similarities = cosine_similarity(new_query_vector, tfidf_matrix).flatten()
    most_similar_indexes = similarities.argsort()[::-1]

    return [database[i] for i in most_similar_indexes[:5] if similarities[i] > 0.5]

