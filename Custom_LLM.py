import re
from groq import Groq



class groq_llm:
    def __init__(self) -> None:
        self.Groq_client = Groq()

    def extract_query(self, text: str) -> str:
        pattern = r"```(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches[0] if matches else text

    def generate_query(self, question, sys_prompt):
        chat_completion = self.Groq_client.chat.completions.create(
            messages=[
                    {
                            "role":"system",
                            "content":sys_prompt
                    },
                    {
                        "role": "user",
                        "content": question,
                    }
            ],
            model="llama-3.1-70b-versatile",
        )
        data =  chat_completion.choices[0].message.content
        data = self.extract_query(data)
        return data
    
    def decide(self, sql_all_data_prompt, sql_llm_prompt, neo4j_llm_prompt, question):
        chat_completion = self.Groq_client.chat.completions.create(
            messages=[
                    {
                            "role":"system",
                            "content":'''You are an assistant that helps to form nice and human understandable answers.
                    The information part contains the provided information that you must use to construct an answer.
                    The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
                    Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
                    Always Prioritize the Manually Provided Context, if Manually Provided Context is not present then construct the answer from `SQL_DATABASE_CONTEXT`
                    and `NEO4J_DATABASE_CONTEXT`.
                    Here is an example:

                    Information:
                    Manually Provided Context: The actors from the movie Jumanji are Robin Williams, Bradley Pierce, Kirsten Dunst, and Jonathan Hyde.

                    SQL_DATABASE_CONTEXT (by running the following query: 
                    SELECT actors FROM movies WHERE title LIKE 'Jumanji': 
                    [('Robin Williams|Bradley Pierce|Kirsten Dunst|Jonathan Hyde',)]

                    NEO4J_DATABASE_CONTEXT (by running the following query:  
                    MATCH (p:Person)-[:ACTED_IN]->(m:Movie {title: "Jumanji"}) RETURN p.name): 
                    [('p.name': 'Jonathan Hyde'), ('p.name': 'Kirsten Dunst'), ('p.name': 'Bradley Pierce'), ('p.name': 'Robin Williams')]

                    Question: actors from jumanji?

                    Helpful Answer: The actors from the movie Jumanji are Robin Williams, Bradley Pierce, Kirsten Dunst, and Jonathan Hyde.

                    Follow this example when generating answers.
                    If the provided information is empty, say that you don't know the answer.'''
                    },
                    {
                        "role": "user",
                        "content": f'''Information:
                                        {sql_all_data_prompt}\n\n{sql_llm_prompt}\n\n{neo4j_llm_prompt}

                                        Question: {question}
                                        Helpful Answer:''',
                                        }
            ],
            model="llama-3.1-70b-versatile",
        )
        data =  chat_completion.choices[0].message.content
        return data
    
    def sql_db_all(self, question, data):
        chat_completion = self.Groq_client.chat.completions.create(
            messages=[
                    {
                            "role":"system",
                            "content":'''You are an assistant that helps to form nice and human understandable answers.
                    The information part contains the provided information that you must use to construct an answer.
                    The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
                    Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
                    Here is an example:

                    Information:
                    SQL_DATABASE_CONTEXT (by searching for main keywords, in this case ['jumanji']):(NOTE: Before analyzing this part, convert this data in a table and make the schema as column headers. once done analyze this.)
                    schema: ['movieId', 'released', 'title', 'actors', 'director', 'genres', 'imdbRating']
                    Data: 
                    [['movieId:2', 'released:1995-12-15', 'title:Jumanji', 'actors:Robin Williams|Bradley Pierce|Kirsten Dunst|Jonathan Hyde', 'director:Joe Johnston', 'genres:Adventure|Children|Fantasy', 'imdbRating:6.9']]

                    Question: actors from jumanji?

                    Helpful Answer: The actors from the movie Jumanji are Robin Williams, Bradley Pierce, Kirsten Dunst, and Jonathan Hyde.

                    Follow this example when generating answers.
                    If the provided information is empty, say that you don't know the answer.
                    NOTE:Do not include any explanations or apologies in your responses.
                         Do not respond to any questions that might ask anything else than for you to construct a Answer.
                         Do not include any text except the generated Answer.'''
                    },
                    {
                        "role": "user",
                        "content": f'''Information:
                                        {data}

                                        Question: {question}
                                        Helpful Answer:''',
                                        }
            ],
            model="llama-3.1-70b-versatile",
        )
        data =  chat_completion.choices[0].message.content
        return data
