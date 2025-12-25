from backend.database.db_connection import DatabaseConnection

db = DatabaseConnection()
db.connect()

# Check total count
result = db.execute_query('SELECT COUNT(*) FROM developers;')
print(f'Total developers: {result[0]["count"]}')

# Show some examples
devs = db.execute_query('SELECT github_username, total_stars FROM developers ORDER BY total_stars DESC LIMIT 10;')
print('\nTop 10 by stars:')
for dev in devs:
    print(f'  {dev["github_username"]}: {dev["total_stars"]} stars')

db.close()
