from groq import Groq
from Custom_LLM import groq_llm
import re
import json


llm = groq_llm()
Groq_client = Groq()

def extract_query(text: str) -> str:
    pattern = r"```(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0] if matches else text

def get_in_chunks(question, schema):
    chat_completion = Groq_client.chat.completions.create(
        messages=[
                {
                        "role":"system",
                        "content":"""analyze the question given below and return the main parts so that i can be easy for a semantic search. here are some examples:
                        Examples:
                        question: home for the Holidays, Screamers, Things to Do in Denver When You're Dead?, White Balloon which movie released first?, schema = ['movieId', 'released', 'title', 'actors', 'director', 'genres', 'imdbRating']
                        answer: {"entities":["home for the Holidays", "Screamers", "Things to Do in Denver When You're Dead" , "White Balloon"]}

                        question: which movies released in 1977-12-03, 1947-10-08 and 1877-1-04?
                        answer: {"entities":["1977-10-08", "1947-10-08", "1877-1-04"]}

                        question: which movie or movies are directed by Sean Penn and Noah Baumbach?
                        answer: {"entities":["Sean Penn", "Noah Baumbach"]}
                                        
                        question: Cast of Braveheart?
                        answer: {"entities":["Braveheart"]}

                        Note: Do not include any explanations or apologies in your responses.
                              Do not include any text except the generated statement.
                              Return only the text in json format and nothing else. and always keep the keys as "entities" as shown in the example.
                        """
                },
                {
                    "role": "user",
                    "content": f"question: {question}, schema = {schema}",
                }
        ],
        model="llama3-70b-8192",
    )
    data =  chat_completion.choices[0].message.content
    data = extract_query(data)
    query = json.loads(data)
    query = query['entities']
    return query

def create_query(schema):
        chat_completion = Groq_client.chat.completions.create(
            messages=[
                    {
                            "role":"system",
                            "content":"""analyze the format given below and create a similer code for the given input.note that the schema given is from the sql database
                                        schema: path: movies.csv, [('movieId', 3, None, None, None, None, 1, 32768, 63),
                                                                    ('released', 252, None, None, None, None, 1, 16, 255),
                                                                    ('title', 252, None, None, None, None, 1, 16, 255),
                                                                    ('actors', 252, None, None, None, None, 1, 16, 255),
                                                                    ('director', 252, None, None, None, None, 1, 16, 255),
                                                                    ('genres', 252, None, None, None, None, 1, 16, 255),
                                                                    ('imdbRating', 5, None, None, None, None, 1, 32768, 63)]
                                        sample neo4j code:
                                        MERGE (m:Movie {id: $movieId})
                                        SET m.released = date($released),
                                            m.title = $title,
                                            m.imdbRating = toFloat($imdbRating)
                                        FOREACH (director IN $director |
                                            MERGE (p:Person {name: trim(director)})
                                            MERGE (p)-[:DIRECTED]->(m))
                                        FOREACH (actor IN $actors |
                                            MERGE (p:Person {name: trim(actor)})
                                            MERGE (p)-[:ACTED_IN]->(m))
                                        FOREACH (genre IN $genres |
                                            MERGE (g:Genre {name: trim(genre)})
                                            MERGE (m)-[:IN_GENRE]->(g))
                                            
                                            Return only the code and nothing else."""
                    },
                    {
                        "role": "user",
                        "content": f"input: {schema}",
                    }
            ],
            model="llama3-70b-8192",
        )
        data =  chat_completion.choices[0].message.content
        query = extract_query(data)
        return query

def get_neo4j_query(conv):
    data = llm.generate_query(sys_prompt='''Do not include any explanations or apologies in your responses.
                                 Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
                                 Do not include any text except the generated Cypher statement.
                              ''', 
                            question=conv
                            )
    data= data.replace('cypher','')
    return data


def get_sql_query(conv):
    data = llm.generate_query(sys_prompt='''Do not include any explanations or apologies in your responses.
                                 Do not respond to any questions that might ask anything else than for you to construct a SQL statement.
                                 Do not include any text except the generated SQL statement.
                              ''', 
                            question=conv
                            )
    data= data.replace('sql','')
    return data
