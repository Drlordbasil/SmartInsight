import requests
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import schedule
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random

nltk.download('vader_lexicon')


class SearchEngine:
    def __init__(self, search_engine="Google"):
        self.search_engine = search_engine

    def search_query_processing(self, search_query):
        if self.search_engine == "Google":
            url = f"https://www.google.com/search?q={search_query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0;Win64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return response.text
            else:
                print("Error occurred while performing the search.")
                return None
        else:
            print("Currently, only Google search engine is supported.")
            return None


class NLPModel:
    def __init__(self, nlp_model="HuggingFace"):
        self.nlp_model = nlp_model

    def natural_language_processing(self, article_content):
        if self.nlp_model == "HuggingFace":
            summarization_pipeline = pipeline("summarization")
            sentiment_pipeline = SentimentIntensityAnalyzer()
            topic_modeling_pipeline = TfidfVectorizer()

            sentiment_scores = sentiment_pipeline.polarity_scores(article_content)["compound"]
            summary = summarization_pipeline(article_content, max_length=100, min_length=30, do_sample=False)[0][
                "summary_text"]

            # Tokenize and remove stopwords
            tokens = [word.lower() for word in nltk.word_tokenize(article_content) if word.isalnum()]
            stopwords = nltk.corpus.stopwords.words("english")
            tokens = [word for word in tokens if word not in stopwords]
            tokenized_content = " ".join(tokens)

            # Topic modeling using TF-IDF
            vectors = topic_modeling_pipeline.fit_transform([tokenized_content, summary])
            similarity_score = cosine_similarity(vectors[0].reshape(1, -1), vectors[1].reshape(1, -1))[0][0]

            return sentiment_scores, summary, similarity_score
        else:
            print("Currently, only HuggingFace NLP model is supported.")
            return None


class ContentAggregator:
    def __init__(self, search_engine="Google", nlp_model="HuggingFace"):
        self.search_engine = SearchEngine(search_engine)
        self.nlp_model = NLPModel(nlp_model)
        self.user_search_queries = []
        self.article_database = []
        self.recommendations = []

    def collect_search_queries(self):
        while True:
            search_query = input("Enter your search query (type 'stop' to exit): ")
            if search_query == "stop":
                break
            self.user_search_queries.append(search_query)

    def web_scraping(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        article_titles = []
        article_summaries = []
        article_urls = []

        for result in soup.find_all("div", class_="result"):
            title = result.find("h3").text
            summary = result.find("span", class_="st").text
            url = result.find("a")["href"]

            article_titles.append(title)
            article_summaries.append(summary)
            article_urls.append(url)

        return article_titles, article_summaries, article_urls

    def extract_article_content(self, url):
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            article_content = soup.find("div", class_="article-content")
            if article_content:
                return article_content.text.strip()
            else:
                print("Error occurred while extracting article content. No article content found.")
                return None
        else:
            print("Error occurred while extracting article content.")
            return None

    def content_filtering_and_ranking(self):
        filtered_articles = []

        for article in self.article_database:
            if article["sentiment_scores"] >= 0.5:
                filtered_articles.append(article)

        filtered_articles = sorted(filtered_articles,
                                   key=lambda x: (x["sentiment_scores"], x["similarity_score"]), reverse=True)

        return filtered_articles

    def personalized_content_recommendations(self):
        for article in self.article_database:
            if article["user_feedback"] == "interested":
                self.recommendations.append(article)

        self.recommendations = sorted(self.recommendations, key=lambda x: x["popularity"], reverse=True)

        return self.recommendations

    def autonomous_content_updates(self):
        def update_articles():
            new_articles = []

            for search_query in self.user_search_queries:
                html_content = self.search_engine.search_query_processing(search_query)
                if html_content is None:
                    continue
                article_titles, article_summaries, article_urls = self.web_scraping(html_content)

                for i in range(len(article_urls)):
                    article_content = self.extract_article_content(article_urls[i])
                    if article_content is None:
                        continue
                    sentiment_scores, summary, similarity_score = self.nlp_model.natural_language_processing(article_content)

                    new_articles.append({
                        "title": article_titles[i],
                        "summary": article_summaries[i],
                        "url": article_urls[i],
                        "content": article_content,
                        "sentiment_scores": sentiment_scores,
                        "summary_text": summary,
                        "similarity_score": similarity_score,
                        "popularity": random.randint(1, 100),
                        "user_feedback": ""
                    })

            self.article_database += new_articles

        schedule.every(1).day.do(update_articles)

        while True:
            schedule.run_pending()
            time.sleep(1)

    def api_integration_and_notifications(self):
        def send_email_recommendations():
            sender_email = "your_email@example.com"
            receiver_email = "receiver_email@example.com"
            password = "your_email_password"

            message = MIMEMultipart("alternative")
            message["Subject"] = "Content Recommendations"
            message["From"] = sender_email
            message["To"] = receiver_email

            content = MIMEText("Here are your personalized content recommendations:")

            recommendations = self.personalized_content_recommendations()

            for recommendation in recommendations:
                content += MIMEText(
                    f"\nTitle: {recommendation['title']}\nSummary: {recommendation['summary']}\nURL: {recommendation['url']}\n")

            message.attach(content)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())

        schedule.every(1).day.at("09:00").do(send_email_recommendations)

        while True:
            schedule.run_pending()
            time.sleep(1)


class RevenueGenerator:
    def __init__(self, content_aggregator):
        self.content_aggregator = content_aggregator

    def sponsored_content_recommendations(self):
        recommendations = self.content_aggregator.personalized_content_recommendations()

        for recommendation in recommendations:
            recommendation["sponsored"] = True

        return recommendations

    def advertising_partnerships(self):
        # Functionality for implementing advertising partnerships
        pass

    def affiliate_marketing(self):
        # Functionality for implementing affiliate marketing
        pass


class AIProgram:
    def __init__(self):
        self.content_aggregator = ContentAggregator()
        self.revenue_generator = RevenueGenerator(self.content_aggregator)

    def run(self):
        self.content_aggregator.collect_search_queries()

        while True:
            user_choice = input(
                "Enter your choice:\n1. Search and curate content\n2. Get personalized content recommendations\n3. Generate revenue\n4. Exit\n")

            if user_choice == "1":
                for search_query in self.content_aggregator.user_search_queries:
                    html_content = self.content_aggregator.search_engine.search_query_processing(search_query)
                    if html_content is None:
                        continue
                    article_titles, article_summaries, article_urls = self.content_aggregator.web_scraping(
                        html_content)

                    for i in range(len(article_urls)):
                        article_content = self.content_aggregator.extract_article_content(article_urls[i])
                        if article_content is None:
                            continue
                        sentiment_scores, summary, similarity_score = self.content_aggregator.nlp_model.natural_language_processing(
                            article_content)

                        self.content_aggregator.article_database.append({
                            "title": article_titles[i],
                            "summary": article_summaries[i],
                            "url": article_urls[i],
                            "content": article_content,
                            "sentiment_scores": sentiment_scores,
                            "summary_text": summary,
                            "similarity_score": similarity_score,
                            "popularity": random.randint(1, 100),
                            "user_feedback": ""
                        })

                print("Content has been successfully curated!")

            elif user_choice == "2":
                recommendations = self.content_aggregator.personalized_content_recommendations()

                for recommendation in recommendations:
                    print(f"Title: {recommendation['title']}")
                    print(f"Summary: {recommendation['summary']}")
                    print(f"URL: {recommendation['url']}")
                    print()

            elif user_choice == "3":
                revenue_choice = input(
                    "Enter your choice:\n1. Sponsored Content Recommendations\n2. Advertising Partnerships\n3. Affiliate Marketing\n")

                if revenue_choice == "1":
                    sponsored_recommendations = self.revenue_generator.sponsored_content_recommendations()

                    for recommendation in sponsored_recommendations:
                        print(f"Title: {recommendation['title']}")
                        print(f"Summary: {recommendation['summary']}")
                        print(f"URL: {recommendation['url']}")
                        print()

                elif revenue_choice == "2":
                    self.revenue_generator.advertising_partnerships()

                elif revenue_choice == "3":
                    self.revenue_generator.affiliate_marketing()

            elif user_choice == "4":
                break

            else:
                print("Invalid choice.")


if __name__ == "__main__":
    program = AIProgram()
    program.run()