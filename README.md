# GraphRAG

GraphRAG is a project that combines SQL and Neo4j databases to manage and query movie data. The project utilizes Groq API for enhanced querying capabilities. This README provides step-by-step instructions for setting up and running the project.

## Prerequisites

Before running the Python code, ensure you have the following installed and configured:

1. **SQL Server**
   - Download and run SQL Server locally.

2. **Neo4j**
   - Download and run Neo4j Desktop or get a URI from Neo4j Aura DB and connect to it.

3. **Environment Variables**
   - Store the credentials for SQL Server and Neo4j in a `.env` file located in the same directory as the project files. The `.env` file should look like this:

    ```plaintext
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USERNAME=database_name
    NEO4J_PASSWORD=your_password

    SQL_PORT=3306
    SQL_USERNAME=root
    SQL_HOST=localhost
    SQL_PASSWORD=your_password
    SQL_DATABASE=database_name

    GROQ_API_KEY=your_api_key_here
    ```

## Loading the Databases

### 1. Load Data into SQL Server

```python
from SQL_DB import SQL_LOADER

sql = SQL_LOADER('movies')
sql.load_data("https://raw.githubusercontent.com/tomasonjo/blog-datasets/main/movies/movies_small.csv")
```

### 2. Load Data into Neo4j

```python
from NEO4J import NEO4J_LOADER
from miscellenous import create_query

neo = NEO4J_LOADER('movies')
params = {
    "movieId": row[0],
    "released": row[1],
    "title": row[2],
    "actors": row[3].split('|'),
    "director": row[4].split('|'),
    "genres": row[5].split('|'),
    "imdbRating": row[6]
}
neo.insert_data_neo4j(sql.sql_data, create_query(sql.sql_schema), params)
```

> **Note**: The `params` dictionary is specific to the given data structure.

## How to Run the Project

1. **Clone the Repository**
   - Clone the repository to your local machine:

    ```bash
    git clone https://github.com/yourusername/GraphRAG.git
    ```

2. **Create a `.env` File**
   - In the root directory of the project, create a `.env` file and add your SQL, Neo4j credentials, and Groq API key.

3. **Get Groq API Key**
   - Sign up at [console.groq.com](https://console.groq.com) to get your Groq API key and add it to the `.env` file as `GROQ_API_KEY`.

4. **Run the Notebook**
   - Open and run the `main.ipynb` notebook. Modify the query as needed within the notebook.
