from sqlalchemy import create_engine, inspect
import pandas as pd

# Update these with your actual credentials
USER = 'geohealth'
PASSWORD = 'geohealth'
HOST = 'localhost'
PORT = 5432
DB = 'geohealth'

engine = create_engine(f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")

# List all tables
inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tables in database:", tables)

# Example: Read a table (replace 'lga' with your table name)
if 'lga' in tables:
    df = pd.read_sql("SELECT * FROM lga", engine)
    print(df.head())
else:
    print("Table 'lga' not found.")
