from sqlalchemy import create_engine

dialect_driver = 'mysql+pymysql'
username = 'root'
password = ""
host = '127.0.0.1'
dbname = 'market'

def engine():
	return create_engine(f"{dialect_driver}://{username}:{password}@{host}/{dbname}")

if __name__ == "__main__":
    print("\nYou ran this module directly. It needs to be imported.")

