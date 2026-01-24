import sqlite3
from app.core.config import settings

def init_db():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS response_cache
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query TEXT,
                  response TEXT,
                  language TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS chat_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  intent TEXT,
                  language TEXT,
                  user_location TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  success BOOLEAN)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_preferences
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  phone_number TEXT UNIQUE,
                  preferred_language TEXT DEFAULT 'hindi',
                  location TEXT,
                  last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def log_interaction(intent, language, success=True, location=None):
    try:
        conn = sqlite3.connect(settings.DATABASE_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO chat_logs (intent, language, user_location, success) VALUES (?, ?, ?, ?)",
                  (intent, language, location, success))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Logging error: {e}")

def get_user_language(phone_number):
    try:
        conn = sqlite3.connect(settings.DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT preferred_language FROM user_preferences WHERE phone_number = ?", (phone_number,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 'hindi'
    except:
        return 'hindi'

def set_user_language(phone_number, language):
    try:
        conn = sqlite3.connect(settings.DATABASE_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO user_preferences (phone_number, preferred_language) 
                     VALUES (?, ?) 
                     ON CONFLICT(phone_number) 
                     DO UPDATE SET preferred_language = ?, last_interaction = CURRENT_TIMESTAMP""",
                  (phone_number, language, language))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Set language error: {e}")

def cache_response(query, response, language):
    try:
        conn = sqlite3.connect(settings.DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM response_cache")
        count = c.fetchone()[0]
        if count >= 50:
            c.execute("DELETE FROM response_cache WHERE id IN (SELECT id FROM response_cache ORDER BY timestamp ASC LIMIT 10)")
        
        c.execute("INSERT INTO response_cache (query, response, language) VALUES (?, ?, ?)",
                  (query.lower(), response, language))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Caching error: {e}")

def get_cached_response(query):
    try:
        conn = sqlite3.connect(settings.DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT response FROM response_cache WHERE query LIKE ? ORDER BY timestamp DESC LIMIT 1",
                  (f"%{query.lower()}%",))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Cache retrieval error: {e}")
        return None
