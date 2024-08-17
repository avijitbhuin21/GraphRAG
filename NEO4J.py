from neo4j import GraphDatabase
import os
from miscellenous import get_neo4j_query
from neo4j.exceptions import Neo4jError

class NEO4J_LOADER:
    def __init__(self,table_name) -> None:
        self.graph = GraphDatabase.driver(uri=os.environ.get('NEO4J_URI'), auth=(os.environ.get('NEO4J_USERNAME'), os.environ.get('NEO4J_PASSWORD')))
        self.schema = self.construct_schema(graph=self.graph)
        self.table_name = table_name

    def construct_schema(self, graph: GraphDatabase) -> str:
        with graph.session() as session:
            # Fetch node labels and properties
            node_result = session.run("""
            CALL db.schema.nodeTypeProperties()
            YIELD nodeLabels, propertyName, propertyTypes
            RETURN nodeLabels, collect({property: propertyName, type: propertyTypes[0]}) as properties
            """)
            node_props = {label[0]: props for label, props in node_result}

            # Fetch relationship types and properties
            rel_result = session.run("""
            CALL db.schema.relTypeProperties()
            YIELD relType, propertyName, propertyTypes
            RETURN relType, collect({property: propertyName, type: propertyTypes[0]}) as properties
            """)
            rel_props = {rel_type: props for rel_type, props in rel_result}

            # Fetch relationships with start and end node labels
            rel_structure_result = session.run("""
            CALL apoc.meta.schema()
            YIELD value
            UNWIND keys(value) AS nodeLabel
            UNWIND keys(value[nodeLabel].relationships) AS relType
            RETURN 
                nodeLabel AS start, 
                relType, 
                value[nodeLabel].relationships[relType].direction AS direction,
                value[nodeLabel].relationships[relType].labels[0] AS end
            """)
            relationships = [dict(r) for r in rel_structure_result]

        # Format node properties
        formatted_node_props = []
        for label, properties in node_props.items():
            props_str = ", ".join([f"{prop['property']}: {prop['type']}" for prop in properties])
            formatted_node_props.append(f"{label} {{{props_str}}}")

        # Format relationship properties
        formatted_rel_props = []
        for rel_type, properties in rel_props.items():
            rel_type = str(rel_type).replace(':','').replace('`','')
            props_str = ", ".join([f"{prop['property']}: {prop['type']}" for prop in properties])
            formatted_rel_props.append(f"{rel_type} {{{props_str}}}")

        # Format relationships
        formatted_rels = []
        for rel in relationships:
            if rel['direction'] == 'out':
                formatted_rels.append(f"({rel['start']})-[{rel['relType']}]->({rel['end']})")
            elif rel['direction'] == 'in':
                formatted_rels.append(f"({rel['end']})-[{rel['relType']}]->({rel['start']})")
        formatted_rels = list(set(formatted_rels))

        return "\n".join([
            "Node properties are the following:",
            ", ".join(formatted_node_props),
            "Relationship properties are the following:",
            ", ".join(formatted_rel_props),
            "The relationships are the following:",
            ", ".join(formatted_rels),
        ])
    
    def insert_data_neo4j(self, data, query):
        try:
            for row in data:
                params = {
                        "movieId": row[0],
                        "released": row[1],
                        "title": row[2],
                        "actors": row[3].split('|'),
                        "director": row[4].split('|'),
                        "genres": row[5].split('|'),
                        "imdbRating": row[6]
                    }
                self.graph.query(query, params)
        except:
            self.insert_data_neo4j()

    def reset(self, graph):
        with graph.session(database='system') as session:
            session.run("""DROP DATABASE neo4j""")
            session.run('''CREATE DATABASE neo4j''')
        graph.close()


    def Neo4j_llm_check(self, question):
        conv = [f'''Generate me a cypher query for neo4j for the following question:
                    {question}

                    Here is the schema:
                    {self.schema}
                    ''']
        for i in range(5):
            if i!=0:
                print(f"Retrying: {i}")
            try:
                query = get_neo4j_query("\n".join(conv))
                print(f"Generated NEO4J Query: {query}")
                with self.graph.session() as session:
                    ans = session.run(query)
                    records = [dict(record) for record in ans]
                    print(f'''NEO4J_DATABASE_CONTEXT (by running the following query: {query}):\n{str(records).replace('{','(').replace('}',')')}''')
                    return f'''NEO4J_DATABASE_CONTEXT (by running the following query: {query}):\n{str(records).replace('{','(').replace('}',')')}'''
            except Neo4jError as e:
                print('Failed!!')
                conv.append(f"After running the query: {query}, i got this error: {e}")
                continue

            